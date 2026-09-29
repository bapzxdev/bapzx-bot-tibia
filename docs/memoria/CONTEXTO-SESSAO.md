# CONTEXTO-SESSAO — LEIA NO CHECK-IN (sessão dia 24, bot v2.10.8 — MARKTRADE: autocomplete de itens + ficha local no detalhe CONCLUÍDA e NO AR)

Este arquivo existe para a próxima sessão continuar sem se perder.

## Estado atual: v2.10.8 (bot+painel) · portfólio no ar · Render no ar

- v2.10.8 (24/09) → **autocomplete de itens no Publicar anúncio + ficha local
  no Detalhes do anúncio** (pedido do dono + extensão para o detalhe). Novo
  `mk_itens.py` (`_MK_ITENS_DB` 54 itens: 14 Rods + 40 Wands, campos
  nome/nivel/vocacao/elemento/bonus/resistencia/atk/def/slots/peso/drop) — o
  `bot.py` injeta via `_MK_ITENS_JSON` no `_MK_AC_SCRIPT` (dropdown filtrado +
  ficha do item; SÓ no Publicar anúncio `/cliente/troca`; troca.html revertido).
  `painel.py` ganhou `_ficha_local(nome)` (normalização sem acentos) e devolve
  `ficha_local` em `/api/item` e `/api/troca/<id>`; `anuncio.html` renderiza
  "Ficha do item — dados da nossa base de itens" antes da ficha do Wiki.
  VERSION bot+painel **2.10.8**. Testes: py_compile OK; test_marketplace **61
  OK**; test_coins **26 OK**; navegador mock id=99 com ficha local completa.
- **NO AR**: commits `fd8e412` (bapzx: bot.py+painel.py+mk_itens.py novo,
  .gitignore ignora `_mk_*.py`) e `fa61927` (portfólio). Render já em v2.10.8
  (`/health` ok). **8 anúncios de teste criados (ids 14–21)** — 4 VIP (Sanguine
  Coil 95M, Falcon Wand 89M, Cobra Wand 70M, Lion Wand Troca) + 4 recentes
  (Hailstorm 4M, Moonlight 3,5M, Rod of Dest 60M, Wand of Dest 50M), sprite
  real TibiaWiki. Validado ao vivo: `/api/troca/14` com ficha_local (600/
  Sorcerers/114 atk); `anuncio.html?id=14` renderiza a ficha local; `troca.
  html` mostra 4 VIP no topo + recentes.
- **Próximo (dono)**: validar ao vivo o autocomplete digitando "sangui" em
  /cliente/troca e conferir os 8 anúncios (manter/remover os de teste).
- v2.10.1 (23/09) → **ajustes do MARKTRADE pedidos pelo dono**: o campo
  **Mundo** virou `<select>` com os **16 mundos** (`_MK_MUNDOS`: Auroria,
  Belaria, Bellum, Drakaria, Eldrian, Elysian, Infernum I/II/III, Lunarian,
  Malveria, Mystian, Obsidian, Solarian, Tenebrium, Vesperia), com mundo
  validado no POST (`world not in _MK_MUNDOS` → flash rejeição); **"Tipo de
  PvP" removido** do form e do payload (`/api/troca` sem `pvp`; vitrine
  troca.html sem dot, cores SERVER_COLORS p/ 16 mundos); **imagem automática
  do Wiki Tibia** via `_mk_itemsprite(item_name)` (mediawiki API, cache
  `_SPRITE_CACHE` cap 800, timeout 8s, nunca derruba), chamado no POST quando
  `sprite` vazio. Migration **v124 APLICADA pelo dono** (23/09). VERSION
  bot+painel **2.10.1**. Testes: **37 OK** marketplace (novos: `_MK_MUNDOS`,
  `_mk_itemsprite` sucesso/cache/falha, mundo inválido rejeita 302, mundo
  válido sem tipo_pvp, sprite vazio busca automático) + **26 OK** coins;
  py_compile OK. Linha 1 do bot.py corrompida (`ja subimport base64`) →
  restaurada `import base64`. **Falta deploy no Render (v2.10.1) e validar ao
  vivo (publicar com mundo do select + sprite do Wiki Tibia no anúncio +
  vitrine troca.html no portfólio).**

- v2.10.0 (23/09) → **MARKTRADE (marketplace de anúncios)** (pedido do dono):
  área do cliente `/cliente/troca` (publicar anúncio + detail com selo
  VERIFICADO/SELLER# + PIX + listagem com filtros) e módulo ADM
  `/admin/marketplace` (config preços/limites/durações + gestão de anúncios
  ativar/bloquear/verificar + teste VIP). PIX Mercado Pago com
  `external_reference` prefixado `PUB-<listing>`/`DES-<listing>`/`VIP-<email>`;
  ativação e selo VIP SÓ via webhook/query real. rbac:
  ver_marketplace/gerenciar_marketplace. Migration `supabase_migracao_v124.sql`
  (marketplace_config + marketplace_listings + marketplace_pagamentos +
  profiles.vip_until) **APLICADA (23/09)**. VERSION 2.10.0 bot+painel.
  30 testes novos OK + regressão 26 OK. **Deploy no Render e validação ao vivo
  pendentes.**

- v2.9.0 → redesign da área do cliente (dashboard SaaS dark); bot.py 2.9.0.

- v2.7.12 → **Autocomplete de cliente no Service**: campos Nome do cliente e
  WhatsApp do cliente no dashboard auto-completam com clientes já cadastrados
  (junta `servicos_manuais` + `profiles`); JS preenche o WhatsApp/nome do
  parceiro ao escolher um conhecido. VERSION painel.py 2.7.12 (bot.py 2.7.3).
  **Falta deploy no Render** e validação ao vivo.

- v2.7.1 → **Service com valor cobrado automático**: form novo/editar de
  serviço agora tem **Valor por hora (R$)** (padrão 20), **Horas** e
  **Desconto (R$)** (novo) com **pré-cálculo ao vivo via JS**; o valor salvo
  = `max(0, valor_hora * horas - desconto)` (ex.: 1h → R$ 20, 1,5h → R$ 30).
  Corrigido o bug que estourava os totais/"valor absurdo": `_parse_brl`
  tratava "150.00" do Supabase como milhar → 15000; agora só o formato BR
  "1.500,50" usa vírgula como decimal. Migration nova
  `supabase_migracao_v122.sql` (colunas valor_hora/desconto + backfill) —
  **PENDENTE do dono no SQL Editor**.
- v2.7.0 → áreas **Service** (diário de serviços manuais do dono: CRUD +
  KPIs Pix/Coins/Horas no topo; sidebar Principal, ícone dollar) e
  **Segurança** (histórico de login com IP/dispositivo, sessões ativas e
  encerrar sessão; sidebar Sistema, ícone lock); bot.py registra sessão no
  login (tabela `sessoes`) e encerra no logout; guardas do painel validam a
  sessão ativa (`_sessao_ativa`, cache 60s) e forçam logout se encerrada;
  WhatsApp adicionado ao form de edição de cliente. Migration
  `supabase_migracao_v121.sql` (servicos_manuais + sessoes +
  profiles.whatsapp) — **APLICADA pelo dono (17/09)**.
- v2.6.0 → Item 13 (cargos/Administradores: ADMINISTRADOR total, MODERADOR,
  ATENDENTE, FINANCEIRO; legados normalizados) + item 9 (Notificações: sino e
  /admin/notificacoes com feed por permissão + Alertas administrativos).
- v2.5.0 → Auditoria completa: /admin/audit com busca, filtros, paginação
  e Exportar CSV + eventos do bot (pedido, PIX, pagamento, entrega, feedback).
- v2.4.0 → aba Configurações no dashboard: Site, Conta, Pagamentos, Notificações.
- v2.3.0 → cupons de desconto.
- v2.0.0 → RBAC "BAPZX ACCESS" + páginas legais LGPD + grupos do WhatsApp.
- v2.0.1 → acentos padronizados (sem entidades HTML) + links na mesma aba.
- v2.0.2 → pentest ZAP: headers HSTS + CSP adicionados.
- v2.1.0 → separação SERVIÇOS × ITENS (Intermediação na tabela `servicos`).
- v2.1.1 → endpoints públicos (`/api/itens`, `/api/grupos`, `/api/servicos`)
  degradam para lista vazia em queda momentânea do Supabase (sem 500).
- v2.1.2 → página "Escolha a área": link "Voltar ao site", título da aba
  "BAPZX · Escolha a área" e marca BAPZX com Sora + gradiente (igual início).
- v2.2.0 → dashboard de Grupos com mover (↑/↓) e Excluir + portfólio v3.7
  (cards de grupos alinhados).
- v2.3.0 → Cupons de desconto no dashboard (item 10 do roadmap).
- Migrations v118, v119, **v120 (cupons) já APLICADAS pelo dono**.

## v2.8.0 — COINS administrativo + preço dinâmico (22/09)

- **Pedido do dono**: controlar o estoque/preço de Tibia Coins manualmente no
  dashboard, com histórico e permissão somente de administrador.
- `supabase_migracao_v123.sql` (PENDENTE do dono no SQL Editor): tabela
  `coins_config` (linha única id=1 — estoque numeric(14,2) default 100000,
  preco_mil numeric(12,2) default 90, min_compra default 100, max_compra
  default 50000, status 'ativo'|'pausado', observacao, atualizado_em,
  atualizado_por, criado_em) e `coins_historico` (admin, qtd_anterior/
  qtd_nova, preco_anterior/preco_novo, alteracao, criado_em) + índices + seed
  `insert on conflict (id) do nothing`.
- `rbac.py`: novas permissões `ver_coins` e `gerenciar_coins` (labels +
  PERM_TRACK "coins"); ADMINISTRADOR=ALL e MASTER cobrem automaticamente.
- `painel.py` (VERSION 2.8.0): item **COINS** na sidebar (grupo Vendas, gated
  `ver_coins`); GET `/admin/coins` — 4 cards (COINS disponíveis, Preço/1.000,
  Status ATIVO/PAUSADO, Última atualização + por), aviso de migração pendente,
  form de edição (se `gerenciar_coins`: estoque, preço/1.000, mínimo, máximo,
  status, observação), calculadora JS `qtd*preco_mil/1000`, tabela de histórico
  (até 100); POST `/admin/coins/salvar` — CSRF, validações, grava
  `coins_historico` SÓ quando há mudança (diff), upsert `id=1` com `Prefer:
  resolution=merge-duplicates`, auditoria `coins_salvar`. Helpers `_coins_num`
  (parser BR robusto), `_coins_int`, `_coins_dec`, `_coins_linha`, `_coins_brl`.
- `bot.py` (VERSION 2.8.0): preço dinâmico — `_coins_config()` (cache 120s,
  fail-soft) em `calc_price`, `price_table_text`, `price_table_compact`,
  proporção no prompt da IA e `persona.txt` (`_persona_precos()` em
  `load_persona`); `_coins_check(tc)` barra venda quando status='pausado' ou tc
  fora de [min,max] — chamado no webhook logo após `build_order`; fail-open sem
  tabela. Preço congelado no pedido na criação (calc_price → save_order).
- **Mojibake do nome corrigido**: profiles → "Lucas \"bapstyl3x\" Cristianini
  Marca" (aspas ASCII, PATCH 204).
- Testes: py_compile OK; `test_coins.py` NOVO (23 testes — TODOS OK); regressão
  test_qtd_coins (e2e Playwright) intacto.
- **Pendente dono**: (1) aplicar `supabase_migracao_v123.sql` no SQL Editor;
  (2) re-deploy no Render (v2.8.0 no /health); (3) validar ao vivo /admin/coins
  (pausado barra venda, limites, histórico, tabela de preços do bot refletindo
  preco_mil novo).

## v2.7.0 — Service + Segurança (16/09)

- **Pedido do dono**: área Service = agenda pessoal de serviços manuais (data,
  hora, nome do serviço, cliente, WhatsApp, valor, forma de pagamento
  pix|coins, horas, observação) com KPIs no topo e CRUD completo; área
  Segurança = histórico de login com IP/dispositivo, sessões ativas e
  capacidade de encerrar uma sessão remota.
- `supabase_migracao_v121.sql` (PENDENTE do dono no SQL Editor): tabela
  `servicos_manuais` (valor numeric(12,2), formato pix|coins, status
  pendente|concluido + índices), tabela `sessoes` (sid/email/ip/user_agent/
  criado_em/ultimo_acesso/encerrado_em/ativo + índices) e `alter table
  profiles add column whatsapp`.
- `rbac.py`: permissões novas `ver_servicos_manuais`,
  `gerenciar_servicos_manuais`, `ver_seguranca`, `gerenciar_seguranca`
  (labels + PERM_TRACK).
- `painel.py` (VERSION 2.7.0, linha 17): sidebar **Service** (857-858) e
  **Segurança** (886-887); `_sessao_ativa(sid)` (145-165, `_SID_CACHE` 60s)
  usado em `_require_perm` (168) e `_require_any_perm` (183) — sessão
  encerrada → `session.clear()` + bloqueio. Rotas novas ao fim do arquivo
  (após admin_notificacoes ~3094): GET `/admin/services` (KPIs +
  tabela Editar/Concluir-Reabrir/Excluir + form novo), POST `/novo`, GET+POST
  `/admin/services/<sid>`, POST `/toggle`, POST `/excluir`, GET
  `/admin/seguranca`, POST `/admin/seguranca/sessoes/<sid>/encerrar`.
  Auditoria (`servico_*`, `sessao_encerrar`) no `_ACOES_AUDIT`. WhatsApp no
  form de edição de cliente (`admin_cliente_detalhe`).
- `bot.py` (VERSION 2.7.0): `_registrar_sessao(email)` (sid=
  `session["sid"]` setado no oauth_callback; POST `sessoes`), `_encerrar_sessao`
  no logout (PATCH `ativo=false`+encerrado_em), `audit_log("login"/"logout")`.
- Testes: test_services_seguranca.py + test_bot_sessoes.py criados; ranhou
  regressão completa (rbac/notificacoes/config/cupons/audit/v200/bot_config)
  — TODOS PASSARAM. py_compile OK.
- **Pendente**: aplicar v121 no Supabase (SQL Editor) e conferir o deploy —
  /health deve mostrar v2.7.0; sem a migration, Service/Segurança abrem
  vazios via `_fetch_soft`.

## v2.3.0 — Cupons no dashboard (16/09)

- **Item 10 do roadmap do dono**: cupons de desconto gerenciados no painel.
- `supabase_migracao_v120.sql` (PENDENTE do dono no SQL Editor): tabela
  `cupons` — codigo (unique), tipo `percentual|fixo`, valor (numeric),
  validade (date), limite_usos (0 = ilimitado), usos (contador), produto_id
  (itens.id), servico_id (servicos.id), grupo_id (grupos.id), ativo +
  índices.
- `rbac.py`: novas permissões `ver_cupons` e `gerenciar_cupons` (labels +
  PERM_TRACK "cupons"), incluídas no padrão de ADMIN e MANAGER.
- `painel.py`: item **Cupons** na sidebar do grupo Vendas (ícone novo
  "ticket"); rotas — GET `/admin/cupons` (lista com desconto/validade/
  usos-limite/escopo/status + form de novo cupom), POST `/admin/cupons/novo`,
  GET/POST `/admin/cupons/<id>` (editar), POST `/admin/cupons/<id>/ativar`
  (toggle), POST `/admin/cupons/<id>/excluir`. Validação de payload
  (codigo obrigatório/uppercase, valor > 0, % limitada a 100, validade ≤ 10
  chars, limite ≥ 0) e mensagem "Já existe um cupom com o código X" em
  conflito unique. Auditoria em todas as ações.
- Exemplo do dono: `BAPZVESPERIA` → 10% OFF.
- VERSION 2.3.0 (bot.py e painel.py). Validado: py_compile OK; test client —
  GET 200 (lista + form), novo 302 (payload normalizado), duplicado 400,
  editar 302 (fixo 15.50), ativar/desativar 302, excluir 302, CSRF inválido
  403, valor zero 400. Deploy bot `e303372` → Render: /health "bot ok v2.3.0".
- **Pendente do dono**: aplicar `supabase_migracao_v120.sql` no Supabase SQL
  Editor (o `_fetch_soft` mantém /admin/cupons abrindo vazio antes disso).

---

## Sessão v2.4.0 — Configurações no Dashboard (CONCLUÍDA, deploy 07a8467)

**Decisões**: tabela `config` já existia (v116) — sem migration nova; RBAC e
sidebar já tinham o item; só reescrevi `/admin/config`. Conta usa login do
Google (senha/2FA ficam na conta Google, exibido como card informativo).
Gateway MP fica read-only (dependente da env `MP_ACCESS_TOKEN` no Render).
Preços antigos continuam via `secao=precos`.

**Implementado**:
- `painel.py` (VERSION 2.4.0): helpers `_CONFIG_CAMPOS`, `_CONFIG_SECOES`,
  `_CONFIG_PUBLICAS`, `_config_field`, `_config_textarea`, `_config_bool`,
  `_config_tabs`, `_config_grupo_html`. Abas via `?aba=site|conta|pagamentos|
  notificacoes`. Salvamento valida por seção e grava **só campos presentes no
  form** (não apaga os outros). POST `/admin/config/conta` altera o nome do
  usuário logado + auditoria. GET `/api/site` público (rate-limit + CORS)
  devolve brand + só as chaves de `_CONFIG_PUBLICAS` (nunca token/segredo).
- `bot.py` (VERSION 2.4.0): `_config_map()` com cache 120 s (falha → `{}`);
  `payment_text` usa `pix_chave` do config (fallback env `PIX_KEY`);
  `notify_owner` gate `notificar_pedido`; `notify_owner_pix` gate
  `notificar_pix`; `_error500` só avisa dono se `notificar_erro != "0"`.

**Testes feitos** (local, venv):
- `test_config.py`: GET abas 200; salvar site/apagar grupos → 302 (valores no
  mock); URL inválida → 400; notificações toggles; precos antigo; conta nome
  302 (PATCH com `params email=eq.`); CSRF errado 403; `/api/site` 200 e sem
  chaves privadas; sem permissão → 302/403. **TODOS PASSARAM**.
- `test_bot_config.py`: gates de notificação OFF/ON; `payment_text` override
  e fallback; `_config_map` falha → `{}`. **TODOS PASSARAM**.
- `py_compile` bot.py/painel.py/rbac.py OK.

**Produção (deploy `07a8467`)**: Render redeploy → `/health` "bot ok v2.4.0";
`/api/site` responde com `{"ok":true,"site":{...públicas}}` (vazias ainda);
`/admin/config` sem login → 302 para /login.

**Pendências**: preencher /admin/config (logo, banner, textos, links, redes,
pix_chave, toggles) e conferir /api/site; depois ligar /api/site no portfólio
(itens 8/9 e 14 do roadmap). Migration v120 do cupom segue pendente do dono.

---

## Sessão v2.5.0 — Auditoria completa (item 14 do roadmap) (CONCLUÍDA, deploy 97565a2)

**Objetivo** (donzão): "saber quem fez o quê e quando" — listar no log
Admin X alterou preço, confirmou pedido #1234, criou grupo, usuário X comprou
500 RC. Auditoria de admin (21 rotas POST) JÁ existia desde v2.0.0; faltava:
eventos do bot e uma página de auditoria utilizável.

**Decisões**: eventos do bot gravados em `audit_log` (mesma tabela) com
`email="sistema@bapzx"`, `ip="sistema"`. `pix_gerado` loga SEMPRE (mesmo com
`notificar_pix` off) — é a trilha financeira, não a notificação. `/api/track`
(analytics de página) continua sem audit. `_ACOES_AUDIT` mapeia cada ação para
label + cores do badge.

**Implementado**:
- `bot.py` (VERSION 2.5.0): `audit_log(acao, detalhes="")` após o STORE init
  (POST `{STORE.url}/rest/v1/audit_log`, headers `STORE._headers()`,
  fire-and-forget, `detalhes[:500]`, try/except print `[audit] falhou`).
  Hooks: `pedido_criado` (fim de `_finalizar_confirmacao_char`, detalhes
  `pedido {id} | {tc} RC | {preco} | {mundo}`), `pix_gerado` (em
  `notify_owner_pix`, sempre loga), `pedido_pago`/`pedido_entregue` (em
  `apply_status` — cobre /pago, /entregue E o webhook MP), `feedback_recebido`.
- `painel.py` (VERSION 2.5.0): `/admin/audit` reescrito — busca `q` (ação ou
  detalhe via `or=(acao.ilike.*q*,detalhes.ilike.*q*)`), `ata` (dropdown
  `_ACOES_AUDIT`, `acao=eq.`), `quem` (`email=ilike.*p*`), paginação 50/pág
  (`Range: n-m` + `Prefer: count=exact` → total), **Exportar CSV**
  (até 2000 filtrados, `;` e aspas nos campos), badges coloridos por ação,
  `_fetch_soft` na listagem (PGRST205 → vazio, sem derrubar). Import
  `urllib.parse.quote` + `flask.Response` adicionados.

**Testes feitos** (local, venv): `test_audit.py` (GET base 200 + badges
traduzidos, filtro ata, busca q, quem, p=2, CSV com attachment/substrings,
sem permissão 302) e `test_audit_bot.py` (payload correto email/ip/acao,
truncamento 500, falha silenciosa), mais regressão `test_config.py` e
`test_bot_config.py` — TODOS PASSARAM. `py_compile` OK.

**Produção (deploy `97565a2`)**: `/health` "bot ok v2.5.0"; `/admin/audit`
sem login → 302 /login (rota protegida). Via test client os filtros CSV
funcionam com dados mock; ao vivo depende do dono preencher config/cupons e
fazer pedidos.

## Sessão v2.6.0 — Itens 13 (Administradores) + 9 (Notificações) (CONCLUÍDA)

**Pedido do dono**: itens 13 e 9 do roadmap. Cargos — "Administrador = acesso
total (nível 100); Moderador = clientes + pedidos; Atendente = serviços +
clientes; Financeiro = pagamentos + relatórios". Notificações — centro de
alertas no dashboard/sino.

**Decisões**: ADMINISTRADOR usa o sentinel `"ALL"` (acesso total, ignora perms
individuais restritivas) — antes o `_PADRAO["ADMINISTRADOR"]` listava as
permissões e o bypass era dead code. Cargos antigos precisam continuar válidos
(usuários já no Supabase) → `LEGADO` + `normalizar()` em todas as funções do
rbac. Notificações derivam de `pedidos`/`audit_log` (sem tabela nova): serviços
= pedidos 7d sem `tc`; novos clientes = 1º pedido nos últimos 7d; erros =
`audit_log` de `erro_pagamento` 7d. Categoria "grupo comprado" foi descartada
por não haver fonte de dados real.

**Implementado**:
- `rbac.py`: CARGOS MASTER 100 / ADMINISTRADOR 80 / MODERADOR 60 / ATENDENTE 50
  / FINANCEIRO 40 / CLIENTE 10; `CARGOS_LABEL`, `CARGOS_DESC`;
  `_PADRAO["ADMINISTRADOR"] = _PADRAO_ADMINISTRADOR` (ALL); `LEGADO`
  (ADMIN→ADMINISTRADOR, MANAGER→MODERADOR, OPERADOR/SUPORTE→ATENDENTE) +
  `normalizar()` usada por `nivel`/`cargo_valido`/`cargo_label`/`cargo_desc`/
  `perms_padrao`/`perms_efetivas`/`tem_perm`/`tem_qualquer_perm`.
- `painel.py`: helpers `_NOTIFICACOES_CACHE` (TTL 20s por e-mail),
  `_count_servicos_recentes`, `_count_novos_clientes`, `_notificacoes(user)` →
  `(feed, sistema, total)`; ícone `"alert"`; CSS das notificações; item
  "Notificações" na sidebar (grupo Principal); sino reescrito (feed + alertas
  de sistema + "Ver todas"); rota GET `/admin/notificacoes`
  (`_require_any_perm("ver_dashboard","ver_pedidos")`); `erro_pagamento` no
  `_ACOES_AUDIT`; `_cargos_desc_html()` nos formulários de usuário.
- `bot.py`: `audit_log("erro_pagamento", ...)` na falha de Pix
  (`_finalizar_confirmacao_char`) e no `/webhook/mp` não-aprovado.
- VERSION 2.6.0 (bot.py e painel.py).

**Testes feitos** (local, venv): `py_compile` OK; `test_rbac_painel.py`
(reescrito p/ o novo modelo + cargos legados + rotas), `test_notificacoes.py`
(novo: contadores, permissões FINANCEIRO/ATENDENTE, página 200, CLIENTE
bloqueado); regressão `test_config.py`, `test_audit.py`, `test_audit_bot.py`,
`test_bot_config.py`, `test_cupons.py`, `test_v200.py` — TODOS PASSARAM.
(`test_v170.py`/`test_auth_v111.py` têm falhas pré-existentes de versão/dados,
sem relação com esta mudança.)

## Ações do dono para o check-in seguinte

1. **Aplicar `supabase_migracao_v123.sql` (v2.8.0 — COINS)** no Supabase SQL
   Editor: cria `coins_config` e `coins_historico`. Sem isso o `/admin/coins`
   mostra o aviso de migração pendente e o bot segue no preço legado (R$ 90).
2. **Re-deploy no Render** e conferir `/health` "bot ok v2.8.0".
3. **Validar ao vivo /admin/coins**: editar preço/estoque → conferir cálculo e
   o histórico gravado; mudar status pausado → novo pedido no bot é barrado;
   testar limites min/max; conferir que a tabela de preços do bot (e a persona)
   refletem o preco_mil novo.
4. **Re-deploy e validação do autocomplete do Service (v2.7.12)**: abrir
   `/admin/services`, digitar "Dout" e conferir que completa para "Doutor
   Odeioretro" e puxa o WhatsApp; testar o inverso no campo WhatsApp (o
   `/health` é do bot.py — o deploy do painel não muda esse texto).
5. (**v2.7.1**) validar ao vivo `/admin/services` com o cálculo (1,5h → R$ 30),
   totais Pix/Coins, e `/admin/seguranca` (encerrar a própria sessão desloga).
6. Cupom exemplo `BAPZVESPERIA` (10% OFF, grupo Belaria-Vesperia).
7. `/admin/usuarios`, `/admin/notificacoes`, `/admin/config` (Site/Pagamentos/
   Notificações), `/admin/grupos` e `/admin/audit` — validação ao vivo pendente.
8. (Opcional) env `MASTER_EMAILS` no Render com o e-mail do dono.
9. Pendências antigas: limpeza pedidos teste, fluxo celular, publish Google
   OAuth, Fase C vetada.

--- [CHECK-OUT] Sessão v2.9.0 — 22/09/2026 ---
ENTREGUE: redesign da área do cliente (dashboard SaaS dark) — AUTH_LAYOUT
reescrito com tokens @@..@@ + _render_layout; helpers _title_initials/
_cliente_header/_status_badge/_fmt_brl/_cliente_profile/_cliente_tickets;
rotas /cliente, /cliente/perfil, /cliente/suporte, /cliente/suporte/<id>
redesenhadas (KPIs reais, tabela pedidos, empty state CTA portfólio, badges);
bug _fmt_brl corrigido (vírgula/ponto BR). VERSION bot.py 2.9.0 (painel 2.8.1).
Validado: py_compile + test_coins.py 26 OK + test client (rotas 200, 302 sem
sessão, detail 404/200) + Playwright (dark theme, responsivo 4→2 cols, header
colapsa <480px). PROXIMO DONO: re-deploy no Render (v2.9.0 no /health) e
validar ao vivo a área /cliente (logado, com/sem pedidos, suporte, perfil,
logout, mobile). Várias pendências antigas seguem (Google OAuth publish,
migrations v122/v123, validações v2.7.x/v2.8.x ao vivo).

--- [CHECK-OUT] Sessão v2.8.0 — 22/09/2026 ---
ENTREGUE: módulo COINS (painel admin com cards/form/calculadora/histórico +
RBAC ver_coins/gerenciar_coins + migration v123) + preço do bot dinâmico via
coins_config.preco_mil (calc_price, tabelas, IA, persona) + _coins_check
(pausado/limites) + mojibake do nome corrigido. 23 testes novos OK + regressão.
PROXIMO DONO: aplicar supabase_migracao_v123.sql no SQL Editor, re-deploy no
Render e validar /admin/coins ao vivo (pausado barra venda, limites, histórico,
tabela de preços refletindo preco_mil).

--- [CHECK-OUT] Sessao v2.7.2 � 17/09/2026 21:48 ---
ENTREGUE: botao/form 'Adicionar grupo' em /admin/grupos (POST /admin/grupos/novo, perm gerenciar_grupos, CSRF, audit grupo_criar). CRUD completo de grupos.
VERSION: painel.py + bot.py = 2.7.2 (sync). Suites de regressao 7/7 OK (incl. test_grupo_crud). Commit 3c716c9, push main OK.
PROXIMO DONO: re-deploy no Render (mostra v2.7.2 no /health). Apos deploy rodar /health. Feito.

--- [CHECK-OUT] Sessao v2.7.4 - 19/09/2026 ---
ENTREGUE (pedido do dono no check-in): Service form fix - horas com virgula ("2,5")
nao viram mais 0 ao salvar/editar. Causa real: float("2,5") nos POSTs de
/admin/services/novo e /admin/services/<sid> dava ValueError e o except zerava
horas (e valor_hora/desconto). Criado helper _sv_num() (aceita "2,5"/"2.5"/"1.500,50")
usado nos 2 POSTs. Removida a logica JS `svRecalc` e suas chamadas dos 2 forms;
`svCoinToggle` foi mantida e elevada a funcao independente (antes aninhada em
svRecalc no form novo; no editar era svfpToggle). forma_pagamento + campo
Quantidade de COINS (qtd_coins_row) intactos. `sv_total` (valor cobrado persistido)
continua exibido no editar, so nao e mais recalculado ao vivo.
VERSION: painel.py 2.7.3 -> 2.7.4 (bot.py 2.7.3, sem mudanca). Validado:
py_compile OK; _sv_num('2,5')=2.5, _sv_num('2.5')=2.5, _sv_num('1.500,50')=1500.5,
20 x 2,5 - 0 = 50.0 (antes 0); grep svRecalc=0 ocorrencias; svCoinToggle presente
nos 2 forms. Documentacao atualizada (MEMORIA/PENDENCIAS/ROADMAP/LEMBRETE).
PROXIMO DONO: re-deploy no Render (painel) e validar 2,5 -> salvar -> editar
(mostra 2.5, nao 0). O /health continua "bot ok v2.7.3" (bot.py nao mudou).

--- [CHECK-OUT] Sessão v2.10.8 — 24/09/2026 ---
ENTREGUE: (1) autocomplete de itens no Publicar anúncio (novo mk_itens.py com
54 itens, dropdown filtrado + ficha via JS/_MK_AC_SCRIPT; SÓ em /cliente/troca,
troca.html revertido); (2) ficha local no Detalhes do anúncio (painel.py
_ficha_local + ficha_local em /api/item e /api/troca/<id>; anuncio.html
renderiza a seção; VERSION bot+painel 2.10.8). Testes: py_compile OK;
test_marketplace 61 OK; test_coins 26 OK. NO AR: commits fd8e412 (bot) e
fa61927 (portfolio); Render em v2.10.8 (/health); **8 anúncios de teste
criados (ids 14–21): 4 VIP + 4 recentes**, sprite real TibiaWiki. Validado ao
vivo: /api/troca/14 retorna ficha_local; anuncio.html?id=14 renderiza a ficha
local completa; troca.html lista 4 VIP no topo + recentes.
PROXIMO DONO: validar ao vivo digitar "sangui" no campo Item de /cliente/troca
(autocomplete) e conferir os 8 anúncios na vitrine (manter ou remover os de
teste via _mk_cria_8.py). Pendências antigas seguem: Google OAuth publish,
migrations v122/v123 (coins), validações v2.7.x/v2.8.x/v2.9.x ao vivo,
sexta-feira = auditoria leve de segurança.

--- [CHECK-OUT] Sessão v2.10.1 — 23/09/2026 ---
ENTREGUE: ajustes do MARKTRADE pedidos pelo dono. (1) **Mundo vira select** com
os 16 mundos (`_MK_MUNDOS` em bot.py) — POST valida (`world not in _MK_MUNDOS`
→ flash + redirect), habilita o group por categoria (jogos Tibia 12 mundos,
Pokémon 3). (2) **Campo "Tipo de PvP" removido** do form e do payload (POST
não envia mais `tipo_pvp`; painel.py `/api/troca` sem `pvp`; vitrine troca.html
sem dot/texto e sem CSS `.pvp`, SERVER_COLORS mapeando os 16 mundos). Coluna da
v124 fica no banco (default vazia), SEM migration nova. (3) **Sprite automático
do Wiki Tibia**: `_mk_itemsprite(item_name)` (bot.py) via mediawiki API
(`prop=images` + `imageinfo iiurlwidth=96`), User-Agent BAPZX-MARKTRADE, timeout
8s, cache `_SPRITE_CACHE` cap 800 (entrada sempre tuple (ts, url)); chamado no
POST quando `sprite` vazio; falha → "" sem derrubar. Hint no form
("Deixe em branco para buscar a imagem automaticamente no Wiki Tibia").
Validado ao vivo: "War Hammer" → tibiawiki.com.br/images/2/25/War_Hammer.gif,
"Guardian Axe" → images/6/67/Guardian_Axe.gif, item inexistente → "". Migration
**v124 APLICADA pelo dono** (23/09). Correção: linha 1 do bot.py corrompida
(`ja subimport base64`) → `import base64`. VERSION bot+painel **2.10.1**.
Validado: py_compile OK; test_marketplace.py **37 OK** (novos: _MK_MUNDOS,
_mk_itemsprite sucesso/cache/falha_e_vazio, publicar_mundo_invalido_rejeita
302, publicar_mundo_ok_nao_valida_mundo — payload sem tipo_pvp,
publicar_sprite_vazio_busca_auto); regressão test_coins.py **26 OK**.
PROXIMO DONO: re-deploy no Render (v2.10.1 no /health), re-deploy do portfólio
(GitHub Pages, troca.html) e validar ao vivo: publicar anúncio escolhendo o
mundo no select → sprite automático aparece no anúncio → PIX → webhook ativa →
selo VIP → /admin/marketplace → vitrine troca.html. Segue em aberto: Google
OAuth publish, migrations v122/v123, validações v2.7.x/v2.8.x/v2.9.x ao vivo;
sexta-feira = auditoria leve de segurança.

--- [CHECK-OUT] Sessão v2.10.0 — 23/09/2026 ---
ENTREGUE: MARKTRADE (marketplace de anúncios) — bot.py `/cliente/troca`
(publicar + detail com selo VERIFICADO/SELLER# e PIX + listagem com filtros),
`_mk_gp`, PIX MP com external_reference `PUB-<l>`/`DES-<l>`/`VIP-<email>`
(ativação/selo VIP só por webhook/query real), `_marketplace_confirm`
PUB/DES/VIP antes do gate isdigit; limpeza de `if False else`/walrus/%-format
no cliente_troca. painel.py `/admin/marketplace` (config preços/limites/
durações + gestão ativar/bloquear/desbloquear/encerrar/verificar + teste VIP;
coluna correta `limite_publicacoes`), sidebar MARKTRADE (ícone tag), audit
marketplace_config/acao/vip. rbac.py ver_marketplace/gerenciar_marketplace.
Migration supabase_migracao_v124.sql criada (C:\DEV\Supabase). VERSION
bot+painel 2.10.0. Validado: py_compile OK; test_marketplace.py NOVO 30 OK;
regressão test_coins.py 26 OK. PROXIMO DONO: aplicar v124 no SQL Editor,
re-deploy no Render e validar ao vivo (publicar anúncio, PIX confirmando via
webhook, selo VIP, /admin/marketplace). Várias pendências antigas seguem
(Google OAuth publish, migrations v122/v123 válidas ou pendentes, validações
v2.7.x/v2.8.x/v2.9.x ao vivo).
