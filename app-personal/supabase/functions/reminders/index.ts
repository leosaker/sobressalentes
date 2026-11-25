// Edge Function "reminders" — lembrete "Hoje é dia de treino!".
// Deve ser chamada a cada 15 minutos por um agendamento (veja supabase/lembretes-cron.sql).
// Envia para quem marcou o dia e o horário no app e ainda não treinou hoje (no máximo 1 por dia).
// Segredos necessários: VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT e CRON_SECRET.
import webpush from 'npm:web-push@3.6.7';
import { createClient } from 'npm:@supabase/supabase-js@2.119.0';

// ===== núcleo (testável) =====
const DOW = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
export function localParts(date, tz) {
  const f = new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', weekday: 'short' });
  const o = Object.fromEntries(f.formatToParts(date).map(p => [p.type, p.value]));
  return { date: `${o.year}-${o.month}-${o.day}`, dow: DOW[o.weekday], min: (+o.hour) * 60 + (+o.minute) };
}
const toMin = t => { const [h, m] = String(t).split(':'); return (+h) * 60 + (+m); };
// Executa tarefas com no máximo `n` ao mesmo tempo (envia milhares de notificações sem estourar o tempo da função).
export async function pool(items, n, fn) {
  let i = 0;
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => { while (i < items.length) { const k = i++; await fn(items[k], k); } }));
}

export async function handleReminders(now, repo, send) {
  const due = [];
  for (const p of await repo.reminderPrefs()) {
    if (!p.remind_time || !(p.remind_days || []).length) continue;
    const L = localParts(now, p.tz || 'America/Sao_Paulo'), t = toMin(p.remind_time);
    if (!p.remind_days.includes(L.dow) || L.min < t || L.min >= t + 180 || p.last_reminded === L.date) continue;
    due.push({ p, L });
  }
  if (!due.length) return { checked: 0, sent: 0 };
  const students = await repo.studentsByUsers(due.map(d => d.p.user_id));
  const sids = students.map(s => s.id);
  const logs = sids.length ? await repo.recentLogs(sids, new Date(now - 14 * 864e5).toISOString()) : [];
  const plans = sids.length ? await repo.plansOf(sids) : [];
  let sent = 0;
  // marca "lembrete do dia" de todos de uma vez (agrupado por data local)
  const byDate = {};
  for (const { p, L } of due) (byDate[L.date] ||= []).push(p.user_id);
  for (const [d, ids] of Object.entries(byDate)) {
    if (repo.setRemindedMany) { for (let i = 0; i < ids.length; i += 500) await repo.setRemindedMany(d, ids.slice(i, i + 500)); }
    else for (const u of ids) await repo.setReminded(u, d);
  }
  const stBy = new Map(students.map(s => [s.user_id, s]));
  const logsBy = new Map(); for (const l of logs) { let a = logsBy.get(l.student_id); if (!a) logsBy.set(l.student_id, a = []); a.push(l); }
  const plansBy = new Map(); for (const x of plans) { let a = plansBy.get(x.student_id); if (!a) plansBy.set(x.student_id, a = []); a.push(x); }
  const jobs = [];
  for (const { p, L } of due) {
    const st = stBy.get(p.user_id);
    if (!st) continue;
    const mine = (logsBy.get(st.id) || []).sort((a, b) => String(b.done_at).localeCompare(String(a.done_at)));
    if (mine.some(l => localParts(new Date(l.done_at), p.tz || 'America/Sao_Paulo').date === L.date)) continue; // já treinou hoje
    const ps = (plansBy.get(st.id) || []).sort((a, b) => a.position - b.position);
    let next = ps[0];
    if (mine[0] && ps.length > 1) { const i = ps.findIndex(x => x.name === mine[0].plan_name); if (i >= 0) next = ps[(i + 1) % ps.length]; }
    const msg = { title: 'Hoje é dia de treino! 💪', body: next ? `Seu ${next.name} está te esperando.` : 'Bora treinar? Seu treino está no app.', url: './#treino', tag: `lembrete-${L.date}` };
    jobs.push({ uid: p.user_id, msg });
  }
  // aparelhos de todos de uma vez, envio com até 25 notificações em paralelo
  const subsAll = repo.subsMany ? await repo.subsMany(jobs.map(j => j.uid)) : null;
  await pool(jobs, 25, async ({ uid, msg }) => {
    const subs = subsAll ? subsAll.filter(s => s.user_id === uid) : await repo.subs(uid);
    for (const s of subs) {
      try { await send(s, JSON.stringify(msg)); sent++; }
      catch (e) { if (e && (e.statusCode === 404 || e.statusCode === 410)) await repo.deleteSub(s.endpoint); }
    }
  });
  return { checked: due.length, sent };
}
// ===== fim do núcleo =====

Deno.serve(async req => {
  const secret = Deno.env.get('CRON_SECRET');
  if (!secret || req.headers.get('x-cron-secret') !== secret) return new Response('não autorizado', { status: 401 });
  const admin = createClient(Deno.env.get('SUPABASE_URL'), Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'));
  const rows = q => q.then(r => { if (r.error) throw r.error; return r.data || []; });
  const repo = {
    reminderPrefs: () => rows(admin.from('notif_prefs').select('*').not('remind_time', 'is', null)),
    studentsByUsers: uids => rows(admin.from('students').select('id, name, user_id').in('user_id', uids)),
    recentLogs: (sids, since) => rows(admin.from('workout_logs').select('student_id, done_at, plan_name').in('student_id', sids).gte('done_at', since)),
    plansOf: sids => rows(admin.from('plans').select('student_id, name, position').in('student_id', sids)),
    setReminded: (uid, day) => admin.from('notif_prefs').update({ last_reminded: day }).eq('user_id', uid),
    setRemindedMany: (day, uids) => admin.from('notif_prefs').update({ last_reminded: day }).in('user_id', uids),
    subsMany: async uids => { const out = []; for (let i = 0; i < uids.length; i += 500) out.push(...await rows(admin.from('push_subs').select('*').in('user_id', uids.slice(i, i + 500)))); return out; },
    subs: uid => rows(admin.from('push_subs').select('*').eq('user_id', uid)),
    deleteSub: endpoint => admin.from('push_subs').delete().eq('endpoint', endpoint)
  };
  webpush.setVapidDetails(Deno.env.get('VAPID_SUBJECT') || 'mailto:contato@example.com', Deno.env.get('VAPID_PUBLIC_KEY'), Deno.env.get('VAPID_PRIVATE_KEY'));
  const send = (s, payload) => webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, payload, { TTL: 6 * 3600 });
  try { return Response.json(await handleReminders(new Date(), repo, send)); }
  catch (e) { return Response.json({ error: e.message || String(e) }, { status: 500 }); }
});
