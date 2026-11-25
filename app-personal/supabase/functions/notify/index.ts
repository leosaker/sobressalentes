// Edge Function "notify" — envia notificações quando:
//   • o aluno finaliza um treino        → avisa o personal   ({ type: "log",   id: <id do registro> })
//   • o personal responde um treino     → avisa o aluno      ({ type: "reply", id: <id do registro> })
//   • o personal avisa sobre um treino  → avisa o aluno      ({ type: "plan",  id: <id do treino> })
// Quem chama precisa estar logado; a função confere se a pessoa tem direito de enviar aquele aviso.
// Segredos necessários (Edge Functions → Secrets): VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT.
import webpush from 'npm:web-push@3.6.7';
import { createClient } from 'npm:@supabase/supabase-js@2.119.0';

// ===== núcleo (testável) =====
export class HttpError extends Error { constructor(status, message) { super(message); this.status = status; } }
const cut = (t, n) => { t = String(t || ''); return t.length > n ? t.slice(0, n - 1) + '…' : t; };
const first = n => String(n || '').trim().split(/\s+/)[0] || '';

export async function sendToUser(userId, msg, repo, send) {
  const subs = await repo.subs(userId);
  let sent = 0;
  for (const s of subs) {
    try { await send(s, JSON.stringify(msg)); sent++; }
    catch (e) { if (e && (e.statusCode === 404 || e.statusCode === 410)) await repo.deleteSub(s.endpoint); }
  }
  return { sent, devices: subs.length };
}

export async function handleNotify(caller, body, repo, send, now = new Date()) {
  const { type, id } = body || {};
  if (!caller) throw new HttpError(401, 'login necessário');
  if (!id || !['log', 'reply', 'plan'].includes(type)) throw new HttpError(400, 'pedido inválido');
  let target, pref, msg;
  if (type === 'log' || type === 'reply') {
    const log = await repo.log(id);
    if (!log) throw new HttpError(404, 'registro não encontrado');
    const st = await repo.student(log.student_id);
    if (!st) throw new HttpError(404, 'aluno não encontrado');
    if (type === 'log') {
      if (st.user_id !== caller) throw new HttpError(403, 'sem permissão');
      // Evita avisos repetidos de registros antigos.
      if (now - new Date(log.done_at) > 30 * 60e3) return { sent: 0, reason: 'antigo' };
      const det = log.details || [];
      const done = det.reduce((a, d) => a + (d.done || 0), 0), total = det.reduce((a, d) => a + (d.total || 0), 0);
      target = st.trainer_id; pref = 'notify_logs';
      msg = { title: `${first(st.name)} finalizou o ${log.plan_name} 💪`,
              body: [log.effort ? `Esforço ${log.effort}/10` : '', total ? `${done}/${total} séries` : ''].filter(Boolean).join(' · ') + (log.comment ? `\n“${cut(log.comment, 120)}”` : ''),
              url: `./#aluno=${st.id}`, tag: `log-${log.id}` };
    } else {
      if (st.trainer_id !== caller) throw new HttpError(403, 'sem permissão');
      if (!st.user_id || !log.trainer_reply) return { sent: 0, reason: 'nada a enviar' };
      const tr = await repo.trainer(caller);
      target = st.user_id; pref = 'notify_replies';
      msg = { title: `${(tr && tr.name) || 'Seu personal'} respondeu seu treino 💬`, body: cut(log.trainer_reply, 160), url: './#historico', tag: `reply-${log.id}` };
    }
  } else {
    const plan = await repo.plan(id);
    if (!plan) throw new HttpError(404, 'treino não encontrado');
    if (plan.trainer_id !== caller) throw new HttpError(403, 'sem permissão');
    const st = await repo.student(plan.student_id);
    if (!st || !st.user_id) return { sent: 0, reason: 'aluno sem conta' };
    const tr = await repo.trainer(caller);
    target = st.user_id; pref = 'notify_plans';
    msg = { title: `Treino atualizado: ${plan.name} 🏋️`, body: `${(tr && tr.name) || 'Seu personal'} preparou seu treino. Toque para ver.`, url: './#treino', tag: `plan-${plan.id}` };
  }
  const prefs = await repo.prefs(target);
  if (prefs && prefs[pref] === false) return { sent: 0, reason: 'desativado' };
  return sendToUser(target, msg, repo, send);
}
// ===== fim do núcleo =====

const cors = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type', 'Access-Control-Allow-Methods': 'POST, OPTIONS' };
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { ...cors, 'Content-Type': 'application/json' } });

Deno.serve(async req => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors });
  try {
    const URL = Deno.env.get('SUPABASE_URL');
    const auth = req.headers.get('Authorization') || '';
    const userClient = createClient(URL, Deno.env.get('SUPABASE_ANON_KEY'), { global: { headers: { Authorization: auth } } });
    const { data: { user } } = await userClient.auth.getUser(auth.replace(/^Bearer\s+/i, ''));
    const admin = createClient(URL, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'));
    const one = q => q.maybeSingle().then(r => r.data);
    const repo = {
      log: id => one(admin.from('workout_logs').select('*').eq('id', id)),
      student: id => one(admin.from('students').select('id, name, user_id, trainer_id').eq('id', id)),
      trainer: id => one(admin.from('trainers').select('id, name').eq('id', id)),
      plan: id => one(admin.from('plans').select('id, name, student_id, trainer_id').eq('id', id)),
      prefs: uid => one(admin.from('notif_prefs').select('*').eq('user_id', uid)),
      subs: uid => admin.from('push_subs').select('*').eq('user_id', uid).then(r => r.data || []),
      deleteSub: endpoint => admin.from('push_subs').delete().eq('endpoint', endpoint)
    };
    webpush.setVapidDetails(Deno.env.get('VAPID_SUBJECT') || 'mailto:contato@example.com', Deno.env.get('VAPID_PUBLIC_KEY'), Deno.env.get('VAPID_PRIVATE_KEY'));
    const send = (s, payload) => webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, payload, { TTL: 24 * 3600 });
    return json(await handleNotify(user && user.id, await req.json(), repo, send));
  } catch (e) {
    return json({ error: e.message || String(e) }, e.status || 500);
  }
});
