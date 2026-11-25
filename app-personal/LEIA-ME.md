# Meu Personal — app de treinos com login e acompanhamento

App de celular (PWA, instalável na tela inicial) para o personal montar as séries dos alunos com os
**próprios vídeos** e acompanhar a evolução de cada um. Usa o **Supabase** (plano grátis) para login e banco de dados.

## O que o app faz
**Personal**
- Login com e-mail e senha (só e-mails autorizados viram personal)
- Alunos com objetivo e observações privadas (🔒 só você vê)
- Treinos A, B, C… com séries, repetições, carga, descanso e observação, salvos automaticamente
- Biblioteca de exercícios com o link do seu vídeo (YouTube não listado, Google Drive, Vimeo ou .mp4)
- Convite por WhatsApp: o aluno cria a conta pelo link e o treino aparece na hora
- **Acompanhamento**: aviso de treino novo, alunos sem treinar há 7+ dias, convites pendentes,
  treinos em 7 e 30 dias, esforço médio, gráfico semanal, comentários e cargas usadas em cada exercício
- Mudou o treino? O aluno vê na hora, sem precisar reenviar link
- **Notificações no celular**: aviso quando um aluno finaliza o treino (toque e abre direto nele) e botão
  "📣 Avisar o aluno" no editor de treino (opcional — veja o passo 6)
- **Avaliação física**: peso, altura, % de gordura e 10 circunferências, com IMC, massa magra e massa gorda
  calculados na hora, gráfico de evolução de cada medida e comparação com a avaliação anterior
- **Fotos de evolução** (frente, lado e costas), comprimidas no celular e guardadas em pasta privada:
  só você e o aluno veem. Comparação "primeira × última" lado a lado
- **Anamnese e PAR-Q**: o aluno responde no app (aparece um aviso até ele responder). Se ele marcar "sim"
  em alguma pergunta do PAR-Q, você e ele veem o alerta para pedir liberação médica
- **Evolução de carga**: gráfico por exercício com as cargas que o aluno anotou (ex.: 30 kg → 42,5 kg, +42%)
- **Validade do treino**: data de vencimento (padrão de 6 semanas, com atalhos de 4/6/8/12) e aviso de "treinos para renovar"
- **Responder o aluno**: responda o comentário de cada treino; ele recebe o aviso no app
- **Modelos de treino** (aba 📋 Modelos): monte uma vez e aplique em vários alunos com um toque.
  Também dá para usar "Salvar como modelo" dentro de um treino, ou escolher um modelo em "+ Novo treino"
- **Bi-set, tri-set e circuito**: use "🔗 Juntar com o anterior". Os exercícios aparecem agrupados (2A, 2B…)
  e o descanso só começa no fim do grupo
- **Técnicas marcadas**: drop-set, rest-pause, pirâmide, até a falha, excêntrica lenta e pico de contração.
  O aluno vê a técnica em destaque com a explicação. Na pirâmide, escreva as reps por série (ex.: 15-12-10-8)
  e cada série mostra as suas repetições
- **Três tipos de exercício**: 🔁 séries × repetições, ⏱ por tempo (ex.: prancha 30 s) e 🏃 cardio
  (ex.: esteira 20 min, com intensidade). Cada exercício da biblioteca tem um tipo padrão

**Aluno**
- Login próprio, vídeo de execução em cada exercício
- Marca as séries, o cronômetro de descanso começa sozinho (som + vibração)
- Exercício por tempo: toca na série e o cronômetro de execução conta o tempo; no cardio, toca em "▶ Iniciar"
- Anota a carga usada (o app lembra a do último treino)
- Ao finalizar: nota de esforço (1–10) e comentário para o personal
- Vê a resposta do personal, o próprio gráfico de evolução de carga e quando o treino vence
- Aba **📏 Avaliação**: suas medidas, gráficos, fotos de evolução e o questionário de saúde
- Notificações: resposta do personal, treino atualizado e lembrete "Hoje é dia de treino!" nos dias e horário que escolher
- Histórico e treinos do mês. Funciona offline: o registro é enviado quando a internet volta

## Como colocar no ar (uns 15 minutos, tudo grátis)

### 1. Criar o banco no Supabase
1. Crie uma conta em https://supabase.com e um **New project** (região: São Paulo).
2. Vá em **SQL Editor → New query**, cole todo o conteúdo de `supabase/schema.sql` e clique em **Run**.
3. Ainda no SQL Editor, autorize o SEU e-mail de personal:
   ```sql
   insert into public.trainer_allowlist (email) values ('seu-email@exemplo.com');
   ```

> **Já tinha rodado o `schema.sql` antes?** Rode também as atualizações que faltam, em ordem:
> `supabase/migracao-v2.sql`, `migracao-v3.sql` e `migracao-v4.sql` (ou rode o `schema.sql` inteiro de novo, que não apaga nada).
> A v4 cria a pasta privada **fotos** no Storage do Supabase.

### 2. Ligar o app ao Supabase
1. No Supabase, abra **Project Settings → API** (ou o botão **Connect**).
2. Copie a **Project URL** e a chave **anon / publishable** para o arquivo `config.js`.
   (Essa chave pode ficar pública: quem protege os dados são as regras do `schema.sql`.)

### 3. Publicar o app
- **Netlify Drop**: acesse https://app.netlify.com/drop e arraste a pasta `app-personal`.
  Você recebe um endereço `https://...netlify.app`.
- Ou **GitHub Pages**, num repositório só do app.

### 4. Ajustar os links de e-mail
No Supabase, em **Authentication → URL Configuration**, coloque o endereço do seu app em **Site URL**
e também em **Redirect URLs**. Assim os links de confirmação de e-mail e de "esqueci minha senha" voltam para o app.

> Dica: em **Authentication → Providers → Email** dá para desligar "Confirm email". Assim o aluno entra
> direto sem precisar confirmar o e-mail. É mais prático, mas menos seguro.

### 6. Notificações no celular (opcional)
O app funciona sem isso. Para ativar os avisos e lembretes:

1. **Banco:** se ainda não rodou, rode `supabase/migracao-v5.sql` no SQL Editor.
2. **Chaves:** abra `ferramentas/gerar-chaves.html` no navegador (no app publicado: `https://SEU-APP/ferramentas/gerar-chaves.html`)
   e toque em **Gerar chaves**. As chaves são criadas no seu navegador; nada é enviado.
3. **Chave pública:** cole em `config.js` → `VAPID_PUBLIC_KEY` e publique o app de novo.
4. **Segredos:** no Supabase, **Edge Functions → Secrets**, crie:
   `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `CRON_SECRET` (os três da página) e `VAPID_SUBJECT` = `mailto:seu-email@exemplo.com`.
5. **Funções:** em **Edge Functions → Deploy a new function → Via Editor**:
   - nome `notify`: cole o conteúdo de `supabase/functions/notify/index.ts` e faça o deploy;
   - nome `reminders`: cole `supabase/functions/reminders/index.ts`, faça o deploy e, nos detalhes da função,
     **desligue "Verify JWT"** (ela é protegida pelo `CRON_SECRET`).
6. **Lembretes de treino:** em **Database → Extensions**, ative `pg_cron` e `pg_net`. Depois rode
   `supabase/lembretes-cron.sql` no SQL Editor, trocando `SEU-PROJETO` e `SEU-CRON-SECRET`.
7. **No celular:** personal em ⚙️ Ajustes, aluno em 👤 Conta → **Ativar notificações neste celular**.
   - **Android:** funciona no Chrome.
   - **iPhone:** precisa do iOS 16.4 ou mais novo, e o app tem que estar na Tela de Início
     (Safari → Compartilhar → Adicionar à Tela de Início). Abra pelo ícone e ative.

### 7. Usar
1. Abra o endereço no celular, toque em **Criar conta** com o e-mail autorizado e depois em **Criar meu perfil de personal**.
2. Em 🎬 Exercícios, adicione os exercícios básicos e cole os links dos seus vídeos.
3. Cadastre um aluno, monte o treino e toque em **WhatsApp** no cartão de convite.
4. Na aba 📈 Acompanhar você vê cada treino que os alunos finalizam.

Para instalar como app: no iPhone, Safari → Compartilhar → **Adicionar à Tela de Início**.
No Android, Chrome → ⋮ → **Instalar app**.

## Segurança
- Cada personal só vê os próprios alunos, exercícios e registros.
- O aluno só vê o próprio treino e não vê as observações privadas.
- Cada código de convite vale para uma conta só. "Gerar novo convite" desliga o acesso atual do aluno.
- Só e-mails da tabela `trainer_allowlist` podem virar personal.

## Testar no computador
```
cd app-personal && python3 -m http.server 8000
```
Abra http://localhost:8000. É preciso preencher o `config.js` antes.
