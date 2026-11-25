-- =====================================================================
-- Atualização v3 — rode UMA vez no SQL Editor se você já tinha rodado o schema.sql antes.
-- (Rodar o schema.sql inteiro de novo também funciona.)
-- Adiciona: modelos de treino e o tipo padrão do exercício (repetições, tempo ou cardio).
-- Bi-set e os modos tempo/cardio ficam dentro dos itens do treino e não precisam de colunas novas.
-- =====================================================================
create table if not exists public.templates (
  id         uuid primary key default gen_random_uuid(),
  trainer_id uuid not null default auth.uid() references public.trainers on delete cascade,
  name       text not null,
  focus      text not null default '',
  items      jsonb not null default '[]',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists templates_trainer_idx on public.templates (trainer_id);

alter table public.exercises add column if not exists kind text not null default 'reps'
  check (kind in ('reps', 'time', 'cardio'));

alter table public.templates enable row level security;
revoke all on public.templates from anon;
drop policy if exists templates_trainer on public.templates;
create policy templates_trainer on public.templates for all to authenticated
  using (trainer_id = auth.uid()) with check (trainer_id = auth.uid());
