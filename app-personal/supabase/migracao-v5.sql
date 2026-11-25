-- =====================================================================
-- Atualização v5 — Notificações no celular.
-- Rode UMA vez no SQL Editor se você já tinha rodado o schema.sql antes
-- (rodar o schema.sql inteiro de novo também funciona).
-- =====================================================================

-- Aparelhos que aceitaram receber notificações (um registro por celular/navegador).
create table if not exists public.push_subs (
  endpoint   text primary key,
  user_id    uuid not null default auth.uid() references auth.users on delete cascade,
  p256dh     text not null,
  auth       text not null,
  ua         text not null default '',
  created_at timestamptz not null default now()
);
create index if not exists push_subs_user_idx on public.push_subs (user_id);

-- Preferências de notificação e lembrete de treino de cada pessoa.
create table if not exists public.notif_prefs (
  user_id        uuid primary key default auth.uid() references auth.users on delete cascade,
  notify_logs    boolean not null default true,   -- personal: aluno finalizou treino
  notify_replies boolean not null default true,   -- aluno: personal respondeu
  notify_plans   boolean not null default true,   -- aluno: treino atualizado
  remind_days    int[]   not null default '{}',   -- 0 = domingo … 6 = sábado
  remind_time    time,                            -- horário do lembrete (hora local)
  tz             text    not null default 'America/Sao_Paulo',
  last_reminded  date
);

alter table public.push_subs   enable row level security;
alter table public.notif_prefs enable row level security;
revoke all on public.push_subs, public.notif_prefs from anon;

-- Cada pessoa só vê e mexe nos próprios aparelhos e preferências.
-- (O envio é feito pelas Edge Functions, que usam a chave de serviço.)
drop policy if exists push_subs_own on public.push_subs;
create policy push_subs_own on public.push_subs for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
drop policy if exists notif_prefs_own on public.notif_prefs;
create policy notif_prefs_own on public.notif_prefs for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
-- O app não altera "last_reminded" (é a função de lembretes que controla).
revoke update on public.notif_prefs from authenticated;
grant update (user_id, notify_logs, notify_replies, notify_plans, remind_days, remind_time, tz) on public.notif_prefs to authenticated;
