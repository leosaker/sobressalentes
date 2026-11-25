-- =====================================================================
-- Atualização v7 — Ferramentas por aluno, financeiro (Pix), painel do negócio e agenda de aulas.
-- Rode UMA vez no SQL Editor se você já tinha rodado o schema.sql antes
-- (rodar o schema.sql inteiro de novo também funciona).
-- =====================================================================

-- Ferramentas que cada aluno vê no app ({"videos": true, "financeiro": false, ...}),
-- mensalidade e dia de vencimento.
alter table public.students add column if not exists features jsonb not null default '{}';
alter table public.students add column if not exists fee      numeric(10,2);
alter table public.students add column if not exists due_day  int check (due_day between 1 and 28);
grant update (features, fee, due_day) on public.students to authenticated;

-- Padrão de ferramentas para novos alunos e dados do Pix do personal.
alter table public.trainers add column if not exists default_features jsonb not null default '{}';
alter table public.trainers add column if not exists pix_key  text not null default '';
alter table public.trainers add column if not exists pix_name text not null default '';
alter table public.trainers add column if not exists pix_city text not null default '';

-- O aluno não lê mais a tabela de personais (ela guarda o padrão de ferramentas).
-- O que ele precisa (nome, ferramentas liberadas para ele e Pix) vem da função my_student().
drop policy if exists trainers_select on public.trainers;
create policy trainers_select on public.trainers for select to authenticated using (id = auth.uid());

drop function if exists public.my_student();
create function public.my_student()
returns table (id uuid, name text, goal text, trainer_name text, features jsonb, pix_key text, pix_name text, pix_city text)
language sql stable security definer set search_path = public as $$
  select s.id, s.name, s.goal, t.name,
         coalesce(t.default_features, '{}'::jsonb) || coalesce(s.features, '{}'::jsonb),
         t.pix_key, t.pix_name, t.pix_city
  from students s join trainers t on t.id = s.trainer_id
  where s.user_id = auth.uid();
$$;
revoke all on function public.my_student() from public, anon;
grant execute on function public.my_student() to authenticated;

-- Cobranças (mensalidades e avulsas).
create table if not exists public.charges (
  id          uuid primary key default gen_random_uuid(),
  trainer_id  uuid not null default auth.uid() references public.trainers on delete cascade,
  student_id  uuid not null references public.students on delete cascade,
  description text not null default 'Mensalidade',
  amount      numeric(10,2) not null check (amount >= 0),
  due_date    date not null,
  status      text not null default 'aberta' check (status in ('aberta', 'informada', 'paga', 'cancelada')),
  method      text not null default '',
  paid_at     timestamptz,
  informed_at timestamptz,
  created_at  timestamptz not null default now()
);
create index if not exists charges_trainer_idx on public.charges (trainer_id, due_date desc);
create index if not exists charges_student_idx on public.charges (student_id, due_date desc);
alter table public.charges enable row level security;
revoke all on public.charges from anon;
drop policy if exists charges_trainer on public.charges;
create policy charges_trainer on public.charges for all to authenticated
  using (trainer_id = auth.uid())
  with check (trainer_id = auth.uid() and student_id in (select id from public.students where trainer_id = auth.uid()));
drop policy if exists charges_student on public.charges;
create policy charges_student on public.charges for select to authenticated
  using (student_id = public.my_student_id());

-- O aluno só consegue avisar "já paguei" (não muda valor, data nem marca como paga).
create or replace function public.inform_payment(p_charge uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  update charges set status = 'informada', informed_at = now()
   where id = p_charge and student_id = my_student_id() and status = 'aberta';
  if not found then raise exception 'Cobrança não encontrada ou já informada'; end if;
end $$;
revoke all on function public.inform_payment(uuid) from public, anon;
grant execute on function public.inform_payment(uuid) to authenticated;

-- Agenda de aulas presenciais.
create table if not exists public.sessions (
  id           uuid primary key default gen_random_uuid(),
  trainer_id   uuid not null default auth.uid() references public.trainers on delete cascade,
  student_id   uuid not null references public.students on delete cascade,
  starts_at    timestamptz not null,
  duration_min int not null default 60 check (duration_min between 10 and 300),
  location     text not null default '',
  notes        text not null default '',
  status       text not null default 'marcada' check (status in ('marcada', 'realizada', 'cancelada')),
  response     text not null default 'pendente' check (response in ('pendente', 'confirmada', 'recusada')),
  created_at   timestamptz not null default now()
);
create index if not exists sessions_trainer_idx on public.sessions (trainer_id, starts_at);
create index if not exists sessions_student_idx on public.sessions (student_id, starts_at);
alter table public.sessions enable row level security;
revoke all on public.sessions from anon;
drop policy if exists sessions_trainer on public.sessions;
create policy sessions_trainer on public.sessions for all to authenticated
  using (trainer_id = auth.uid())
  with check (trainer_id = auth.uid() and student_id in (select id from public.students where trainer_id = auth.uid()));
drop policy if exists sessions_student on public.sessions;
create policy sessions_student on public.sessions for select to authenticated
  using (student_id = public.my_student_id());

-- O aluno só responde (confirma ou recusa) as próprias aulas futuras.
create or replace function public.respond_session(p_session uuid, p_response text) returns void
language plpgsql security definer set search_path = public as $$
begin
  if p_response not in ('confirmada', 'recusada') then raise exception 'Resposta inválida'; end if;
  update sessions set response = p_response
   where id = p_session and student_id = my_student_id() and status = 'marcada' and starts_at > now();
  if not found then raise exception 'Aula não encontrada'; end if;
end $$;
revoke all on function public.respond_session(uuid, text) from public, anon;
grant execute on function public.respond_session(uuid, text) to authenticated;
