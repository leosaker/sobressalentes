-- =====================================================================
-- Atualização v4 — Avaliação física, fotos de evolução e anamnese (PAR-Q).
-- Rode UMA vez no SQL Editor se você já tinha rodado o schema.sql antes
-- (rodar o schema.sql inteiro de novo também funciona).
-- =====================================================================

-- Avaliações físicas (feitas pelo personal; o aluno só vê as dele).
create table if not exists public.assessments (
  id         uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students on delete cascade,
  trainer_id uuid not null default auth.uid() references public.trainers on delete cascade,
  taken_on   date not null default current_date,
  weight     numeric(5,1),            -- kg
  height     numeric(5,1),            -- cm
  body_fat   numeric(4,1),            -- %
  measures   jsonb not null default '{}',   -- circunferências em cm: {"cintura": 80, "quadril": 98, ...}
  photos     jsonb not null default '[]',   -- [{"pos": "frente", "path": "<trainer>/<aluno>/<arquivo>.jpg"}]
  notes      text not null default '',
  created_at timestamptz not null default now()
);
create index if not exists assessments_student_idx on public.assessments (student_id, taken_on desc);

-- Anamnese / PAR-Q (respondida pelo aluno no app; o personal também pode preencher).
create table if not exists public.anamnesis (
  student_id uuid primary key references public.students on delete cascade,
  answers    jsonb not null default '{}',
  updated_at timestamptz not null default now()
);

alter table public.assessments enable row level security;
alter table public.anamnesis   enable row level security;
revoke all on public.assessments, public.anamnesis from anon;

drop policy if exists assessments_trainer on public.assessments;
create policy assessments_trainer on public.assessments for all to authenticated
  using (trainer_id = auth.uid())
  with check (trainer_id = auth.uid()
              and student_id in (select id from public.students where trainer_id = auth.uid()));
drop policy if exists assessments_student on public.assessments;
create policy assessments_student on public.assessments for select to authenticated
  using (student_id = public.my_student_id());

drop policy if exists anamnesis_student on public.anamnesis;
create policy anamnesis_student on public.anamnesis for all to authenticated
  using (student_id = public.my_student_id()) with check (student_id = public.my_student_id());
drop policy if exists anamnesis_trainer on public.anamnesis;
create policy anamnesis_trainer on public.anamnesis for all to authenticated
  using (student_id in (select id from public.students where trainer_id = auth.uid()))
  with check (student_id in (select id from public.students where trainer_id = auth.uid()));

-- Fotos: pasta privada "fotos" no Storage. Caminho: <id do personal>/<id do aluno>/<arquivo>.jpg
-- O personal envia e vê as fotos dos alunos dele; o aluno só vê as próprias. Ninguém mais.
insert into storage.buckets (id, name, public) values ('fotos', 'fotos', false) on conflict (id) do nothing;
drop policy if exists fotos_trainer on storage.objects;
create policy fotos_trainer on storage.objects for all to authenticated
  using (bucket_id = 'fotos' and (storage.foldername(objects.name))[1] = auth.uid()::text)
  with check (bucket_id = 'fotos' and (storage.foldername(objects.name))[1] = auth.uid()::text
              and exists (select 1 from public.students s
                          where s.id::text = (storage.foldername(objects.name))[2] and s.trainer_id = auth.uid()));
drop policy if exists fotos_student on storage.objects;
create policy fotos_student on storage.objects for select to authenticated
  using (bucket_id = 'fotos' and (storage.foldername(objects.name))[2] = public.my_student_id()::text);
