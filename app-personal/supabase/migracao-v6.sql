-- =====================================================================
-- Atualização v6 — Periodização e avaliação por dobras cutâneas.
-- Rode UMA vez no SQL Editor se você já tinha rodado o schema.sql antes
-- (rodar o schema.sql inteiro de novo também funciona).
-- A carga série a série e as alternativas de exercício ficam dentro dos treinos
-- e dos registros que já existem; não precisam de colunas novas.
-- =====================================================================
-- {"start": "2026-11-25", "phases": [{"name": "Adaptação", "weeks": 2, "pct": -10, "reps": "15", "note": "..."}]}
alter table public.plans       add column if not exists period jsonb;
alter table public.templates   add column if not exists period jsonb;
-- {"proto": "jp7", "sex": "F", "age": 32, "values": {"triceps": 18, ...}, "sum": 120, "bf": 24.1}
alter table public.assessments add column if not exists skinfolds jsonb;
