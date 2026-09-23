# BAPZX Tibia Coins Bot â€” MemÃ³ria do projeto

- Onde paramos (11/09, v1.11.3): usuario do GitHub renomeado de lucascristianini1-netizen para bapzxdev a pedido do dono (URL do portfolio agora e https://bapzxdev.github.io/bapzx-portfolio/); PORTFOLIO_URL atualizado no bot, remotes locais dos 3 repos apontam para bapzxdev, referencias em manual.txt/docs/launchers atualizadas (o GitHub redireciona as URLs antigas). Continua tudo da auditoria v1.11.2 (Google Login + Area do Cliente validados ao vivo; XSS do /dashboard corrigido; referer exato no /admin/marcar; sessao 7d + headers de seguranca; TELEGRAM_WEBHOOK_SECRET ativo no Render - webhook so aceita com o header certo). Pendente: publish do app Google antes de clientes reais; itens/prices reais do portfolio (dono vai ajustar); Fase C/1a venda (vetada pelo dono). (dono logou no /admin; pedido de teste id 17 visto em /cliente e /admin e removido; area do cliente lista pedidos do e-mail do login). DEPOIS: auditoria completa de seguranca (a pedido do dono) - sem segredos vazados em nenhum repo; deps sem CVE (Authlib 1.8.0 ja corrige os exploits de 2026, Flask 3.1.3). 4 falhas corrigidas na v1.11.2: (1) XSS no /dashboard (campos do pedido escapados, como nas paginas novas), (2) /admin/marcar compara o host de origem exato via urlparse (antes era substring, dava pra burlar), (3) sessao permanente por 7 dias (PERMANENT_SESSION_LIFETIME 7d + session.permanent) + headers de seguranca (nosniff, DENY, same-origin), (4) webhook do Telegram protegido por TELEGRAM_WEBHOOK_SECRET (X-Telegram-Bot-Api-Secret-Token com compare_digest; setWebhook envia secret_token; sem a env, comportamento antigo). Testes verdes: test_v170 (v1.11.2), test_auth_v111 (+4 checagens novas de seguranca), test_planilha_v180. Pendente: adicionar TELEGRAM_WEBHOOK_SECRET na env do Render + restart; publish do app Google antes de clientes reais; excluir client OAuth velho (desktop); itens/prices reais do portfolio; Fase C/1a venda (vetada pelo dono).

## PROTOCOLO DE REENTRADA (atualizado no último check-out)

- **v2.10.1 (23/09, MARKTRADE — ajustes pedidos pelo dono)**: (1) **Mundo**
  virou `<select>` com os **16 mundos** (`_MK_MUNDOS` em bot.py: Auroria,
  Belaria, Bellum, Drakaria, Eldrian, Elysian, Infernum I/II/III, Lunarian,
  Malveria, Mystian, Obsidian, Solarian, Tenebrium, Vesperia) — validado no
  POST (`world not in _MK_MUNDOS` → flash "Selecione um mundo válido"). (2)
  **Campo "Tipo de PvP" removido** do form e do payload; coluna `tipo_pvp`
  da v124 segue no banco (default vazia; sem migration nova). `/api/troca`
  não devolve mais `pvp` (painel.py); vitrine `troca.html` sem dot/texto de
  pvp e cores `SERVER_COLORS` mapeadas para os 16 mundos. (3) **Imagem
  automática do Wiki Tibia**: novo `_mk_itemsprite(item_name)` (bot.py) —
  mediawiki API `prop=images` + `imageinfo iiurlwidth=96`, cache `_SPRITE_
  CACHE` (cap 800), timeout 8s, User-Agent BAPZX-MARKTRADE, nunca derruba;
  chamado no POST quando `sprite` vazio. Validado ao vivo: "War Hammer" →
  `tibiawiki.com.br/images/2/25/War_Hammer.gif`, "Guardian Axe" → OK,
  item inexistente → "". Migration **v124 APLICADA pelo dono**.
  bot.py+painel.py VERSION **2.10.1**. Testes: test_marketplace.py **37 OK**
  (novos: _MK_MUNDOS, _mk_itemsprite sucesso/cache/falha, publish com mundo
  inválido rejeita, mundo válido chega ao supabase sem tipo_pvp, sprite vazio
  busca automático e vai no payload), regressão test_coins.py **26 OK**;
  py_compile OK. Também: linha 1 do bot.py estava corrompida
  (`ja subimport base64`) → restaurada para `import base64`. **Próximo passo
  (dono): re-deploy no Render (v2.10.1 no /health) e validar ao vivo
  (publicar com mundo, sprite do Wiki Tibia no anúncio, vitrine troca.html).**
- **v2.10.0 (23/09, MARKTRADE — marketplace de anúncios)**: pedido do dono.
  bot.py (VERSION 2.10.0): rotas `/cliente/troca` (publicar anúncio: jogo,
  categoria, título, descrição, preço em GP por vidro flexível, imagens),
  `/cliente/troca/<aid>` (detail com selo VERIFICADO/SELLER# e PIX com
  prefixos), listagem com filtros; `_mk_gp` (formata GP; None/vazio → "Aceita
  ofertas"); PIX via Mercado Pago com `external_reference` `PUB-<listing>`
  (publicação+destaque num PIX só), `DES-<listing>`, `VIP-<email>` — selo VIP e
  ativação de anúncio SÓ via webhook/query real no MP, nunca ao abrir o QR.
  `_marketplace_confirm` cobre PUB/DES/VIP; branch do webhook ANTES do gate
  `reference.isdigit()`. Limpeza de construções frágeis no `cliente_troca`
  (`if False else`, walrus `vip_until`, mistura `%`-format com f-string).
  painel.py (VERSION 2.10.0): módulo ADM `/admin/marketplace` — config de
  preços/limites/durações (INSIDE o admin, entre COINS e Segurança; default
  R$ 2,99 publicação / +R$ 5,00 destaque / R$ 12,99 VIP / limite 3 anúncios /
  30 dias), lista de anúncios com status e ações
  ativar/bloquear/desbloquear/encerrar/verificar + teste VIP; coluna correta
  `limite_publicacoes` (não `limite_ativas`) no helper, form e handler POST;
  sidebar item **MARKTRADE** (Vendas, ícone "tag"), entradas de audit
  `marketplace_config`/`marketplace_acao`/`marketplace_vip`. rbac.py: perms
  `ver_marketplace` e `gerenciar_marketplace` (ADMINISTRADOR/MASTER via ALL).
  Vitrine pública no portfólio (troca.html) pronta para consumir os anúncios.
  Migration `supabase_migracao_v124.sql` criada — APLICADA pelo dono no SQL
  Editor (arquivo em `C:\DEV\Supabase\`). Validado: py_compile OK; **test_marketplace.py NOVO (30 testes OK)** (helpers, GET/POST admin com mocks,
  webhook VIP, `_marketplace_confirm` PUB/DES/VIP, render `/cliente/troca`);
  regressão test_coins.py **26 OK**. **Próximo passo (dono): re-deploy no
  Render e validar ao vivo (publicar anúncio, PIX, webhook, selo VIP,
  /admin/marketplace).**
- **v2.9.0 (22/09, redesign /cliente)**: pedido do dono — área do cliente
  (`/cliente`, `/cliente/perfil`, `/cliente/suporte`, `/cliente/suporte/<id>`)
  redesenhada como **dashboard profissional SaaS dark** (UI/UX apenas; backend/
  rotas/auth/CSRF intactos). AUTH_LAYOUT reescrito (CSS Sora + gradiente verde→
  azul, :root vars, header sticky com blur, nav do cliente com aba ativa,
  dropdown do usuário, KPIs, painéis, tabelas, badges de status, empty state,
  help-cards, alerts, fade-in, responsivo 900/640/480px); agora usa tokens
  `@@TITLE@@/@@BRAND@@/@@TOP@@/@@BODY@@/@@WHATSAPP@@` via `.replace()` na nova
  `_render_layout()` (NÃO usar `.format()` nesse template). Helpers novos:
  `_title_initials`, `_cliente_header`, `_status_badge` (pendente/pago/entregue/
  cancelado + aberto/respondido/encerrado), `_fmt_brl` (usa parse_brl; conserta
  "22,50"), `_cliente_profile`, `_cliente_tickets`. `/cliente` = boas-vindas +
  4 KPIs reais + tabela pedidos recentes (8) + card último pedido + empty state
  → PORTFOLIO_URL + ajuda + perfil; `/cliente/suporte` ganhou âncoras
  `#novo`/`#chamados`; detail ticket body trocado de `.format()` para `%`.
  VERSION bot.py **2.9.0** (painel.py segue 2.8.1, sem mudança). Validado:
  py_compile OK; test_coins.py **26 testes OK**; test client + Playwright —
  rotas 200 (com e sem pedidos), 404 detail inexistente, sem sessão 302→/login,
  valores R$ ("R$ 2.250,00"), badges, avatar iniciais, dark theme ativo e
  responsividade (nav wrap/header colapsa/KPIs 4→3→2 cols). **Pendente dono:
  deploy no Render e validar ao vivo; publish Google OAuth; aplicações de
  migrações (v122/v123) e validações pendentes seguem as mesmas.**
- **v2.8.1 (22/09, cache COINS instantâneo)**: pedido do dono — o cache de
  2 min de `coins_config` deixava o preço/status demorar para valer no bot.
  Agora o POST `/admin/coins/salvar` chama `_invalidate_coins_cache()` (gancho
  registrado por bot.py via `painel._registra_invalidador_coins`, sem import
  circular; bot.py `_coins_invalidate()` zera `_COINS_CACHE`) → mudança vale na
  HORA (mesmo processo). TTL reduzido de 120s para **30s** (`_COINS_TTL`).
  VERSION bot.py + painel.py **2.8.1**. Validado: py_compile + test_coins.py
  **26 testes OK** (3 novos: ttl=30, invalidação zera cache, gancho ativo).
  dono — controlar o estoque/preço de Tibia Coins manualmente no dashboard, com
  histórico e permissões admin-only. **supabase_migracao_v123.sql** (PENDENTE do
  dono no Supabase SQL Editor — ARQUIVO EM `C:\DEV\Supabase\`: foi corrigido em
  22/09 por erro 428C8/428C9 `cannot insert non-DEFAULT into id`: identity
  agora é `generated BY DEFAULT as identity` nas duas tabelas + bloco `do $$`
  que converte identity ALWAYS já criado; exige upsert id=1 do painel e o seed.
  Colar o arquivo ATUALIZADO e rodar de novo): `coins_config` (linha única id=1 — estoque
  numeric(14,2) default 100000, preco_mil numeric(12,2) default 90, min_compra
  default 100, max_compra default 50000, status 'ativo'|'pausado', observacao,
  atualizado_em, atualizado_por, criado_em) + `coins_historico` (admin,
  qtd_anterior/qtd_nova, preco_anterior/preco_novo, alteracao, criado_em) +
  índices + seed `insert on conflict (id) do nothing`. **rbac.py**: novas
  permissões `ver_coins` e `gerenciar_coins` (labels + PERM_TRACK "coins");
  ADMINISTRADOR=ALL e MASTER cobrem automaticamente. **painel.py** (VERSION
  2.8.0): item **COINS** na sidebar (grupo Vendas, ícone dollar, gated
  `ver_coins`); GET `/admin/coins` — 4 cards (COINS disponíveis, Preço/1.000,
  Status ATIVO/PAUSADO, Última atualização + por), aviso de migração pendente,
  form de edição (se `gerenciar_coins`: estoque, preço/1.000, mínimo, máximo,
  status, observação), calculadora JS `qtd*preco_mil/1000`, tabela de histórico
  (até 100 registros); POST `/admin/coins/salvar` — CSRF, validações
  (estoque ≥0, preco_mil>0, min/max ≥0, min≤max, status ativo|pausado), grava
  `coins_historico` SÓ quando há mudança (diff), upsert `id=1` com `Prefer:
  resolution=merge-duplicates`, auditoria `coins_salvar`. Helpers `_coins_num`
  (parser BR: vírgula → ponto; sem vírgula, ponto único com ≤2 decimais =
  decimal, senão milhar), `_coins_int`, `_coins_dec`, `_coins_linha`,
  `_coins_brl`. **bot.py** (VERSION 2.8.0): preço agora É DINÂMICO —
  `_coins_config()` (cache 120s, fail-soft → legado) alimenta `calc_price`
  (`preco_mil` com fallback PRICES/90), `price_table_text`,
  `price_table_compact`, proporção no prompt da IA (`ask_ai`) e `persona.txt`
  (`_persona_precos()` reescreve os 2 blocos fixos em `load_persona`; busca por
  strings legadas, sem match = no-op). `_coins_check(tc)` barra a venda quando
  status='pausado' ou tc fora de [min,max] — chamado no webhook logo após
  `build_order` (antes de pedir char, fluxo AWAITING_CHAR); fail-open sem tabela.
  `_fmt_coin_brl`. Preço continua congelado no pedido na criação (calc_price →
  save_order). **Mojibake do nome do dono corrigido**: profiles agora `Lucas
  "bapstyl3x" Cristianini Marca` (aspas ASCII, PATCH 204). Validado: py_compile
  OK; **test_coins.py NOVO (23 testes, TODOS OK)** — painel (GET/POST,
  permissões, CSRF, helpers de parse), bot (calc_price legado/dinâmico,
  `_coins_check` pausado/limites, tabelas dinâmicas, persona dinâmica);
  regressão test_qtd_coins (Playwright e2e) intacto. Pendente dono: (1) **aplicar
  `supabase_migracao_v123.sql`** no SQL Editor; (2) **re-deploy no Render**
  (v2.8.0 no /health); (3) validar ao vivo /admin/coins (pausado barra venda no
  bot, limites, histórico, preço novo refletindo na tabela de preços). Commit +
  push OK (bapzx e docs raiz).
- **v2.7.12 (22/09, autocomplete Service)**: pedido do dono — no dashboard
  **Service**, os campos **Nome do cliente** e **WhatsApp do cliente** agora têm
  **autocomplete**: ao digitar (ex.: "Dout") aparecem os clientes já cadastrados
  e, ao escolher um nome com whatsapp conhecido, o WhatsApp é preenchido sozinho
  (e o inverso). Helpers `_sv_sugestoes()` (junta `servicos_manuais` + `profiles`;
  devolve nomes, whats e pares nome↔whatsapp) e `_sv_autocomplete_html()` (2
  datalists `sv_nomes`/`sv_whats` + JS `svPair`, só preenche o parceiro se vazio,
  `hasOwnProperty` contra `__proto__`). Inputs novo e editar de serviço com
  `list` + ids `sv_nome_input`/`sv_wpp_input`. VERSION painel.py **2.7.12** (bot.py
  segue 2.7.3). Validado: py_compile OK + test client real — `/admin/services` e
  `/admin/services/<sid>` 200 com datalists + SV_PAIRS; sugestões reais:
  "Doutor Odeioretro", "Milena Soares", "wak", +55 15 99814-7564... Observação:
  nome "Lucas �bapstyl3x� Cristianini" -> MOJIBAKE CORRIGIDO na v2.8.0: profiles agora com "Lucas \"bapstyl3x\" Cristianini Marca" (aspas ASCII, PATCH 204). Commit + push OK.
- **v2.7.4 (19/09, Service form fix)**: corrigido bug em que **horas digitadas com vírgula ("2,5") viravam 0** ao salvar/editar. Causa: `float()` nos POSTs `/admin/services/novo` e `/admin/services/<sid>` quebrava com `ValueError` ao receber vírgula e o `except` zerava `horas` (e `valor_hora`/`desconto`). Criado helper **`_sv_num`** — aceita "2,5", "2.5" e formato BR "1.500,50" — aplicado aos 3 campos nos 2 POSTs. Removida a lógica **`svRecalc`** e todas as suas chamadas dos 2 forms; **`svCoinToggle`** foi mantida e elevada a função independente (no form novo estava aninhada DENTRO de `svRecalc`; no editar estava como `svfpToggle`). `forma_pagamento`, `qtd_coins_row`/campo Quantidade de COINS preservados (HTML não alterado). `sv_total` (valor cobrado persistido) continua exibido no editar, só não é mais recalculado ao vivo. **v2.7.6 (19/09, mesmo dia, +2 pedidos do dono)**: (1) KPI "Total Coins" e coluna Valor mostravam R$ (somavam `valor`, calculado em R$), mas devem mostrar COINS — agora somam a qtd extraída da observação (`_sv_qtd_from_obs`, prefixo `QTD COINS: N |`) e exibem "1000 Coins" e "500 Coins" por linha; registros COINS antigos sem prefixo mostram "0 Coins"; (2) horas saíam com ponto (3.0) — helper `_sv_fmt_hrs()` (`:g` → 3) na tabela e no input do form. VERSION painel.py **2.7.6** (bot.py segue 2.7.3). Validado: py_compile OK; test client c/mocks (KPI 1000 Coins, linha 500 Coins, PIX R$ 100,00, horas "3" e "2.5"). **Falta**: deploy no Render (o /health é do bot.py, que segue 2.7.3) e validar ao vivo digitar 2,5 no form de Service. **v2.7.7 (19/09, mesmo dia)**: removida a seção "Últimas ações do admin" do dashboard principal — ela duplicava a página Auditoria `/admin/audit` (busca, filtros, paginação, CSV, v2.5.0). Removidos o `_fetch("audit_log"...)`/`audit_rows` do `admin_index` e o bloco HTML; KPIs/gráfico/páginas visitadas/últimos pedidos intactos. VERSION painel.py **2.7.7**. Validado: py_compile OK; /admin 200 sem a seção, "Últimos pedidos" presente.
- Onde paramos (17/09, v2.7.1): **área Service com cálculo automático do valor cobrado** (`valor = valor_hora × horas − desconto`, pré-cálculo ao vivo por JS, campo Desconto novo) e **bug do "valor absurdo" corrigido** (`_parse_brl` tratava string decimal do Supabase `"150.00"` como milhar → 15000; agora número sem vírgula é float direto, só formato BR `1.500,50` usa vírgula como decimal, linhas 518-529). **DEPLOY CONFIRMADO**: /health "bot ok v2.7.1". **MIGRATION v122 APLICADA pelo dono (17/09)** verificada no Supabase (colunas valor_hora/desconto presentes; registro id 1 com valor_hora 20). v121 também aplicada (Service testado). Resta só validação fina ao vivo (caso 1,5h e desconto). (cargos MASTER 100..CLIENTE 10, permissões padrão por cargo, permissões individuais jsonb substituindo padrão quando não-vazias, MASTER só via MASTER_EMAILS env com fallback ADMIN_EMAILS — .env não tem MASTER_EMAILS). **supabase_migracao_v118.sql** cria `users` (email pk, nome, cargo, permissoes, ativo) e `grupos` (Coroa/Rubinot/Pokepixel/PokeIdle, ordenados, links vazios) + seed item "Intermediação BAPZX" R$5. **painel.py v2.0.0**: `_require_perm`/`_require_any_perm` substituíram `_require_admin` em 18 rotas (mapeamento por permissão), rotas novas /admin/usuarios (listar/criar/editar c/ permissões), /admin/audit, /admin/grupos (CRUD) e /api/grupos (público, só ativos com link); sidebar `_page()` filtrada por permissão (novos itens Grupos/Usuários/Auditoria no grupo SISTEMA), sino/KPIs/botões condicionais, badge de cargo no chip do usuário. **bot.py v2.0.0**: OAuth resolve cargo/perms da tabela users (MASTER env → users ativo → CLIENTE), session armazena cargo/perms, /acesso usa cargo, AUTH_LAYOUT com footer legal+WhatsApp, avisos LGPD em /cliente/perfil e /cliente/suporte. **legais.py** novo: /privacidade /termos /reembolso (LGPD, 11 seções) + /privacidade/pdf (reportlab). **Portfólio v3.3**: seção "Nossos Grupos" no index + links legais/WhatsApp no footer das 7 páginas. Intermediação R$5 via /api/itens (seed).
- Migration v118: **APLICADA pelo dono** (tabelas users/grupos no ar; /api/grupos vazio porque links ainda vazios).
- Testes: RBAC suite (MASTER 20 perms, ADMIN 18 default, custom substitui default, tem_perm, cargo_valido) verdes; painel rotas MASTER 200 / CLIENTE 302→/login bloqueado; /privacidade/termos/reembolso/PDF 200; pentest 35/35; headers 6/6; py_compile OK.
- **v2.0.1 (15/09)**: corrigido `_page("Entrar", "Escolha a área", ...)` — o parâmetro `brand` do `_page` é escapado com `html.escape`, então `&aacute;` virava `&amp;aacute;` literal. Script `fix_entities.py` substituiu TODAS as entidades HTML (`&aacute;`/`&ccedil;`/`&atilde;`/`&middot;`/`&copy;` etc.) por caracteres reais em `bot.py`/`painel.py`/`legais.py`. Removidos todos os `target="_blank"` do portfólio (7 páginas) e de `bot.py` (2)/`painel.py` (3) — padrão agora é abrir na mesma aba. Commits: bot `db0f135`, portfólio `a027139`.
- **v2.0.2 (15/09)**: pentest OWASP ZAP (spider + passive + active + script manual `pentest_v202.py`). Bot passou **35/35 checagens** (RBAC bypass, CSRF, XSS, info disclosure, rotas legais, APIs, error handlers). Achados de header corrigidos em `security_headers` (`bot.py:~727`): **HSTS** (`Strict-Transport-Security: max-age=31536000`, só sob HTTPS via `x-forwarded-proto`) e **CSP** (`default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`). Confirmado em produção 6/6 headers em 7 rotas. Commit bot `886eac8`. Alertas ZAP remanescentes (CORS `*`, anti-clickjacking/CSP aparente, SRI) são do PORTFÓLIO no GitHub Pages — o ZAP segue o 302 da `/`; o scan direto de `/privacidade` (v2.0.2) NÃO gerou alerta. `Application Error Disclosure` era o 500 transitório de `/robots.txt` no cold start do Render (agora 404 limpo).
- **v2.1.0 (15/09, separação serviços × itens)**: a pedido do dono, Intermediação (serviço) não podia ficar junto dos itens do jogo. `supabase_migracao_v119.sql` cria tabela `servicos` espelhando `itens` e move a Intermediação R$5 de `itens` para `servicos` (bucket `servicos` público). Novo endpoint `/api/servicos` no painel.py (espelho de `/api/itens`). Portfólio `itens.html` tem 2 seções: "Itens do jogo ⚒️" (`/api/itens`) e "Serviços 🛡️" (`/api/servicos`), CTA "Quero contratar" nos serviços. VERSION 2.1.0. Migration v119 **APLICADA pelo dono**, validado em produção: `/api/servicos` → Intermediação, `/api/itens` → vazio. Deploys: bot `97c9d3c` → Render, portfólio v3.5 `f171800` → GitHub Pages.
- **v2.1.2 (16/09)**: página "Escolha a área" (/acesso) consistente com o início do site: título "BAPZX · {title}", link "Voltar ao site" (PORTFOLIO_URL) no topo e marca BAPZX com Sora + gradiente verde→azul em toda a área do cliente (AUTH_LAYOUT). Deploy `7887fc5` → Render.
- **v2.2.0 + portfólio v3.7 (16/09, grupos completos)**: 1) Excluir grupo em /admin/grupos (POST `/admin/grupos/<gid>/excluir`, CSRF, botão vermelho com confirm JS); 2) alinhar texto na página de Grupos (cards com tag "💬 WhatsApp", nome centralizado, botão uniforme, `justify-content:space-between;height:100%` em grupos.html e index.html); 3) reordenar ao mudar a ordem — botões ↑/↓ (POST `/admin/grupos/<gid>/mover`, direcao cima|baixo) reescrevem `ordem`=1..n (dashboard e /api/grupos já ordenam por `ordem.asc`). Deploys: bot `03908f9` → Render (v2.2.0 no /health, API grupos ordem 1/2/3), portfólio `a01ece1` → GitHub Pages v3.7.
- **v2.3.0 (16/09, cupons no dashboard — item 10)**: `supabase_migracao_v120.sql` (PENDENTE do dono no SQL Editor) cria `cupons` — codigo unique, tipo `percentual|fixo`, valor numeric, validade date, limite_usos (0=ilimitado), usos (contador), produto_id (itens), servico_id (servicos), grupo_id (grupos), ativo + índices. `rbac.py`: `ver_cupons`/`gerenciar_cupons` (padrão ADMIN + MANAGER). `painel.py`: item "Cupons" na sidebar (Vendas, ícone ticket); rotas GET /admin/cupons (lista + form novo), POST /admin/cupons/novo, GET/POST /admin/cupons/<id> (editar), POST /admin/cupons/<id>/ativar (toggle), POST /admin/cupons/<id>/excluir; validação (codigo MAIÚSCULAS obrigatório, valor > 0, % limitada a 100, validade ≤ 10 chars, limite ≥ 0) e "Já existe um cupom com o código X" em conflito unique; auditoria em tudo. VERSION 2.3.0. Validado: py_compile + test client (lista 200, novo 302 payload normalizado, duplicado 400, editar 302 fixo 15.50, toggle 302, excluir 302, CSRF 403, valor 0 400). Deploy bot `e303372` → Render (/health "bot ok v2.3.0").
- **v2.4.0 (16/09, Configurações no dashboard — item 11)**: aba Configurações de /admin/config reescrita em 4 abas via `?aba=site|conta|pagamentos|notificacoes`, usando a tabela `config` (chave/valor) JÁ EXISTENTE da v116 — sem migration nova. Chaves novas: site_nome, site_logo, site_banner, site_slogan, site_texto_topo, site_texto_rodape, link_portfolio, link_whatsapp, link_telegram, link_instagram, link_youtube, link_discord, link_tiktok, pix_chave, pix_beneficiario, notificar_pix, notificar_erro (além de precos e notificar_pedido). painel.py: helpers `_CONFIG_CAMPOS` (texto|url|texto_livre|bool + limites), `_CONFIG_SECOES`, `_CONFIG_PUBLICAS`, `_config_field`, `_config_textarea`, `_config_bool`, `_config_tabs`, `_config_grupo_html`; `admin_config_salvar` valida por seção (URL http(s), bool 1/0) e grava **só campos presentes no form** (frame Site tem 3 forms; sem isso salvar um grupo apagava os outros); rotas novas POST /admin/config/conta (altera nome do usuário logado: PATCH users?email=eq. + session["name"] + auditoria config_conta_nome) e GET /api/site púbico (rate-limit + CORS, devolve brand + só _CONFIG_PUBLICAS — nunca token/segredo); secao=precos antigo mantido (redireciona ?aba=pagamentos). Aba Conta: e-mail read-only, senha/2FA são da conta Google (card informativo). Aba Pagamentos: pix_chave (fallback env PIX_KEY quando vazia) + beneficiário; Gateway MP read-only (status pela presença da env MP_ACCESS_TOKEN no Render). bot.py: `_config_map()` cache 120 s (falha → {}, sem derrubar), `payment_text` usa `pix_chave = _config_map().get("pix_chave") or PIX_KEY`, `notify_owner` gate `notificar_pedido != "0"`, `notify_owner_pix` gate `notificar_pix != "0"`, `_error500` só avisa dono se `notificar_erro != "0"`. VERSION 2.4.0. Validado: py_compile + test_config.py (4 abas 200, salvar site/notificações/precos 302, URL inválida 400, conta 302 com params email=eq., CSRF 403, /api/site 200 sem chaves privadas, sem permissão 302/403) + test_bot_config.py (gates OFF/ON, override/fallback pix no payment_text, _config_map falha → {}) — TODOS PASSARAM. Deploy `07a8467` → Render: /health "bot ok v2.4.0"; /api/site {"ok":true,"site":{campos públicos vazios}}; /admin/config sem login 302→/login.
- **v2.5.0 (16/09, Auditoria completa — item 14 antecipado)**: o dono pediu execução do item 14 do roadmap ("Logs / Auditoria: saber quem fez o quê e quando"). Auditoria de admin já existia (21 rotas POST desde v2.0.0), mas o bot NÃO logava nada e a página /admin/audit era tabela crua sem filtro. **bot.py**: função `audit_log(acao, detalhes="")` após o STORE init (POST `{STORE.url}/rest/v1/audit_log` com `STORE._headers()`, `email="sistema@bapzx"`, `ip="sistema"`, `detalhes[:500]`, fire-and-forget try/except com print `[audit] falhou`) + hooks: `pedido_criado` (fim de `_finalizar_confirmacao_char`; detalhes `pedido {id} | {tc} RC | {preco} | {mundo}`), `pix_gerado` (em `notify_owner_pix`, loga SEMPRE mesmo com toggle off — trilha financeira), `pedido_pago`/`pedido_entregue` (em `apply_status`, cobre /pago, /entregue E webhook MP), `feedback_recebido`. **painel.py**: `/admin/audit` reescrito — `_ACOES_AUDIT` (26 ações → label + cores de badge), busca `q` (`or=(acao.ilike.*q*,detalhes.ilike.*q*)`), dropdown `ata`, filtro `quem` (`email=ilike.*p*`), paginação 50/pág via `Range` + `Prefer: count=exact` (total), **Exportar CSV** (até 2000 filtrados, `;` com aspas via flask.Response), `_fetch_soft` (PGRST205 → vazio). Imports novos: `urllib.parse.quote`, `flask.Response`. VERSION 2.5.0. Validado: py_compile + test_audit.py (base 200 + badges traduzidos, ata/q/quem/p=2, CSV attachment, sem permissão 302) + test_audit_bot.py (payload, truncamento 500, falha silenciosa) + regressão test_config/test_bot_config — TODOS PASSARAM. Deploy `97565a2` → Render (/health "bot ok v2.5.0"; /admin/audit sem login → 302 /login).
- **v2.6.0 (16/09, item 13 Administradores + item 9 Notificações)**: o dono pediu o modelo de cargos (Administrador = acesso total; Moderador = clientes + pedidos; Atendente = serviços + clientes; Financeiro = pagamentos + relatórios) e o centro de notificações do dashboard. **rbac.py** reescrito: CARGOS MASTER 100 / ADMINISTRADOR 80 / MODERADOR 60 / ATENDENTE 50 / FINANCEIRO 40 / CLIENTE 10 (removidos ADMIN/MANAGER/OPERADOR/SUPORTE), `CARGOS_LABEL` + `CARGOS_DESC`, ADMINISTRADOR = ALL (bypass, sempre total, ignora perms individuais restritivas), MODERADOR pedidos+clientes+tickets, ATENDENTE itens(serviços)+clientes+tickets, FINANCEIRO dashboard+pedidos+pagamentos. `LEGADO` + `normalizar()` mapeiam cargos antigos (ADMIN→ADMINISTRADOR, MANAGER→MODERADOR, OPERADOR/SUPORTE→ATENDENTE) em todas as funções — usuários antigos não perdem acesso. **painel.py**: `/admin/notificacoes` (item 9) — sino com feed de categorias por permissão (novas vendas 24h, serviços 7d = pedidos sem `tc`, pedidos pendentes, pagamentos confirmados 24h, novos clientes 7d pelo 1º pedido, erros de pagamento 7d do `audit_log`) + Alertas administrativos (config vazia, tabela cupons ausente); helpers `_notificacoes()` (cache 20s), `_count_servicos_recentes`, `_count_novos_clientes`; página `/admin/notificacoes` com cards + badge somando; item "Notificações" na sidebar (Principal); `erro_pagamento` no `_ACOES_AUDIT`; descrições de cargo (`_cargos_desc_html`) nas telas de usuários. **bot.py**: `audit_log("erro_pagamento", ...)` na falha de geração de Pix (`_finalizar_confirmacao_char`) e no `/webhook/mp` com pagamento não-aprovado. VERSION 2.6.0. Validado: py_compile; `test_rbac_painel` (novo modelo + rotas), `test_notificacoes` (contadores, permissões FINANCEIRO/ATENDENTE, página 200, CLIENTE bloqueado), regressão `test_config`/`test_audit`/`test_audit_bot`/`test_bot_config`/`test_cupons`/`test_v200` — TODOS PASSARAM.
- **Migration v120 (cupons) APLICADA pelo dono** (16/09): `/admin/cupons` já opera com a tabela real.
- **v2.7.1 (17/09, Service com cálculo automático)**: dono testou Service e pediu que o valor cobrado seja **valor/hora × horas** (ex.: 1h → R$ 20, 1,5h → R$ 30) com campo de **Desconto (R$)**; ao investigar "valor absurdo" descobri bug: **`_parse_brl` corrompia valores do Supabase** ("150.00" → 15000.0) — removia todos os pontos antes de parsear; corrigido (linhas 518-529). **painel.py** (VERSION 2.7.1): forms novo/editar de serviço agora têm **Valor por hora (R$)** (padrão 20), **Horas** e **Desconto (R$)** com **pré-cálculo ao vivo via JS** (`sv_total`); POST novo/editar calcula `valor = max(0, valor_hora*horas - desconto)` e persiste `valor_hora` e `desconto`. **bot.py** (VERSION 2.7.1). **supabase_migracao_v122.sql** (PENDENTE do dono): colunas `valor_hora` e `desconto` em `servicos_manuais` + backfill.
- **v2.7.0 (16/09, área Service + área Segurança)**: o dono pediu "Service" (agenda de serviços manuais: data/hora/serviço/nome/WhatsApp/valor/forma/horas/observação, com totais no topo) e "Segurança" (histórico de login/IP/dispositivo, sessões ativas e botão de encerrar). **rbac.py**: permissões novas `ver_servicos_manuais`, `gerenciar_servicos_manuais`, `ver_seguranca`, `gerenciar_seguranca` (labels + PERM_TRACK). **painel.py** (VERSION 2.7.0, linha 17): `_sessao_ativa(sid)` com `_SID_CACHE` (cache 60s) chamado por `_require_perm`/`_require_any_perm` — sessão encerrada dispara `session.clear()` e bloqueia rotas; sidebar ganhou **Service** (Principal, ícone dollar) e **Segurança** (Sistema, ícone lock); rotas novas: GET `/admin/services` (KPIs Serviços/Concluídos/Total Pix/Total Coins/Horas + tabela com Editar/Concluir-Reabrir/Excluir + form novo serviço), POST `/admin/services/novo`, GET+POST `/admin/services/<sid>`, POST `/admin/services/<sid>/toggle`, POST `/admin/services/<sid>/excluir`, GET `/admin/seguranca` (KPIs Sessões ativas/Logins hoje/Logins 30d + tabela de sessões com IP/dispositivo/último acesso + dica dos links Google de segurança + Encerrar), POST `/admin/seguranca/sessoes/<sid>/encerrar`; auditoria em todas as ações (`servico_criar`, `servico_editar`, `servico_concluir`, `servico_reabrir`, `servico_excluir`, `sessao_encerrar`); campo **WhatsApp** adicionado ao form de edição de cliente (`/admin/clientes/<email>`). **bot.py** (VERSION 2.7.0): `_client_ip_bot()`, `_registrar_sessao(email)` (POST em `sessoes` com sid/email/ip/user_agent) chamado no `oauth_callback` (gera `session["sid"]`), e `_encerrar_sessao(sid)` no `logout`; `audit_log("login"/"logout")` p/ não-CLIENTE. **supabase_migracao_v121.sql** (PENDENTE do dono no SQL Editor): tabela `servicos_manuais` (data, hora, servico, nome_cliente, whatsapp, valor numeric(12,2), forma_pagamento pix|coins, horas, observacao, status pendente|concluido + índices) + tabela `sessoes` (sid, email, ip, user_agent, criado_em, ultimo_acesso, encerrado_em, ativo + índices) + `alter table profiles add column whatsapp`. VERSION 2.7.0. Validado: py_compile OK; `test_services_seguranca.py` (Service 200 com KPIs/tabela, CRUD novo/toggle/excluir/editar 302, sem login 302; Segurança 200 com sessões/Google, encerrar 302 com PATCH, sem login 302), `test_bot_sessoes.py` (registrar POST sessoes, encerrar PATCH ativo=False, sem sid sem chamada), regressão `test_rbac_painel`, `test_notificacoes`, `test_config`, `test_cupons`, `test_v200`, `test_audit`, `test_audit_bot`, `test_bot_config` — TODOS PASSARAM.
- Próximo passo (ações do dono): (1) **aplicar `supabase_migracao_v122.sql` no SQL Editor** (colunas `valor_hora`/`desconto` em servicos_manuais + backfill — sem isso o cálculo automático roda mas não persiste); (2) **deploy da v2.7.1** no Render e conferir `/health` "bot ok v2.7.1"; (3) testar `/admin/services` ao vivo com o novo cálculo (valor/hora 20 → 1,5h = R$ 30, com desconto subtraindo) e Conferir que KPIs/totais não estouram mais; (4) testar `/admin/seguranca` (encerrar própria sessão desloga); (5) criar o cupom de exemplo `BAPZVESPERIA` (10%, grupo Belaria-Vesperia); (6) preencher `/admin/config` (Site/Pagamentos/Notificações) + conferir `/api/site`; (7) `/admin/grupos`, `/admin/audit`, `/admin/usuarios`, `/admin/notificacoes`: validação ao vivo pendente; (8) opcional: env `MASTER_EMAILS` no Render. Depois (roadmap itens 8/9): portfólio consumir /api/site. Pendências antigas seguem: limpar pedidos de teste, fluxo do bot no celular, publish Google OAuth, Fase C vetada.
- Arquivos tocados (v2.7.4): painel.py. Anteriores (v2.7.1): painel.py, bot.py, supabase_migracao_v122.sql.
- Bloqueios: nenhum. **v122 (valor_hora/desconto do Service) APLICADA (17/09)**; v121 aplicada (17/09).
- Dias restantes: a pedido do dono (16/09) o prazo do bloco foi **estendido por +2 meses** — nova meta 16/11/2026 (o bloco original de 15 dias terminava em 24/09).

Atendente IA de venda de Tibia Coins via Telegram (Flask webhook + Google Gemini).
Versão atual do bot: 2.10.0.

## Leitura obrigatÃ³ria antes de alterar (memÃ³rias do projeto)

- `MEMORIA.md` (este arquivo) â€” decisÃµes e histÃ³rico.
- `MEMORIA_COMPRA.md` â€” regra de cÃ¡lculo de preÃ§o (1.000 TC = R$ 90).
- `MEMORIA_SEGURANCA.md` â€” regra de seguranÃ§a absoluta: confidencialidade
  de cÃ³digo, dados e mÃ©tricas; leitura obrigatÃ³ria em toda sessÃ£o.
- `MEMORIA_PENDENCIAS.md` â€” pendÃªncias e observaÃ§Ãµes (publish do Google app, itens do portfÃ³lio, Fase C, etc).

## Estrutura

- `bot.py` â€” webhook Flask: `/` (landing page pÃºblica de vendas), `/health` (ok + versÃ£o), `/webhook` (mensagens), `/webhook/mp` (notificaÃ§Ãµes do Mercado Pago), `/pedidos` e `/dashboard` (protegidos por chave), comandos `/id`. Landing gerada por `landing_page()` (preÃ§os, como comprar, botÃ£o + QR para t.me/bapzx_bot).
- `storage.py` â€” `OrderStore`: salva/lista pedidos em Supabase (persistente) com fallback em `pedidos.json`.
- `persona.txt` â€” persona da loja e regras de atendimento.
- `pedidos.json` â€” pedidos salvos (runtime, fora do git, usado como fallback).
- `scripts/criar_tabela_supabase.sql` â€” DDL da tabela `public.pedidos` para o Supabase.
- `requirements.txt` â€” flask, requests, google-genai.
- `.env` — segredos (fora do git).
- `MEMORIA_EXPLICACAO.md` — passo a passo (com capturas de tela) de como configurar o Render (supabase_migracao_v115.sql, variáveis de ambiente, deploy). Referência aprovada pelo dono.

## VariÃ¡veis de ambiente

- `TELEGRAM_BOT_TOKEN` (obrigatÃ³rio, no `.env` local e no Render).
- `TELEGRAM_OWNER_CHAT_ID` = `1695600926` (aviso de novo pedido).
- `GOOGLE_API_KEY` â€” fallback lido de `gemini-cli/.env`; no Render deve estar configurada.
- `SUPABASE_URL` e `SUPABASE_KEY` â€” persistÃªncia em nuvem (opcional). Sem elas o bot grava sÃ³ no arquivo local.
- `MP_ACCESS_TOKEN` â€” Access Token de produÃ§Ã£o do Mercado Pago (comeÃ§a com `APP_USR-`). Sem ele o bot volta ao modo manual (texto com PIX_KEY + /pago).
- `RENDER_URL` â€” URL do deploy (padrÃ£o `bapzx-bot-tibia.onrender.com`), usada como notification_url das cobranÃ§as: `<RENDER_URL>/webhook/mp`.
- `PIX_KEY` â€” chave Pix estÃ¡tica, usada sÃ³ como fallback quando o Mercado Pago nÃ£o estÃ¡ configurado.
- `DASHBOARD_KEY` â€” chave de acesso do `/dashboard` e `/pedidos` (query `?key=` ou header `X-Dashboard-Key`). Sem ela as rotas ficam bloqueadas (fail-closed). Valor gerado fica sÃ³ no `.env` local e no Render â€” nunca em cÃ³digo/docs/repo (ver MEMORIA_SEGURANCA.md).
- `SHEET_WEBAPP_URL` e `SHEET_TOKEN` â€” alimentaÃ§Ã£o automÃ¡tica da planilha de clientes (Google Sheets via Apps Script Web App). URL do deploy + token compartilhado botâ†”script. Sem eles o bot pula o envio sem quebrar.

## DecisÃµes

- Pedido detectado por palavras-chave em conversa privada; salvo de forma estruturada (TC, preÃ§o da tabela, pagamento, mundo, char) e dono notificado (mensagem "ðŸ›’ NOVO PEDIDO").
- PreÃ§os fixos na persona (100 a 2500 TC). Pagamento: Pix. Entrega: Trade in-game (pedir mundo e char).
- Fallback de modelo IA: gemini-3.6-flash â†’ gemini-3-flash-preview â†’ gemini-3.5-flash.
- PersistÃªncia: `OrderStore` usa Supabase (REST) como fonte de verdade quando `SUPABASE_URL`/`SUPABASE_KEY` estÃ£o setadas; falha/ausÃªncia cai para `pedidos.json` (local). Contagem (`/pedidos`) vem do Supabase via `Prefer: count=exact`, com fallback no arquivo.
- Tarifa do Mercado Pago no Pix: ABSORVIDA pela loja por enquanto (decisÃ£o de 11/09) â€” o cliente paga exatamente o valor da tabela, sem acrÃ©scimo. Reavaliar quando a 1Âª venda real aparecer no /dashboard (ver PendÃªncias).
- SeguranÃ§a do painel: `/dashboard` e `/pedidos` exigem `DASHBOARD_KEY`; sem chave configurada as rotas negam acesso. Landing `/` Ã© pÃºblica (sÃ³ conteÃºdo comercial, sem dados).
- Defesa contra spam: rate limit por chat (mÃ¡x. ~5 mensagens em 12s) com resposta Ãºnica; protege custo da IA e fluxos.
- ExtraÃ§Ã£o do char usa stop-words (mundo, pagamento, pix, etc.) para nÃ£o engolir palavras seguintes.
- Pedido de e-mail do Pix expira em 30 min se o cliente nÃ£o responder (limpeza do estado em memÃ³ria).
- Fase C (divulgaÃ§Ã£o) VETADA pelo dono atÃ© tudo ficar ajustado. Controle de clientes serÃ¡ via Google Sheets online (modelo em planilha-clientes/: TEMPLATE_CLIENTES_v2.csv recomendado + COMO_USAR_GOOGLE_SHEETS.txt; dono jÃ¡ importou/criou a planilha, ID 1CAjZTzAPkkhDXfIJrjUDg6aUVYxk6wW5HjuZpN0wRfU, agora RESTRITA c/ automaÃ§Ã£o por token). Plano B documentado em planilha-clientes/PLANO_B.txt (operaÃ§Ã£o manual nÃ£o para: fallback Supabaseâ†’pedidos.json jÃ¡ no cÃ³digo; MP falhaâ†’Pix manual via /pago; Render/Gemini/Telegram falhaâ†’atendimento manual + planilha como registro).
- REBRAND (11/09): a empresa Ã© BAPZX (main); este bot Ã© a Ã¡rea de vendas online da BAPZX; a loja de Tibia Coins vira RUBINI COINS (internamente opÃ§Ã£o "BAPZX RUBINOT"). Novo ServiÃ§o BAPZX: R$20 por hora, solicitaÃ§Ã£o pelo WhatsApp (19) 99181-3598 (comando /servico). Entrega padronizada: trade in-game em atÃ© 10 minutos apÃ³s a confirmaÃ§Ã£o do pagamento. Confirmar com o dono o nÃºmero do WhatsApp e se o serviÃ§o Ã© R$20/h (R$ ou dÃ³lar).

## Testes feitos (09/09/2026)

- Local: pedido de teste `quero comprar 500 tc` registrado (2 pedidos) e notificaÃ§Ã£o enviada.
- Render: health `200 - bot ok`; webhook respondeu `200` a `quero comprar 250 tc`; `/pedidos` == 1 (filesystem do deploy Ã© separado do local).
- Webhook aponta para `https://bapzx-bot-tibia.onrender.com/webhook`.

## Testes feitos (10/09/2026)

- v1.2.0 (estrutura + persistÃªncia): `quero comprar 1000 tc, pagamento pix, mundo pacera, char Nap Lord` â†’ extrato `tc=1000, preco=R$90, pag=Pix, mundo=pacera, char=nap lord`; `quero comprar 250 tc` â†’ `tc=250, preco=R$22,50`. Health exibe `bot ok v1.2.0`. Contagem `/pedidos` == 3.
- v1.2.1 (fix de configuraÃ§Ã£o): `SUPABASE_URL`/`SUPABASE_KEY` passados via `load_env_key` (antes sÃ³ `os.environ`, entÃ£o o Supabase nunca ativava no .env local). Pedido `quero comprar 500 tc, mundo pacera, char Nap Lord` gravado no Supabase com `tc=500, preco=R$45, mundo=pacera, char=nap lord`; `/pedidos` passou a contar do Supabase (2). Feito tambÃ©m o teste POST/GET/DELETE direto na REST API.
- v1.2.1 no Render: apÃ³s configurar as 5 Environment Variables no serviÃ§o, pedido via webhook do Render (`quero comprar 250 tc, mundo ferobra`) gravado no Supabase (id=3, tc=250, mundo=ferobra) â€” persistÃªncia em nuvem confirmada no deploy.
- **Teste real end-to-end (10/09)**: mensagem enviada de dentro do Telegram (`quero comprar 500 tc, mundo pacera, char Teste Real`) â†’ webhook â†’ gravado no Supabase id=5 com `tc=500, preco=R$45, mundo=pacera, char=teste real`, chat 1695600926 (Lucas). `/id` respondeu pelo webhook. Durante o teste, `GOOGLE_API_KEY` estava incorreta no Render (erro 400 API_KEY_INVALID); corrigida para a chave correta do `gemini-cli/.env` (formato `AQ.` â€” validada, 50 modelos acessÃ­veis). Parser validado com 5 mensagens de amostra.
- v1.3.0 (comandos + IA reforÃ§ada): testados local `/start`, `/preco`, `/quemsomos`, `/vendedor`, `/help` (respostas enviadas ao chat do dono em teste) e pedido `quero comprar 1000 tc, pix, mundo antica, char Rei Leao` â†’ Supabase id=6 (tc=1000, preco=R$90, pag=Pix, mundo=antica, char=rei leao). IA reforÃ§ada: tabela oficial injetada no prompt e respostas limpas sem asteriscos.
- v1.3.1 (texto do pedido): ajuda e regra da IA agora deixam claro os 4 dados obrigatÃ³rios para comprar â€” nome do char, quantidade de TC, mundo e forma de pagamento (Pix). Exemplo no /start. Testado local (200 ok).
- v1.4.0 (dashboard de vendas): rota GET /dashboard com faturado total, nÂº de pedidos, nÂº de clientes, pedidos dos Ãºltimos 14 dias (grÃ¡fico de barras) e tabela dos Ãºltimos 10 pedidos â€” dados reais do Supabase via novo mÃ©todo `OrderStore.list()` (paginaÃ§Ã£o Range + fallback para arquivo). /pedidos agora aponta para /dashboard. Testado local: 5 pedidos, R$247,50, 1 cliente.
- v1.4.1 (memoria de compra): criado MEMORIA_COMPRA.md com a regra de cÃ¡lculo de preÃ§o (proporÃ§Ã£o 1.000 TC = R$ 90 â€” valor = quantidade x 90 / 1.000, passo a passo). Regra injetada no prompt da IA (calcula quantidades fora da tabela mostrando o cÃ¡lculo) e aplicada no registro: novo `calc_price()` em bot.py (tabela fixa para 100/250/500/1.000/2.500; fÃ³rmula para o resto). Testado local: pedido de 600 TC gravou no Supabase id=7 com preco R$54,00; calc_price(800)=R$72,00, calc_price(1500)=R$135,00.
- MigraÃ§Ã£o do histÃ³rico (10/09): script `scripts/migrar_pedidos.py` insere no Supabase as linhas do `pedidos.json` ainda ausentes (dedupe por mensagem+chat_id) e esvazia o arquivo local ao concluir. Resultado: 5 inseridos (banco com 11 pedidos), pedidos do dia 09/09 preservados com data/chat/usuario originais.
- v1.5.0 (fluxo de pagamento Pix): colunas `status`, `pix_confirmado_em` e `entregue_em` adicionadas ao Supabase via `scripts/migracao_status.sql`; pedido nasce com `status=pendente` e cliente recebe texto com valor + chave Pix (configurÃ¡vel via var `PIX_KEY` no .env/Render; sem chave o texto pede para usar /vendedor). Comandos `/pago <id>` e `/entregue <id>` no chat do dono (validaÃ§Ã£o por chat_id), com aviso automÃ¡tico ao cliente em cada etapa; nÃ£o-dono recebendo `/pago` Ã© bloqueado. Dashboard: faturado contabiliza sÃ³ pedidos com `status=pago` e agora tem card "Pagos" + coluna "Status" estilizada. Testado local: pedido id=13 (1500 tc, R$135, nisseus, antica) -> /pago -> status=pago (ts preenchido) -> /entregue -> status=entregue; dashboard exibe status e totais; nÃ£o-dono bloqueado.
## Testes feitos (11/09/2026)

- v1.6.0 (Pix automÃ¡tico via Mercado Pago, 11/09): token de produÃ§Ã£o do Mercado Pago validado (`GET /users/me`). Fluxo novo: pedido detectado -> bot pede o e-mail do cliente -> `create_pix_charge` cria cobranÃ§a Pix real (`POST /v1/payments`, payment_method_id=pix, external_reference=id do pedido, header `X-Idempotency-Key` obrigatÃ³rio, notification_url `RENDER_URL/webhook/mp`) -> `send_qr` envia QR (imagem via sendPhoto + cÃ³digo copia e cola, validade 30 min) -> quando o pagamento confirma, o Mercado Pago chama `/webhook/mp`, que consulta o pagamento e, se `approved`, marca o pedido como `pago` sozinho e avisa cliente e dono. Sem MP configurado, cai no fluxo manual (PIX_KEY + /pago). `OrderStore.save` voltou a retornar a linha salva com id (header `Prefer: return=representation` na REST do Supabase; fallback arquivo gera id prÃ³prio). Testado local: fluxo completo pedido->e-mail->QR no Telegram; webhook mock validou pedido -> pago com pix_confirmado_em; cobranÃ§a real de R$1,00 criada e cancelada (validaÃ§Ã£o da API). OrfÃ£os de teste cancelados e linhas de teste removidas. OBS.: nessa sessÃ£o a tabela pedidos foi limpa â€” as linhas existentes eram todas de teste (ids 1-13, nenhuma venda real).
- v1.7.0 (revisÃ£o, seguranÃ§a e landing, 11/09): `/` virou landing pÃºblica (preÃ§os, como comprar, botÃ£o + QR para t.me/bapzx_bot), novo `/health` para monitoramento, `/dashboard` e `/pedidos` passaram a exigir `DASHBOARD_KEY` (401 sem chave; 200 com `?key=`), rate limit anti-spam da IA (5 msgs/12s), extraÃ§Ã£o do char corrigida com stop-words (`char Rei Leao mundo antica` -> "rei leao"), expiraÃ§Ã£o de 30 min no pedido de e-mail do Pix, prompt da IA orientado a nÃ£o pedir e-mail (o sistema pede). Suite de testes offline passou: landing, health, trava de dashboard/pedidos, fluxo de pedido (fallback e MP), e-mail (vÃ¡lido/invÃ¡lido/expirado), QR gerado, rate limit e webhook/mp idempotente.
- v1.8.0 (automaÃ§Ã£o da planilha de clientes, 11/09): `push_to_sheet` envia cada pedido (e cada atualizaÃ§Ã£o de status via `apply_status` â€” pago/entregue) como POST para o Apps Script Web App (`SHEET_WEBAPP_URL`), autenticado por `SHEET_TOKEN`; payload mapeado para as 14 colunas da planilha (data, cliente, contato, origem, mundo, char, quantidade_tc, preco, tipo_pagamento, data_pagamento, data_entrega, status, id_pedido, observacoes); status "pendente" vira "pagamento_pendente" na planilha. Testes: unit de payload/mapeamento/what-if (sem config nÃ£o quebra) + suÃ­te v1.7.0 completa verde. CONFIRMADO AO VIVO: create criou linha e update por id_pedido atualizou a MESMA linha (pago/entregue) sem duplicar; script ganhou `ensureHeader` (auto-repara o cabeÃ§alho p/ 14 colunas). Web App implantado; SHEET_WEBAPP_URL/SHEET_TOKEN/DASHBOARD_KEY adicionados no Render.
- v1.10.0 (11/09): precos proporcionais a R$ 90/1.000 RC (100=R$9,00; 250=R$22,50; 500=R$45; 1.000=R$90; 2.500=R$225). Moeda em todo o bot vira RC (Rubini Coins, do server RubinOT). Service BAPZX: R$20/h (BRL, confirmado), dedicado a UP level no RubinOT.
- v1.9.1/v1.9.0 (rebrand BAPZX/RUBINI COINS + serviÃ§o + entrega 10 min, 11/09): troca do nome da loja para "RUBINI COINS" (empresa mÃ£e BAPZX), comando /servico (R$20/h, WhatsApp (19) 99181-3598), HELP/ABOUT/persona/landing atualizados, entrega em atÃ© 10 min apÃ³s pagamento em todos os textos (tabela, pedido, QR), resumo do pedido junto com o QR gerado (tc, valor, mundo, char, validade, entrega). Testado: py_compile + suÃ­tes (v1.7.0, planilha) verdes.
- v1.12.0 (validacao de personagem no pedido, 12/09): antes de salvar o pedido, o bot consulta a API publica do RubiNot (GET /api/characters/search?name=...) e: (a) achou -> mostra nome/level/vocacao/mundo oficiais e pede confirmacao (sim/nao); (b) mundo informado diferente do oficial -> avisa e so fecha com confirmacao explicita; (c) nao achou -> bloqueia pedido e pede nome certo; (d) erro/API fora -> segue fluxo normal. Confirmado, o pedido salva char e mundo OFICIAIS. Timeout 12s + User-Agent de navegador (requests normal sem bloqueio). Interruptor por env RUBINOT_VALIDATE (default on). Expira confirmacao em 15 min. Testado: py_compile + suÃ­tes (test_rubinot_v112 8 cenarios, v1.7.0, auth) verdes.
- v1.12.1/v1.12.2 (12/09): diagnostico da validacao caindo em prod. (1) Webhook do Telegram estava registrado SEM secret_token -> todo update real do Telegram dava 403 (suas respostas nao chegavam). Corrigido com --set-webhook registrando o secret de novo. (2) Logs [rubinot] nao apareciam no Render (stdout bufferizado) -> flush=True. (3) parse_amount so aceitava tc; adicionado rc/rubini coins (pedido "100 rc" ficava sem valor). (4) Verificado nos logs do Render: RubiNot devolve 403 HTML proprio para IP de datacenter (Render), tanto requests quanto curl_cffi (impersonate chrome); do IP de casa funciona. Consulta inviavel a partir do servidor.
- v1.13.0 (12/09): confirmacao MANUAL garantida. Com a API do RubiNot indisponivel no Render, status "erro" agora pede confirmacao manual do pedido inteiro (char/mundo/rc/valor) antes de salvar - substituiu o comportamento de salvar direto. Mensagem final a pedido do dono: "Confere os dados acima? Responda SIM ou NÃO." Validado ao vivo: SIM salva pedido (id 21, Inmortals/auroria/250/R$22,50), NÃO cancela sem salvar; supabase zerado depois da limpeza dos testes (ids 18-21 removidos).
- v1.14.0 (12/09): 3 melhorias. (1) Botoes inline (SIM/NÃO de confirmacao + menu Comprar/\,/preco/\,/vendedor) com handler de callback_query. (2) Feedback pos-entrega (nota 1-5 e/ou comentario) salvo no pedido (colunas feedback, feedback_score) e avisado ao dono; migracao supabase_migracao_v114.sql pendente de aplicar. (3) Relatorio mensal com /relatorio (dono) + envio automatico dia 1. Testes: test_v170 (v1.14.0), test_rubinot_v112 (mocks com reply_markup), auth, planilha, parse_rc — todos verdes.
- v1.14.1 (12/09): auditoria de seguranca (e-mails estranhos). Varredura completa (repos/historico/arvore/backup/.env) sem segredos reais vazados; colaborador unico = dono. Reforcos: throttle por IP no /webhook/mp (60/min, 429) e validacao de host no /login (ALLOWED_HOSTS). Cookie de sessao com SECRET_KEY padrao rejeitado em prod. Deps sem CVE. Testes verdes.
- v1.14.2 (12/09): nova mensagem de boas-vindas a pedido do dono ("Boa tarde! Seja bem-vindo a BAPZX." + comandos /compra /site /info + service R$20/h). Novos comandos /compra (instrucoes de compra), /site (link do portfolio), /info (alias de /quemsomos). MENU_KEYBOARD atualizado: [Comprar RC] [/site] [/info] [/vendedor] (callbacks menu_site/menu_info). /preco e /servico mantidos. Testes verdes.
- v1.14.3 (12/09): correcao do mojibake em producao (o dono reportou letras erradas ex.: "confirmaÃ§Ã£o"). Diagnosticado por bytes crus: o bot.py inteiro tinha strings com dupla codificacao (UTF-8 decodificado como texto e re-encodado). Correcao em 3 etapas: (1) 37 strings via tokenize+repr, (2) 15 via busca de bytes do padrao mojibake + substituicao com validacao de parse, (3) 6 manuais (emojis do SERVICO_TEXT, prompt da IA "TABELA DE PREÃ‡OS"->"PRECOS", dashboard "ultimos/ultimos", "estÃ© no mundo"). Audit final cp1252: 0 literais com dupla codificacao; bytes hex das mensagens (HELP/ABOUT/COMPRA/SITE/SERVICO/NOVO PEDIDO/feedback) conferidos corretos. Migracao supabase_migracao_v114.sql (feedback/feedback_score) aplicada pelo dono e verificada via GET /rest/v1/pedidos. Teste ao vivo em andamento: pedido TESTE-VIVO aceito no /webhook (200); callback char_sim deu HTTP 500 em prod (sem repro local; a investigar). Suites todas verdes (test_v170 v1.14.3, rubinot, auth, planilha, parse_rc).

## ConfiguraÃ§Ã£o Supabase (10/09/2026)

- Projeto: `https://wtgzsurppwwrzhctnnfa.supabase.co` â€” tabela `public.pedidos` criada via SQL Editor.
- Usar a service role key legada (JWT) â€” a `sb_secret_*` nova retornou 401 e a `sb_publishable_*` retornou 404. A JWT Ã© a Ãºnica funcionando com o REST.
- `.env` local configurado. Render configurado (5 variÃ¡veis direto no serviÃ§o: TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_CHAT_ID, GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY) e validado com pedido real gravado no banco.

## SeguranÃ§a

- Token do bot rotacionado em 10/09 (via /revoke no BotFather): antigo revogado (401) e novo token aplicado no `.env` local, no Render (TELEGRAM_BOT_TOKEN) e no webhook (setWebhook â†’ bapzx-bot-tibia.onrender.com/webhook). Teste end-to-end: /preco pelo webhook do Render respondeu 200 com a resposta entregue no chat do dono.
- Token do Mercado Pago (MP_ACCESS_TOKEN): fica somente no `.env` local (gitignored) e nas env vars do Render; nunca em cÃ³digo/documentos/backup. ValidaÃ§Ã£o do dono usada nas chamadas: a conta pertence a lucascristianini@outlook.com.br.
- Nunca colocar senhas, tokens ou chaves de API no cÃ³digo, documentaÃ§Ã£o ou backup (ver MEMORIA_SEGURANCA.md).

## PendÃªncias

- Tratar pedido assÃ­ncrono: cliente informa mundo/char depois do valor (pedido parcial).
- Remover placeholders pendentes da persona, se houver.
- Confirmar visualmente a resposta da IA em atendimento real (no teste, o pedido gravou correto; a resposta da IA precisa ser conferida no chat apÃ³s a correÃ§Ã£o da chave).
- Reavaliar a tarifa do Mercado Pago no Pix: decisÃ£o atual Ã© absorver (ver DecisÃµes, 11/09); revisar na primeira venda real.
- Validar o fluxo Pix automÃ¡tico em atendimento real de ponta a ponta (cliente real paga, webhook confirma, /entregue encerra).- v1.11.0 (Google Login + areas de cliente/admin, 11/09): autenticacao robusta no Flask/Render com OAuth do Google (authlib, sessao segura: SECRET_KEY novo no .env, cookie httpOnly + SameSite=Lax + Secure; e-mail verificado exigido). Rotas: /login, /oauth/callback, /logout, /cliente (pedidos da propria conta via email do Pix), /admin (todos os pedidos + acoes pago/entregue via POST protegido por sessao e verificacao de referer; ADMIN_EMAILS define quem e admin). Area do cliente vincula pelo email: pedido passa a gravar o email usado na cobranca. Schema novo no Supabase (ver supabase_migracao_v111.sql): coluna email em pedidos + tabela profiles. GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET/ADMIN_EMAILS ainda vazios no .env — pendente credencial do Google (GOOGLE_OAUTH_PASSO_A_PASSO.txt) e rodar o SQL. Portfolios v2.0 (dark premium) e v3.0 (multi-pagina; home so hero; Render vira so API com / 302 -> portfolio). Testes: test_v170 (v1.11.0) + test_auth_v111 verdes.
