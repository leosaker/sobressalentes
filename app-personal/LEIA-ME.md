# Meu Personal — app de treinos para alunos

App de celular (PWA) para o personal montar as séries dos alunos com os **próprios vídeos**
e enviar o treino por link (WhatsApp). O aluno abre o link no celular, assiste ao vídeo de cada
exercício, marca as séries e usa o cronômetro de descanso. Não precisa de App Store nem de servidor.

## Funcionalidades
**Personal**
- Cadastro de alunos (objetivo e observações)
- Treinos A, B, C… com séries, repetições, carga, descanso e observação por exercício
- Biblioteca de exercícios com link do seu vídeo (YouTube não listado, Google Drive, Vimeo ou .mp4)
- Enviar treino por WhatsApp, copiar link ou compartilhar
- "Ver como o aluno" (pré-visualização)
- Backup/restauração em arquivo .json

**Aluno**
- Vídeo de execução embutido em cada exercício
- Marca cada série e o cronômetro de descanso começa sozinho (com som e vibração)
- Barra de progresso do dia, histórico de treinos concluídos
- Funciona offline depois de aberto e pode ser adicionado à tela inicial

## Como publicar (grátis)
O link só funciona para o aluno quando o app está publicado na internet. Escolha uma opção:

- **Netlify Drop**: acesse https://app.netlify.com/drop e arraste a pasta `app-personal`. Você recebe um endereço `https://...netlify.app`.
- **GitHub Pages**: num repositório próprio, coloque estes arquivos e ative *Settings → Pages*.

Abra o endereço no seu celular, use a área do personal e toque em "Enviar treino para o aluno".

## Como colocar seus vídeos
1. Grave o exercício.
2. Envie para o YouTube como **Não listado** (ou para o Google Drive com "qualquer pessoa com o link").
3. Cole o link no exercício, na aba 🎬 Exercícios.

## Limitações desta versão
- Os dados do personal ficam salvos no aparelho. Use o backup para trocar de aparelho.
- O treino vai dentro do link. Se você alterar o treino, envie o link de novo.
- Não há login nem pagamento, e o aluno não envia as cargas de volta ao personal.
  Para isso, a próxima etapa é ligar o app a um banco de dados (ex.: Supabase/Firebase).

## Testar no computador
```
cd app-personal && python3 -m http.server 8000
```
Depois abra http://localhost:8000
