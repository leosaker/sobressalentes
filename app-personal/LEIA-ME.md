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
- **Ferramentas por aluno**: na ficha de cada aluno, ligue ou desligue o que ele vê (vídeos, cronômetro, cargas,
  série a série, troca de exercício, periodização, histórico, avaliação, fotos, questionário, notificações,
  mensalidades e agenda). O que estiver desligado **não aparece** para o aluno. Há um padrão em ⚙️ Ajustes e
  atalhos "Completo" / "Essencial"
- **Negócio** (aba 💼):
  - **Painel**: alunos ativos, frequência média, treinos por semana, receita por mês, valores a receber e em atraso,
    e uma lista do que precisa de atenção (pagamentos informados, atrasos, aulas sem confirmação, treinos vencendo, alunos parados)
  - **Financeiro**: mensalidade e dia de vencimento por aluno, "Gerar mensalidades do mês" com um toque, cobranças avulsas,
    cobrança pelo WhatsApp com Pix copia e cola. O aluno paga pelo app (**QR Code Pix** com o valor) e toca em "Já paguei";
    você confirma o recebimento. Cadastre sua chave Pix em ⚙️ Ajustes
  - **Agenda**: aulas presenciais (com repetição semanal); o aluno confirma ou avisa que não vai poder
- Exercícios e modelos de treino ficam juntos na aba 📚 **Biblioteca**
- **Notificações no celular**: aviso quando um aluno finaliza o treino (toque e abre direto nele) e botão
  "📣 Avisar o aluno" no editor de treino (opcional — veja o passo 5)
- **Avaliação física**: peso, altura, % de gordura (digitado ou calculado por **dobras cutâneas — Pollock 3 ou 7 dobras**, equação de Siri) e 10 circunferências, com IMC, massa magra e massa gorda
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
- **Periodização**: divida o treino em fases (ex.: Adaptação → Hipertrofia → Força → Deload) com % de carga e
  repetições por fase. Modelos prontos (linear 8 semanas, ondulatória 6 semanas, progressão 4 semanas) ou personalizada.
  O aluno vê "Semana 3 de 8 · Força" e as cargas já calculadas (40 kg +10% → 44 kg); a validade acompanha o ciclo
- **Alternativas de exercício**: em cada exercício, cadastre alternativas. Se o aparelho estiver ocupado, o aluno
  troca no app (só naquele treino) e você vê no registro "Cadeira extensora ↔ no lugar de Leg press"
- **Técnicas marcadas**: drop-set, rest-pause, pirâmide, até a falha, excêntrica lenta e pico de contração.
  O aluno vê a técnica em destaque com a explicação. Na pirâmide, escreva as reps por série (ex.: 15-12-10-8)
  e cada série mostra as suas repetições
- **Três tipos de exercício**: 🔁 séries × repetições, ⏱ por tempo (ex.: prancha 30 s) e 🏃 cardio
  (ex.: esteira 20 min, com intensidade). Cada exercício da biblioteca tem um tipo padrão

**Aluno**
- Login próprio, vídeo de execução em cada exercício
- Marca as séries, o cronômetro de descanso começa sozinho (som + vibração)
- Anota reps e carga **de cada série** (ex.: 8×44 · 7×46 · 6×47,5); o app sugere a carga da última vez
- Exercício por tempo: toca na série e o cronômetro de execução conta o tempo; no cardio, toca em "▶ Iniciar"
- Anota a carga usada (o app lembra a do último treino)
- Ao finalizar: nota de esforço (1–10) e comentário para o personal
- Vê a resposta do personal, o próprio gráfico de evolução de carga e quando o treino vence
- Aba **📏 Avaliação**: suas medidas, gráficos, fotos de evolução e o questionário de saúde
- Notificações: resposta do personal, treino atualizado e lembrete "Hoje é dia de treino!" nos dias e horário que escolher
- Histórico e treinos do mês. Funciona offline: o registro é enviado quando a internet volta

## Marca do professor (um app para cada professor)
O app é o mesmo para todos; o que muda é a **marca**: nome, logo, cores, frase, Instagram e WhatsApp.
Tudo isso fica no arquivo `marca.js` e nos ícones (`icon-192.png`, `icon-512.png`, `apple-touch-icon.png`,
`badge-96.png`), mais o `manifest.json`.

**Marca atual:** L Castro Personal (@lcastropersonal), **provisória**: monograma "LC" e cores padrão,
até chegarem o logo e as cores oficiais.

**Para criar ou trocar uma marca:**
1. Abra `ferramentas/criar-marca.html` no navegador (no app publicado: `https://SEU-APP/ferramentas/criar-marca.html`).
2. Preencha nome, frase, cores, Instagram e WhatsApp e envie o logo. A prévia mostra como vai ficar
   e avisa se alguma cor deixar os textos difíceis de ler.
3. Clique em **Baixar pacote da marca**. Descompacte o `.zip` na pasta do app, substituindo os arquivos.
4. Publique de novo.

As cores são ajustadas sozinhas para ficarem legíveis no modo claro e no escuro. Se a cor da marca for clara
(ex.: amarelo), os textos sobre ela ficam pretos.

**Para atender outro professor:** faça uma **cópia da pasta do app**, aplique a marca dele e publique num
endereço próprio (ex.: outro site no Netlify). O recomendado é cada professor ter **o próprio projeto no
Supabase** (os passos abaixo): os dados ficam separados e cada um usa a sua cota gratuita.
Também é possível vários professores usarem o mesmo Supabase (cada um só vê os próprios alunos);
basta autorizar o e-mail de cada um na tabela `trainer_allowlist`.

## Como colocar no ar (uns 15 minutos, tudo grátis)

### 1. Criar o banco no Supabase
1. Crie uma conta em https://supabase.com e um **New project** (região: São Paulo).
2. Vá em **SQL Editor → New query**, cole todo o conteúdo de `supabase/schema.sql` e clique em **Run**.
3. Ainda no SQL Editor, autorize o SEU e-mail de personal:
   ```sql
   insert into public.trainer_allowlist (email) values ('seu-email@exemplo.com');
   ```

> **Já tinha rodado o `schema.sql` antes?** Rode também as atualizações que faltam, em ordem:
> `supabase/migracao-v2.sql` até a `migracao-v8.sql` (ou rode o `schema.sql` inteiro de novo, que não apaga nada).
> A v4 cria a pasta privada **fotos** no Storage do Supabase; a v6 adiciona periodização e dobras cutâneas; a v7, ferramentas por aluno, financeiro e agenda; a v8 deixa o banco rápido com muitos alunos (índices e regras de acesso otimizadas).

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

### 5. Notificações no celular (opcional)
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

### 6. Usar
1. Abra o endereço no celular, toque em **Criar conta** com o e-mail autorizado e depois em **Criar meu perfil de personal**.
2. Em 🎬 Exercícios, adicione os exercícios básicos e cole os links dos seus vídeos.
3. Cadastre um aluno, monte o treino e toque em **WhatsApp** no cartão de convite.
4. Na aba 📈 Acompanhar você vê cada treino que os alunos finalizam.

Para instalar como app: no iPhone, Safari → Compartilhar → **Adicionar à Tela de Início**.
No Android, Chrome → ⋮ → **Instalar app**.

## Desempenho e uso sem internet (testado)
- Banco testado com 200 alunos e 50 mil treinos registrados: todas as telas abrem em menos de 0,12 s.
- O app busca os dados em páginas, então nada some quando a conta passa de 1.000 registros.
- O painel carrega os últimos 60 dias. A ficha do aluno busca o histórico completo dele quando você abre.
- Sem internet, o treino do aluno fica guardado no celular. Ele é enviado uma vez só quando a conexão volta, sem duplicar.
- Alterações no treino que não salvaram (sem sinal) são tentadas de novo sozinhas. O app avisa antes de fechar com algo não salvo.
- Toque duplo em botões não cria aluno, cobrança ou registro repetido.
- Fotos de 12 MP são reduzidas para cerca de 1280 px antes do envio (~0,5 MB).
- Lembretes diários: 5.000 alunos processados em segundos, com envio em paralelo.

## Segurança
- Cada personal só vê os próprios alunos, exercícios e registros.
- O aluno não consegue mudar valores nem marcar cobranças como pagas — só avisar "já paguei" e responder às próprias aulas.
- O aluno só vê o próprio treino e não vê as observações privadas.
- Cada código de convite vale para uma conta só. "Gerar novo convite" desliga o acesso atual do aluno.
- Só e-mails da tabela `trainer_allowlist` podem virar personal.

## Testar no computador
```
cd app-personal && python3 -m http.server 8000
```
Abra http://localhost:8000. É preciso preencher o `config.js` antes.
