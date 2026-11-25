-- =====================================================================
-- Atualização v8 — Desempenho (as regras de segurança continuam as mesmas).
-- Rode UMA vez no SQL Editor se você já tinha rodado o schema.sql antes
-- (rodar o schema.sql inteiro de novo também funciona).
--
-- Por quê: nas regras de segurança, auth.uid() e my_student_id() eram calculados para CADA LINHA.
-- Escritos como (select auth.uid()), o banco calcula uma vez por consulta e consegue usar os índices.
-- Com 300 mil registros de treino, o histórico do aluno caiu de ~1 s para poucos milissegundos.
-- =====================================================================

create index if not exists plans_trainer_idx       on public.plans (trainer_id);
create index if not exists assessments_trainer_idx on public.assessments (trainer_id);
create index if not exists logs_done_idx           on public.workout_logs (done_at desc);
create index if not exists students_user_idx       on public.students (user_id);

-- trainers
drop policy if exists trainers_select on public.trainers;
create policy trainers_select on public.trainers for select to authenticated using (id = (select auth.uid()));
drop policy if exists trainers_insert on public.trainers;
create policy trainers_insert on public.trainers for insert to authenticated
  with check (id = (select auth.uid()) and (select public.is_allowed_trainer())
              and not exists (select 1 from public.students where user_id = (select auth.uid())));
drop policy if exists trainers_update on public.trainers;
create policy trainers_update on public.trainers for update to authenticated
  using (id = (select auth.uid())) with check (id = (select auth.uid()));

-- exercícios
drop policy if exists exercises_trainer on public.exercises;
create policy exercises_trainer on public.exercises for all to authenticated
  using (trainer_id = (select auth.uid())) with check (trainer_id = (select auth.uid()));
drop policy if exists exercises_student on public.exercises;
create policy exercises_student on public.exercises for select to authenticated
  using (trainer_id = (select public.my_trainer_as_student()));

-- alunos
drop policy if exists students_trainer on public.students;
create policy students_trainer on public.students for all to authenticated
  using (trainer_id = (select auth.uid())) with check (trainer_id = (select auth.uid()));

-- treinos
drop policy if exists plans_trainer on public.plans;
create policy plans_trainer on public.plans for all to authenticated
  using (trainer_id = (select auth.uid()))
  with check (trainer_id = (select auth.uid())
              and student_id in (select id from public.students where trainer_id = (select auth.uid())));
drop policy if exists plans_student on public.plans;
create policy plans_student on public.plans for select to authenticated
  using (student_id = (select public.my_student_id()));

-- registros de treino
drop policy if exists logs_student_select on public.workout_logs;
create policy logs_student_select on public.workout_logs for select to authenticated
  using (student_id = (select public.my_student_id()));
drop policy if exists logs_student_insert on public.workout_logs;
create policy logs_student_insert on public.workout_logs for insert to authenticated
  with check (student_id = (select public.my_student_id()) and trainer_seen = false);
drop policy if exists logs_trainer_select on public.workout_logs;
create policy logs_trainer_select on public.workout_logs for select to authenticated
  using (student_id in (select id from public.students where trainer_id = (select auth.uid())));
drop policy if exists logs_trainer_update on public.workout_logs;
create policy logs_trainer_update on public.workout_logs for update to authenticated
  using (student_id in (select id from public.students where trainer_id = (select auth.uid())));

-- modelos
drop policy if exists templates_trainer on public.templates;
create policy templates_trainer on public.templates for all to authenticated
  using (trainer_id = (select auth.uid())) with check (trainer_id = (select auth.uid()));

-- avaliações e anamnese
drop policy if exists assessments_trainer on public.assessments;
create policy assessments_trainer on public.assessments for all to authenticated
  using (trainer_id = (select auth.uid()))
  with check (trainer_id = (select auth.uid())
              and student_id in (select id from public.students where trainer_id = (select auth.uid())));
drop policy if exists assessments_student on public.assessments;
create policy assessments_student on public.assessments for select to authenticated
  using (student_id = (select public.my_student_id()));
drop policy if exists anamnesis_student on public.anamnesis;
create policy anamnesis_student on public.anamnesis for all to authenticated
  using (student_id = (select public.my_student_id())) with check (student_id = (select public.my_student_id()));
drop policy if exists anamnesis_trainer on public.anamnesis;
create policy anamnesis_trainer on public.anamnesis for all to authenticated
  using (student_id in (select id from public.students where trainer_id = (select auth.uid())))
  with check (student_id in (select id from public.students where trainer_id = (select auth.uid())));

-- notificações
drop policy if exists push_subs_own on public.push_subs;
create policy push_subs_own on public.push_subs for all to authenticated
  using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
drop policy if exists notif_prefs_own on public.notif_prefs;
create policy notif_prefs_own on public.notif_prefs for all to authenticated
  using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

-- cobranças e aulas
drop policy if exists charges_trainer on public.charges;
create policy charges_trainer on public.charges for all to authenticated
  using (trainer_id = (select auth.uid()))
  with check (trainer_id = (select auth.uid())
              and student_id in (select id from public.students where trainer_id = (select auth.uid())));
drop policy if exists charges_student on public.charges;
create policy charges_student on public.charges for select to authenticated
  using (student_id = (select public.my_student_id()));
drop policy if exists sessions_trainer on public.sessions;
create policy sessions_trainer on public.sessions for all to authenticated
  using (trainer_id = (select auth.uid()))
  with check (trainer_id = (select auth.uid())
              and student_id in (select id from public.students where trainer_id = (select auth.uid())));
drop policy if exists sessions_student on public.sessions;
create policy sessions_student on public.sessions for select to authenticated
  using (student_id = (select public.my_student_id()));

-- fotos (Storage)
drop policy if exists fotos_trainer on storage.objects;
create policy fotos_trainer on storage.objects for all to authenticated
  using (bucket_id = 'fotos' and (storage.foldername(objects.name))[1] = (select auth.uid())::text)
  with check (bucket_id = 'fotos' and (storage.foldername(objects.name))[1] = (select auth.uid())::text
              and exists (select 1 from public.students s
                          where s.id::text = (storage.foldername(objects.name))[2] and s.trainer_id = (select auth.uid())));
drop policy if exists fotos_student on storage.objects;
create policy fotos_student on storage.objects for select to authenticated
  using (bucket_id = 'fotos' and (storage.foldername(objects.name))[2] = (select public.my_student_id())::text);

-- Último treino e total de treinos de cada aluno do personal, calculado no banco
-- (o app não precisa baixar todo o histórico para saber quem está parado).
create or replace function public.last_workouts()
returns table (student_id uuid, last_at timestamptz, total bigint)
language sql stable set search_path = public as $$
  select l.student_id, max(l.done_at), count(*)
  from workout_logs l
  where l.student_id in (select id from students where trainer_id = (select auth.uid()))
  group by l.student_id;
$$;
revoke all on function public.last_workouts() from public, anon;
grant execute on function public.last_workouts() to authenticated;
