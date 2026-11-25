-- =====================================================================
-- Meu Personal — banco de dados (Supabase)
-- Cole este arquivo inteiro em: Supabase → SQL Editor → New query → Run
-- Depois, rode a linha do final trocando pelo SEU e-mail de personal.
-- =====================================================================

-- ---------- Tabelas ----------

-- E-mails autorizados a criar conta de PERSONAL (alunos não precisam estar aqui).
create table if not exists public.trainer_allowlist (
  email text primary key
);

create table if not exists public.trainers (
  id         uuid primary key default auth.uid() references auth.users on delete cascade,
  name       text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists public.exercises (
  id         uuid primary key default gen_random_uuid(),
  trainer_id uuid not null default auth.uid() references public.trainers on delete cascade,
  name       text not null,
  grp        text not null default 'Outros',
  video      text not null default '',
  notes      text not null default '',
  created_at timestamptz not null default now()
);

create table if not exists public.students (
  id          uuid primary key default gen_random_uuid(),
  trainer_id  uuid not null default auth.uid() references public.trainers on delete cascade,
  user_id     uuid unique references auth.users on delete set null,
  name        text not null,
  goal        text not null default '',
  notes       text not null default '',            -- só o personal vê
  invite_code text not null unique default upper(substr(md5(gen_random_uuid()::text), 1, 8)),
  created_at  timestamptz not null default now()
);

create table if not exists public.plans (
  id         uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.students on delete cascade,
  trainer_id uuid not null default auth.uid() references public.trainers on delete cascade,
  name       text not null,
  focus      text not null default '',
  position   int  not null default 0,
  -- [{ "ex": "<exercise id>", "sets": "3", "reps": "12", "load": "20 kg", "rest": "60", "obs": "" }]
  items      jsonb not null default '[]',
  updated_at timestamptz not null default now()
);

create table if not exists public.workout_logs (
  id           uuid primary key default gen_random_uuid(),
  student_id   uuid not null references public.students on delete cascade,
  plan_id      uuid references public.plans on delete set null,
  plan_name    text not null,
  done_at      timestamptz not null default now(),
  duration_min int,
  effort       int check (effort between 1 and 10),
  comment      text not null default '',
  -- [{ "name": "Agachamento", "done": 3, "total": 3, "load": "40 kg" }]
  details      jsonb not null default '[]',
  trainer_seen boolean not null default false
);

-- Versão 2: validade do treino e resposta do personal (seguro rodar de novo).
alter table public.plans        add column if not exists ends_on      date;
alter table public.workout_logs add column if not exists trainer_reply text not null default '';
alter table public.workout_logs add column if not exists replied_at   timestamptz;

create index if not exists exercises_trainer_idx on public.exercises (trainer_id);
create index if not exists students_trainer_idx  on public.students (trainer_id);
create index if not exists plans_student_idx     on public.plans (student_id);
create index if not exists logs_student_idx      on public.workout_logs (student_id, done_at desc);

-- ---------- Funções auxiliares ----------

create or replace function public.is_allowed_trainer() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from trainer_allowlist
                 where lower(email) = lower(coalesce(auth.jwt() ->> 'email', '')));
$$;

create or replace function public.my_student_id() returns uuid
language sql stable security definer set search_path = public as $$
  select id from students where user_id = auth.uid();
$$;

create or replace function public.my_trainer_as_student() returns uuid
language sql stable security definer set search_path = public as $$
  select trainer_id from students where user_id = auth.uid();
$$;

-- Dados do aluno logado (sem as observações privadas do personal).
create or replace function public.my_student()
returns table (id uuid, name text, goal text, trainer_name text)
language sql stable security definer set search_path = public as $$
  select s.id, s.name, s.goal, t.name
  from students s join trainers t on t.id = s.trainer_id
  where s.user_id = auth.uid();
$$;

-- O aluno usa o código de convite para ligar a conta dele ao cadastro feito pelo personal.
create or replace function public.claim_invite(code text) returns text
language plpgsql security definer set search_path = public as $$
declare v_name text;
begin
  if auth.uid() is null then raise exception 'Faça login primeiro'; end if;
  if exists (select 1 from trainers where id = auth.uid()) then
    raise exception 'Esta conta é de personal; use outro e-mail para a conta de aluno';
  end if;
  if exists (select 1 from students where user_id = auth.uid()) then
    raise exception 'Esta conta já está ligada a um aluno';
  end if;
  update students set user_id = auth.uid()
   where invite_code = upper(trim(code)) and user_id is null
  returning name into v_name;
  if v_name is null then raise exception 'Código de convite inválido ou já usado'; end if;
  return v_name;
end $$;

-- O personal desliga o acesso atual do aluno e gera um código novo.
create or replace function public.reset_invite(p_student uuid) returns text
language plpgsql security definer set search_path = public as $$
declare v_code text;
begin
  update students
     set user_id = null, invite_code = upper(substr(md5(gen_random_uuid()::text), 1, 8))
   where id = p_student and trainer_id = auth.uid()
  returning invite_code into v_code;
  if v_code is null then raise exception 'Aluno não encontrado'; end if;
  return v_code;
end $$;

revoke all on function public.is_allowed_trainer(), public.my_student_id(), public.my_trainer_as_student(),
  public.my_student(), public.claim_invite(text), public.reset_invite(uuid) from public, anon;
grant execute on function public.is_allowed_trainer(), public.my_student_id(), public.my_trainer_as_student(),
  public.my_student(), public.claim_invite(text), public.reset_invite(uuid) to authenticated;

-- ---------- Segurança (Row Level Security) ----------

alter table public.trainer_allowlist enable row level security;   -- sem políticas: ninguém lê pela API
alter table public.trainers     enable row level security;
alter table public.exercises    enable row level security;
alter table public.students     enable row level security;
alter table public.plans        enable row level security;
alter table public.workout_logs enable row level security;

-- Visitantes sem login não acessam nada.
revoke all on public.trainer_allowlist, public.trainers, public.exercises,
              public.students, public.plans, public.workout_logs from anon;

-- Personal
drop policy if exists trainers_select on public.trainers;
create policy trainers_select on public.trainers for select to authenticated
  using (id = auth.uid() or id = public.my_trainer_as_student());
drop policy if exists trainers_insert on public.trainers;
create policy trainers_insert on public.trainers for insert to authenticated
  with check (id = auth.uid() and public.is_allowed_trainer()
              and not exists (select 1 from public.students where user_id = auth.uid()));
drop policy if exists trainers_update on public.trainers;
create policy trainers_update on public.trainers for update to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

-- Exercícios: o personal gerencia; os alunos dele podem ler (para ver nome e vídeo).
drop policy if exists exercises_trainer on public.exercises;
create policy exercises_trainer on public.exercises for all to authenticated
  using (trainer_id = auth.uid()) with check (trainer_id = auth.uid());
drop policy if exists exercises_student on public.exercises;
create policy exercises_student on public.exercises for select to authenticated
  using (trainer_id = public.my_trainer_as_student());

-- Alunos: só o personal acessa a tabela (o aluno usa a função my_student()).
drop policy if exists students_trainer on public.students;
create policy students_trainer on public.students for all to authenticated
  using (trainer_id = auth.uid()) with check (trainer_id = auth.uid());
-- O personal não pode mudar user_id/invite_code diretamente (só via reset_invite).
revoke insert, update on public.students from authenticated;
grant insert (name, goal, notes) on public.students to authenticated;
grant update (name, goal, notes) on public.students to authenticated;

-- Treinos: o personal gerencia os dos seus alunos; o aluno só lê os dele.
drop policy if exists plans_trainer on public.plans;
create policy plans_trainer on public.plans for all to authenticated
  using (trainer_id = auth.uid())
  with check (trainer_id = auth.uid()
              and student_id in (select id from public.students where trainer_id = auth.uid()));
drop policy if exists plans_student on public.plans;
create policy plans_student on public.plans for select to authenticated
  using (student_id = public.my_student_id());

-- Registros de treino: o aluno cria e lê os dele; o personal lê os dos alunos e marca como visto.
drop policy if exists logs_student_select on public.workout_logs;
create policy logs_student_select on public.workout_logs for select to authenticated
  using (student_id = public.my_student_id());
drop policy if exists logs_student_insert on public.workout_logs;
create policy logs_student_insert on public.workout_logs for insert to authenticated
  with check (student_id = public.my_student_id() and trainer_seen = false);
drop policy if exists logs_trainer_select on public.workout_logs;
create policy logs_trainer_select on public.workout_logs for select to authenticated
  using (student_id in (select id from public.students where trainer_id = auth.uid()));
drop policy if exists logs_trainer_update on public.workout_logs;
create policy logs_trainer_update on public.workout_logs for update to authenticated
  using (student_id in (select id from public.students where trainer_id = auth.uid()));
revoke update on public.workout_logs from authenticated;
grant update (trainer_seen, trainer_reply, replied_at) on public.workout_logs to authenticated;

-- ---------- Versão 3: modelos de treino e tipo do exercício ----------
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

-- ---------- Versão 4: avaliação física, fotos e anamnese ----------

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

-- ---------- Versão 5: notificações no celular ----------

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

-- ---------- SEU E-MAIL DE PERSONAL ----------
-- Troque pelo e-mail que você vai usar para entrar como personal e rode esta linha:
-- insert into public.trainer_allowlist (email) values ('seu-email@exemplo.com');
