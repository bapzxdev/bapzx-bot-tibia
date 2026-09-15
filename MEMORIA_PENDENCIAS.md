# Memória de Pendências

Lista única de pendências, observações e bloqueios do projeto BAPZX / RUBINI COINS.
Atualizar sempre que algo mudar de estado.

## Bloqueios que dependem do dono (1 clique quando quiser)

- [x] **Aplicar `supabase_migracao_v119.sql` (v2.1.0) — FEITO pelo dono.**
      Tabela `servicos` criada; Intermediação BAPZX R$5 saiu da tabela
      `itens` (itens do jogo) e agora só aparece em `/api/servicos`.
      Validado em produção: `/api/servicos` → Intermediação; `/api/itens` →
      vazio.
- [x] **Aplicar `supabase_migracao_v118.sql` (v2.0.0) — FEITO pelo dono.**
      Tabelas `users` e `grupos` no ar (o `/api/grupos` retorna vazio porque
      os 4 links ainda estão vazios — preencher no `/admin/grupos`).
- [ ] **Publicar o app Google (OAuth)** — console.cloud.google.com/auth →
      Settings → Branding → Publishing status → **Publish app**.
      Hoje o app está em modo Teste: só o e-mail `lucascristianini1@gmail.com`
      consegue logar na área do cliente/admin. Publicar libera o login para
      **qualquer conta Google** (grátis; não precisa de verificação, pois só
      usa nome e e-mail do perfil).
- [ ] **(Opcional) Criar env `MASTER_EMAILS` no Render** com o e-mail do dono.
      Sem ela, o RBAC usa `ADMIN_EMAILS` como lista de MASTER (mínimo:
      `lucascristianini1@gmail.com`). Vale para quando criar outros usuários
      com cargo no `/admin/usuarios`.
- [ ] **Portfólio `itens.html`** — os "Item Exemplo A/B/C..." foram
      substituídos automaticamente pelos itens reais do `/api/itens` (inclui
      o seed "Intermediação BAPZX" R$5 depois da migração v118). O dono ajusta
      categoria/descrição/valores quando definir como vender itens.
- [ ] **Fase C (divulgação) e 1ª venda real** — VETADA pelo dono até tudo
      ajustado. Quando liberar:
      - ficha de divulgação (o que falar, onde postar);
      - post em comunidades/grupos de Tibia;
      - avaliar o WEB DIVULGADOR para divulgação programada.
      - validar venda real de ponta a ponta (cliente paga Pix, `/webhook/mp`
        confirma, `/entregue` encerra com aviso).

## A confirmar com o dono

- [ ] Número do WhatsApp **(19) 99181-3598** e valor do **Serviço BAPZX =
      R$20/h** (confirmar antes de divulgação real).
- [ ] **Limite por venda** a revisar (entrega em até 10 min definida;
      limite de TC por pedido não fechado).

## Qualidade / docs

- [x] **Scan de segurança com OWASP ZAP (13/09, v1.14.16) — CONCLUÍDO.** Primeiro scan
      (spider + passive + active) em bapzx-bot-tibia.onrender.com. Único achado real:
      rotas inexistentes e método errado davam 500 "erro" (Application Error
      Disclosure) e cada probe avisava o dono no Telegram (spam). Correção: handlers
      `404` e de `HTTPException` no bot.py — 404/405 limpos e sem aviso; 500 real
      mantém o aviso ao dono. Alertas Medium do ZAP (anti-clickjacking/CSP/CORS*/SRI)
      são do PORTFÓLIO no GitHub Pages (o ZAP seguiu o 302 da `/`), não do bot —
      sem ação no código do bot; opcional: adicionar CSP no portfólio depois.
- [x] **Pentest OWASP ZAP (15/09, v2.0.2) — CONCLUÍDO.** Scan na nova atualização
      (RBAC + legal + grupos). Bot: **35/35 checagens OK** (`pentest_v202.py`:
      RBAC bypass, CSRF, XSS, info disclosure, rotas legais, APIs, error
      handlers). Corrigidos em `security_headers` (`bot.py:~727`): **HSTS** e
      **CSP** (antes ausentes). Confirmado em produção: 6/6 headers em
      `/health`, `/privacidade`, `/termos`, `/reembolso`, `/api/grupos`,
      `/api/itens`, `/robots.txt`. Alertas ZAP remanescentes (CORS `*`,
      anti-clickjacking, SRI, X-Content-Type-Options aparente) são do
      **portfólio GitHub Pages** (o ZAP segue o 302 da `/`); o scan direto de
      `/privacidade` em v2.0.2 não gerou alerta. `Application Error Disclosure`
      = 500 transitório do cold start em `/robots.txt` (hoje 404 limpo).
      Relatórios: `%TEMP%\zap-reports\bapzx-v201.html` e `bapzx-v202.html`.
- [ ] **Loop do formato compacto RESOLVIDO (12/09, v1.14.13)** — dono digitou
      "inmortals - 1250 - pix" e o bot nao reconhecia (caia na IA, que respondia
      a saudacao fixa para "sim"). Parser tolerante implementado (fallback de
      quantidade/char, dicas no looks_like_order, bloqueio de pedido sem qtd/char).
      Validado ao vivo: mensagem compacta -> CONFIRMAÇÃO DO PEDIDO -> "sim" ->
      pedido 49 (inmortals, 1250, R$112,50) + QR MP pending. Pedido 48 foi o
      "lixo" (char/tc null) que o bloqueio agora evita. A confirmar com o dono:
      repetir o fluxo no celular para conferir a experiência real.
- [ ] **ERRO 500 em /webhook CORRIGIDO (12/09, v1.14.15)** — duplo toque/reenvio
      do botão SIM fazia _finalizar_confirmacao_char rodar com AWAITING_CHAR
      vazio → KeyError (reproduzido localmente) → 500. Guarda `if not pending`
      no topo resolveu; validado ao vivo (2× char_sim → 200, sem novo pedido).
- [ ] **API do RubiNot REMOVIDA (12/09, v1.14.14)** — pedido do dono (muito
      empenho entrar em contato com a staff). Confirmacao agora usa o char
      digitado pelo cliente, sem consulta externa; curl_cffi fora do
      requirements. Validado ao vivo: "inmortals - 1250 - pix" ->
      CONFIRMAÇÃO DO PEDIDO -> "sim" -> pedido 51 + QR MP pending. Removida
      tambem a pendencia de contatar a staff do RubiNot.
- [ ] **Limpeza de pedidos de teste 22/32/33/34/35/36/37/38/47/48/49/50/51** (chat do
      dono) — todos pendentes no Supabase.
- [ ] Conferir visualmente a **resposta da IA em atendimento real** (o pedido
      grava certo; falta confirmar a qualidade da resposta no chat, pois o
      Google Login mudou o fluxo).
- [ ] Revisar `manual.txt` (raiz de MEUS PROJETOS) com os recursos novos:
    Google Login, `/cliente`, `/admin`, `TELEGRAM_WEBHOOK_SECRET`, e agora o fluxo de
    confirmação do personagem via RubiNot (v1.12.0). Tema do ROS (roleta) também
    se aplicável.

- [ ] **Teste ao vivo (v1.13.0)** — FEITO: webhook com secret validado, confirmacao manual
    (SIM salva / NAO cancela) testada ao vivo com Inmortals e Rei Leao.
    RubiNot 403 a partir do Render (IP de datacenter bloqueado) -> fallback
    manual implementado. ENCERRADO 12/09 (v1.14.14): API do RubiNot removida
    a pedido do dono; confirmacao usa o char digitado. Pendente: publicar
    app Google e revisar manual.txt.

- [x] **Teste ao vivo v1.14.0 (CONCLUÍDO 12/09, v1.14.6)** — migração
    `supabase_migracao_v114.sql` aplicada e verificada (feedback/feedback_score OK).
    Fluxo completo validado ao vivo no Supabase: order → char_sim → email →
    `/pago` → `/entregue` → feedback (nota 5 + texto gravados). `/pago`/`/entregue`
    voltaram a funcionar após o dono inserir `TELEGRAM_OWNER_CHAT_ID` na env do
    Render (antes respondiam "Comando indisponível"). char_sim dava 500
    INTERMITENTE após salvar (sem exceção local com Supabase real; suspeita:
    timeout de rede do Telegram) → v1.14.5 blindou as chamadas ao Telegram e
    v1.14.6 adicionou errorhandler global que loga e avisa o dono no Telegram
    (última rodada: char_sim 200). Suite v170 reconstruída (21 checagens OK).
    Pendente: **limpar pedidos de teste 22/32/33/35** (chat do dono).

## Concluído (manter como histórico; reabrir se voltar a aparecer)

- [x] Mojibake / dupla codificação nas mensagens do bot (12/09, v1.14.3) — CORRIGIDO.
      Acentos e emojis apareciam errados no Telegram (ex.: "confirmaÃ§Ã£o"). Causa:
      strings duplamente codificadas no bot.py. Audit cp1252 final: 0 literais restantes;
      bytes hex conferidos. Testes verdes.
- [x] Auditoria de segurança completa (12/09, v1.14.1) — SEM segredos vazados em
      repos/histórico/backups/árvore; apenas dono como colaborador; cookie de
      sessão com SECRET_KEY padrão rejeitado em prod; reforços aplicados:
      throttle no `/webhook/mp` e allowlist de host no `/login`.
- [x] Excluir client OAuth antigo (Desktop app `r2512...`) no Google — FEITO.
- [x] `TELEGRAM_WEBHOOK_SECRET` ativo no Render — FEITO e verificado
      (webhook responde 403 sem o header correto).
- [x] Usuário do GitHub renomeado para `bapzxdev` (URL do portfólio =
      https://bapzxdev.github.io/bapzx-portfolio/) — FEITO.
- [x] Auditoria de segurança v1.11.2 (XSS `/dashboard`, referer exato,
      sessão 7 dias + headers, secret do webhook) — FEITA.