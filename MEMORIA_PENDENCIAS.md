## LOG v2.7.8 (19/09/2026) - Analytics: corrigido NameError na tabela "Serviços mais vendidos"
- Erro real-reportado no dashboard Analytics (`/admin/analytics`): quando havia
  serviços no período (`top_servicos` não-vazio), o generator de `serv_rows`
  (painel.py ~1341) referenciada `qtd` e `total` (variáveis inexistentes) em vez
  de `d['qtd']` / `d['total']` → `NameError: name 'qtd' is not defined` → HTTP 500.
  Só disparava com dados; com mocks de painel vazios passava (o fallback
  `or "<tr>...Sem vendas..."` nunca avaliava o generator).
- Fix (painel.py, admin_analytics): generator agora usa `d['qtd']` (qtd vendida)
  e `_fmt_brl(d['total'])` (receita) por serviço.
- VERSION painel.py **2.7.8**.
- Validado: py_compile OK; repro com dados realistas (3 visitas + 2 pedidos +
  1 profile + 2 serviços concluidos/pago) → `/admin/analytics?per=7/14/30`
  todas 200, sem traceback; "Venda 100/250 coins" renderizam.

# Memória de Pendências

Lista única de pendências, observações e bloqueios do projeto BAPZX / RUBINI COINS.

## LOG v2.7.8 (19/09/2026) - Analytics: corrigido NameError na tabela "Serviços mais vendidos"
- Erro real-reportado no dashboard Analytics (`/admin/analytics`, v2.7.7): quando
  havia serviços no período (top_servicos não-vazio), o generator `serv_rows`
  referenciava `qtd`/`total` (variáveis inexistentes) em vez de `d['qtd']`/`d['total']`
  → `NameError: name 'qtd' is not defined` → HTTP 500 sênio se apresenta no roteiro.
- Fix (painel.py, admin_analytics): linha do generator `serv_rows` agora usa
  `d['qtd']` (quantidade) e `_fmt_brl(d['total'])`.
- VERSION painel.py **2.7.8**.
- Validado: py_compile OK; test client com dados realistas (3 visitas + 2 pedidos
  pago + 1 profile + 2 serviços concluidos/pago) → `/admin/analytics?per=7/14/30`
  todas 200 sem traceback; "Venda 100 coins"/"Venda 250 coins" renderizam.
- Observação: quando top_servicos vazio o fallback `or "<tr>...Sem vendas..."`
  (que não toca qtd/total) mascarava o bug em testes de mocks vazios.

Atualizar sempre que algo mudar de estado.

## Bloqueios que dependem do dono (1 clique quando quiser)

- [x] **Aplicar `supabase_migracao_v122.sql` (v2.7.1 — valor cobrado automático) — FEITO (17/09)**
      verificado no Supabase: colunas `valor_hora`/`desconto` presentes em
      `servicos_manuais` (registro-id 1 já com valor_hora 20).
      Deploy v2.7.1 confirmado: `/health` "bot ok v2.7.1".
- [x] **Aplicar `supabase_migracao_v121.sql` (v2.7.0 — Service + Segurança) — FEITO pelo dono**
      (criou `public.servicos_manuais` e `public.sessoes`; a área Service foi testada ao vivo).
- [ ] **Validar `/admin/services` ao vivo com o cálculo novo (v2.7.1)**.
      Já testado com valor_hora 20 (registro id 1 gravado; deploy v2.7.1 no ar).
      Conferir um caso com horas fracionadas (1,5h → R$ 30) e um com desconto.
- [ ] **Testar `/admin/seguranca` ao vivo (v2.7.0).**
      Ver as sessões do seu login (IP/dispositivo), usar "Encerrar" na própria sessão
      para confirmar que desloga e na de outro dispositivo. Também conferir que
      /admin/audit registra login/logout (sistema@bapzx) e as ações servico_*.
- [ ] **Testar `/admin/audit` ao vivo (v2.5.0, item 14 — FEITO no código).**
      Página com busca `q`, dropdown de ação, filtro por e-mail, paginação
      50/pág e Exportar CSV; eventos do bot (pedido_criado, pix_gerado,
      pedido_pago/entregue, feedback_recebido — email sistema@bapzx, ip
      sistema) já gravam no `audit_log`. Conferir quando preencher
      config/cupons e fizer pedidos de teste.
- [ ] **Preencher `/admin/config` (v2.4.0, item 11 — FEITO no código).** A
      aba Configurações está no ar (Site/Conta/Pagamentos/Notificações) mas
      os campos estão vazios. Preencher: **Site** (logo, nome, banner, slogan,
      textos topo/rodapé, links portfólio/WhatsApp/Telegram/Instagram/YouTube/
      Discord/TikTok), **Pagamentos** (pix_chave — o bot usa como preferido
      com fallback na env PIX_KEY —, beneficiário, conferir Gateway MP e
      preços), **Notificações** (toggles pedido/pix/erro). Depois conferir
      `/api/site` e (futuro) ligar no portfólio (roadmap itens 8/9/14).
- [x] **Aplicar `supabase_migracao_v120.sql` (v2.3.0, cupons) — FEITO pelo dono
      (16/09).** Tabela `public.cupons`: codigo (unique), tipo percentual|fixo,
      valor numeric, validade date, limite_usos (0=ilimitado), usos (contador),
      produto_id/servico_id/grupo_id opcionais, ativo + índices. Agora
      `/admin/cupons` lista/cria com a tabela real. Falta o dono criar o cupom
      de exemplo `BAPZVESPERIA` (10%) e testar ativar/desativar/excluir.
- [ ] **Validar cargos e notificações ao vivo (v2.6.0, itens 13 e 9 — FEITOS no
      código).** (a) `/admin/usuarios`: revisar cargos dos usuários cadastrados
      (cargos antigos ADMIN/MANAGER/OPERADOR/SUPORTE são normalizados
      automaticamente, mas o ideal é re-salvar) e conferir as descrições de
      cargo nos formulários; (b) `/admin/notificacoes`: conferir os contadores
      (novas vendas 24h, serviços 7d, pendentes, pagamentos 24h, novos clientes
      7d, erros de pagamento 7d) e os Alertas administrativos (config vazia /
      tabela cupons). Sino do dashboard soma o feed por permissão.
- [x] **Aplicar `supabase_migracao_v119.sql` (v2.1.0) — FEITO pelo dono.**
      Tabela `servicos` criada; Intermediação BAPZX R$5 saiu da tabela
      `itens` (itens do jogo) e agora só aparece em `/api/servicos`.
      Validado em produção: `/api/servicos` → Intermediação; `/api/itens` →
      vazio.
- [x] **Quedas momentâneas do Supabase → endpoints públicos (v2.1.1) — FEITO.**
      Avisos "ERRO 500" no Telegram eram falha real de conexão com o Supabase
      (não testes). `_fetch_public` criado: `/api/itens`, `/api/grupos` e
      `/api/servicos` agora retornam lista vazia (200) em conexão/timeout/5xx
      do Supabase em vez de 500; 401/403/PGRST30x continuam subindo.
- [x] **Aplicar `supabase_migracao_v118.sql` (v2.0.0) — FEITO pelo dono.**
os 4 links ainda estão vazios - preencher no `/admin/grupos` (agora com botão/form "Adicionar grupo" desde v2.7.2, CRUD completo testado).
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
## LOG v2.7.2 (17/09/2026) - B?tn/form Adicionar Grupo
- GET /admin/grupos agora tem se?o `Adicionar grupo` (nome/link/ativo + ordem autom?tica) acima da tabela.
- Nova rota POST /admin/grupos/novo (perm gerenciar_grupos + CSRF + audit grupo_criar).
- Su?te Services+Seguran?a+Grupos: TODOS PASSARAM (test_services_seguranca.py, 230 linhas).
- painel.py/bot.py VERSION bump 2.7.1 -> 2.7.2; py_compile OK; commit+push (raz?o: 2).

## LOG v2.7.4 (19/09/2026) - Service form fix (pedido do dono no check-in)
- Bug: horas com v?rgula (ex.: 2,5) viravam 0 ao salvar/editar o servi?o. Causa real:
  `float("2,5")` nos POSTs novo/editar dava ValueError e o `except` zerava horas (e
  valor_hora/desconto). O HTML tipo=number pode enviar a v?rgula conforme o locale.
- Fix: helper `_sv_num(val)` em painel.py (utils do Service) — aceita "2,5", "2.5" e
  formato BR "1.500,50"; usado nos 2 POSTs p/ valor_hora, horas e desconto.
  Fluxo: 2,5 -> _sv_num -> 2.5 -> salvo numeric 2.5 -> editar mostra value=2.5 (n?o 0).
- Removida a l?gica `svRecalc` e suas chamadas dos 2 forms (novo + editar). Mantida e
  elevada `svCoinToggle` a fun??o independente (antes aninhada em svRecalc no form novo;
  no editar era svfpToggle). forma_pagamento, qtd_coins_row/campo COINS inalterados.
- VERSION painel.py 2.7.3 -> 2.7.4 (bot.py permanece 2.7.3 — sem mudan?a funcional).
- Validado: py_compile OK; _sv_num('2,5')=2.5, _sv_num('2.5')=2.5, 20x2,5-0=50.0;
  grep svRecalc = 0 ocorr?ncias; svCoinToggle presente nos 2 forms.

## LOG v2.7.6 (19/09/2026) - Service: Total Coins em COINS + horas sem ponto (pedido do dono)
- Bug 1: KPI "Total Coins" e a coluna Valor mostravam R$ (somavam o campo `valor`
  que é calculado em R$); serviços COINS exibiam "R$ 0,00". A quantidade digitada
  em `qtd_coins` já era gravada na observa??o via prefixo "QTD COINS: N |".
- Fix 1 (painel.py admin_services): KPI Total Coins agora soma o `qtd_coins`
  extra?do da observa??o (`_sv_qtd_from_obs`) e exibe "1000 Coins" (e n?o R$);
  a coluna Valor mostra "500 Coins" p/ servi?o COINS (ou "0 Coins" p/ registros
  antigos sem prefixo) e "R$ ..." p/ PIX.
- Bug 2: horas exibidas com ponto decimal (ex.: 3.0) na tabela e no form de
  edi??o (str(float)).
- Fix 2: helper `_sv_fmt_hrs()` (`:g` -> 3.0 vira 3, 2.5 continua 2.5) usado na
  tabela e no input horas do form de edi??o; KPI Horas j? usava :g.
- VERSION painel.py 2.7.5 -> 2.7.6 (bot.py 2.7.3 inalterado).
- Validado: py_compile OK; test client com mocks: KPI "1000 Coins", linha COINS
  "500 Coins", PIX "R$ 100,00", horas "3" (n?o 3.0) e "2.5" preservado.

## LOG v2.7.7 (19/09/2026) - Dashboard: remover "Ultimas a??es do admin" (duplicada)
- Pedido do dono: a se??o "Ultimas a??es do admin" no topo do dashboard principal
  duplicava a p?gina de Auditoria (/admin/audit, v2.5.0: busca, filtros, pagina??o
  e exportar CSV). Confirmado que a auditoria completa j? existe na p?gina pr?pria.
- Fix (painel.py admin_index): removidos o bloco `audit = _fetch("audit_log"...)` /
  `audit_rows` e a se??o `<h2>Ultimas a??es do admin</h2>` do dashboard. O restante
  (KPIs, gr?fico 14 dias, p?ginas mais visitadas, ultimos pedidos) inalterado.
- VERSION painel.py 2.7.6 -> 2.7.7 (bot.py 2.7.3 inalterado).
- Validado: py_compile OK; test client /admin 200 sem a se??o na p?gina e com
  "Ultimos pedidos" preservado; grep audit_rows/sess?o ausentes.

