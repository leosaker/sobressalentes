-- =====================================================================
-- Agenda os lembretes de treino: chama a função "reminders" a cada 15 minutos.
-- Antes: Database → Extensions → ative "pg_cron" e "pg_net".
-- Troque SEU-PROJETO pelo código do seu projeto (está na Project URL)
-- e SEU-CRON-SECRET pelo mesmo valor que você salvou em Edge Functions → Secrets.
-- =====================================================================
select cron.schedule(
  'lembretes-de-treino',
  '*/15 * * * *',
  $$ select net.http_post(
       url := 'https://SEU-PROJETO.supabase.co/functions/v1/reminders',
       headers := '{"Content-Type": "application/json", "x-cron-secret": "SEU-CRON-SECRET"}'::jsonb,
       body := '{}'::jsonb
     ) $$
);
-- Para parar os lembretes: select cron.unschedule('lembretes-de-treino');
