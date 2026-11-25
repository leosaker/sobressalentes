// Configuração do Supabase — preencha com os dados do SEU projeto.
// Supabase → Project Settings → API (ou "Connect"):
//   SUPABASE_URL      = "Project URL"           (ex.: https://abcdefgh.supabase.co)
//   SUPABASE_ANON_KEY = "anon public" / "publishable" key
// Essa chave pode ficar no site: a segurança é garantida pelas regras do arquivo supabase/schema.sql.
//
// VAPID_PUBLIC_KEY = chave PÚBLICA das notificações (gere em ferramentas/gerar-chaves.html).
// Deixe vazio para usar o app sem notificações.
window.APP_CONFIG = {
  SUPABASE_URL: '',
  SUPABASE_ANON_KEY: '',
  VAPID_PUBLIC_KEY: '',
  APP_NAME: 'Meu Personal'
};
