-- =====================================================================
-- Atualização v2 — rode UMA vez no SQL Editor se você já tinha rodado o schema.sql antes.
-- (Rodar o schema.sql inteiro de novo também funciona.)
-- Adiciona: validade do treino e resposta do personal ao registro do aluno.
-- =====================================================================
alter table public.plans        add column if not exists ends_on      date;
alter table public.workout_logs add column if not exists trainer_reply text not null default '';
alter table public.workout_logs add column if not exists replied_at   timestamptz;

revoke update on public.workout_logs from authenticated;
grant update (trainer_seen, trainer_reply, replied_at) on public.workout_logs to authenticated;
