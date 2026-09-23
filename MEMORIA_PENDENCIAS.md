## LOG v2.10.5 (23/09/2026) - Página de detalhes do anúncio + info do item via Wiki
- Pedido do dono: clicar num anúncio da listagem MARKTRADE deve abrir uma página
  de **detalhes dinâmica**, que busca tier/atributos/requisitos/peso/preço de
  referência/histórico **automaticamente no Tibia Wiki**.
- painel.py (VERSION **2.10.5**, bot.py segue 2.10.4):
  - **GET `/api/troca/<id>`**: anúncio individual com `status` incluído;
    `_fetch_public` com `id=eq.<id>&status=eq.ativa` `range_="0-0"`; 404 + CORS
    se não achar; mesmo rate-limit de `/api/troca`.
  - **GET `/api/item?nome=`** (cache 2min `_ITEMINFO_CACHE`): consulta o
    TibiaWiki **server-side** (`action=parse&redirects=1&prop=wikitext`,
    `formatversion=2`, User-Agent BAPZX-MARKTRADE, retry com UA neutro em
    403/429, timeout `(5,15)`) — parse da `{{Infobox_Item` (`_iteminfo_wiki`) e
    limpeza de wikilinks (`_limpa_wiki`) → `info` com tier/nivel/vocacoes/
    armor/peso/imbuement/resistencias/atributos/classificacao/vende_para/
    compra_de/tipo_item/implementado (só campos preenchidos). Sem infobox/falha
    → `{}`.
  - `referencia` (`_ref_de_preco`): min/max/média/quantidade/última data a
    partir dos **anúncios ativos do mesmo item** no próprio marketplace
    (`item_name=ilike.*<nome>*`, ignora preço vazio) — **nunca inventa preço
    externo**; `None` sem dados.
- portfolio C:\DEV\MEUS PROJETOS\bapzx-portfolio:
  - **`anuncio.html`** (nova): visual dark igual troca.html, `header.wrap.back`
    + `.btn ghost` ("← Voltar para os anúncios" → troca.html) padrão do site;
    lê `?id=`, valida formato, trata loading / id inválido / 404 /
    falha de rede; renderiza tipo, status (Ativo/Vendido/Expirado), nome+tier,
    data, categoria, sprite (fallback iniciais), preço ou "Aceitando ofertas",
    mundo, anunciante (verificado), contato (email, pill), descrição (pre-wrap),
    seção "Sobre o item" (ficha do Wiki) e "Preço de referência"; título da aba
    dinâmico (`document.title`); busca `/api/item?nome=` só se houver nome e
    info/referência são bônus (falha não quebra a página).
  - **`troca.html`**: `.mk-card` virou `<a href="anuncio.html?id=...">`
    (`aria-label`, `text-decoration:none`, `cursor:pointer`); **filtros
    persistidos em `sessionStorage`** (`marktrade-filtros`, `saveState()` a cada
    alteração de filtro e `restoreState()` + `syncChips()` no carregamento) para
    o usuário voltar do detalhe com a lista como deixou.
- Testes: **+10 novos** em test_marketplace (api_troca detalhe encontrado/nao
  encontrado/rate-limit/CORS origem fora, api_item sem nome/com info,
  iteminfo_wiki parsea infobox/sem tier/falha+vazio, ref_de_preco média/vazio).
- Validado: py_compile OK; test_marketplace **56 OK**; test_coins **26 OK**;
  JS check troca.html + anuncio.html OK; navegador mock fim-a-fim (filtro Soul
  Core → clique → detalhe com Tier 3/atributos/preço referência → Voltar →
  filtro restaurado; id inválido e 404 tratados).
- **Pendente dono**: re-deploy no Render (v2.10.5 no /health) e validar ao
  vivo: clicar num anúncio real (foto/atributos/referência de preço) e o botão
  "Voltar" preservando os filtros.

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

## LOG v2.8.1 (22/09) - cache COINS: invalidacao ao salvar + TTL reduzido
- Pedido do dono: "tem como melhorar esses 2 min?" (atraso do cache de
  `coins_config` que o bot le do Supabase).
- Implementado: (1) **`_coins_invalidate()`** em bot.py zera
  `_COINS_CACHE`; o painel registra o gancho via painel.py
  `_registra_invalidador_coins()` (evita import circular) e o POST
  `/admin/coins/salvar` chama `_invalidate_coins_cache()` logo apos salvar —
  muda de status/preco/limites vale **na hora** no bot (mesmo processo
  Flask). (2) TTL do cache reduzido de 120s para **30s** (`_COINS_TTL`).
- VERSION bot.py + painel.py **2.8.1**.
- Validado: py_compile OK; test_coins.py agora com **26 testes** (novos:
  ttl=30, invalidade zera cache, gancho do painel ativo sem circular) — TODOS OK.

## LOG v2.8.0 (22/09/2026) - Modulo COINS admin + preco dinamico + mojibake do nome corrigido
- Pedido do dono: controlar manualmente estoque/preco/limites/status de Tibia
  Coins no dashboard, com historico e permissao apenas para admins.
- Migration `supabase_migracao_v123.sql` (PENDENTE do dono no SQL Editor):
  `coins_config` (id=1 unico; estoque default 100000, preco_mil default 90,
  min_compra 100, max_compra 50000, status ativo|pausado, atualizado_em/por) +
  `coins_historico`.
- CORRECAO 428C9 EM C:\DEV\Supabase\supabase_migracao_v123.sql: o primeiro
  rodar falhou com `cannot insert a non-DEFAULT value into column "id"`
  (identity `generated ALWAYS`). As tabelas agora usam `generated BY DEFAULT
  as identity` (aceita id explicito, exigido pelo upsert id=1 do painel em
  painel.py:4252 e pelo seed). Adicionado bloco `do $$` que converte um
  identity ALWAYS ja criado para BY DEFAULT (sem dropar). O arquivo foi
  substituido; basta colar o arquivo ATUALIZADO e rodar de novo (idempotente).
- rbac.py: `ver_coins`/`gerenciar_coins` (labels + PERM_TRACK "coins");
  ADMINISTRADOR=ALL e MASTER cobrem automaticamente (nenhum outro por padrao).
- painel.py (VERSION 2.8.0): sidebar COINS (Vendas, gated ver_coins); GET
  `/admin/coins` (4 cards + aviso de migration pendente + form de edicao se
  gerenciar_coins + calculadora JS + historico ate 100); POST
  `/admin/coins/salvar` (CSRF, validacoes, diff -> historico, upsert id=1,
  audit coins_salvar).
- bot.py (VERSION 2.8.0): preco dinamico via `_coins_config()` (cache 120s,
  fail-soft) em calc_price/price_table_text/price_table_compact/ask_ai/
  load_persona (_persona_precos). `_coins_check(tc)` bloqueia pausado e tc
  fora de [min,max] logo apos build_order (fail-open sem tabela). Preco
  congelado no pedido na criacao.
- Mojibake do nome do dono corrigido (PATCH 204 -> "Lucas \"bapstyl3x\"
  Cristianini Marca", aspas ASCII).
- VERSION bot.py + painel.py **2.8.0**.
- Validado: py_compile OK (admin.py/painel.py/bot.py/rbac.py/storage.py);
  `test_coins.py` NOVO com 23 testes — TODOS OK (painel GET/POST, permissao
  negada 403, CSRF 403, helpers _coins_num/_coins_brl, bot calc_price legado/
  dinamico, _coins_check pausado/limites, tabelas e persona dinamicas).
- Pendente dono: aplicar v123 no Supabase; re-deploy no Render; validar ao vivo
  `/admin/coins` (pausado barra venda, limites, historico, tabela de precos do
  bot refletindo preco_mil novo).

## LOG v2.7.12 (22/09/2026) - Service: autocomplete de Cliente e WhatsApp
- Pedido do dono no check-in: no dashboard Service, os campos "Nome do cliente"
  e "WhatsApp do cliente" devem auto-completar com os clientes já cadastrados
  (ex.: digitar "Dout" → completa "Doutor Odeioretro").
- Implementado (painel.py): helper `_sv_sugestoes()` junta os pares
  (nome, whatsapp) de `servicos_manuais` + `profiles` (perfis) e devolve
  `(nomes, whats, pares)` com `pares` bidirecional (nome↔whatsapp).
  `_sv_autocomplete_html()` renderiza 2 `<datalist>` (`sv_nomes`/`sv_whats`)
  + JS `svPair` que, ao escolher um nome conhecido, preenche o WhatsApp
  (e o inverso) se o campo parceiro estiver vazio. Inputs dos forms
  novo e editar de serviço ganharam `list='sv_nomes'`/`list='sv_whats'`
  com ids `sv_nome_input`/`sv_wpp_input`. Proteção `hasOwnProperty`
  no JS (evita colisão com chaves tipo `__proto__`).
- VERSION painel.py **2.7.12** (bot.py segue 2.7.3).
- Validado: py_compile OK; test client real (Supabase) — `/admin/services`
  200 com form novo + datalists + SV_PAIRS; `/admin/services/<sid>` 200 com
  datalist no editar; `_sv_sugestoes()` retornou clientes reais
  ("Doutor Odeioretro", "Milena Soares", "wak", +55 15 99814-7564 etc).
- Observação: mojibake do nome "Lucas bapstyl3x Cristianini" (aspas curvas no
  profiles) **CORRIGIDO na v2.8.0** — PATCH 204 normalizou para
  "Lucas \"bapstyl3x\" Cristianini Marca" (aspas ASCII).

# Memória de Pendências

Lista única de pendências, observações e bloqueios do projeto BAPZX / RUBINI COINS.

## LOG v2.10.2 (23/09/2026) - MARKTRADE: modo teste do dono (sem Pix/QR)
- Pedido do dono (testando o MARKTRADE ao vivo): na area de cliente nao gerar
  QRCODE de pagamento para ele conseguir testar (email do dono
  lucascristianini1@gmail.com).
- bot.py (VERSION 2.10.2): se o email logado esta em `MASTER_EMAILS` (que cai
  no fallback `ADMIN_EMAILS` = env com o email do dono), **publicar anuncio
  ativa direto** (PATCH status=`ativa` + `expires_at`; com destaque marca
  `is_destaque` + `destaque_until`) SEM criar `marketplace_pagamentos` e SEM
  chamar `create_marketplace_pix` (sem QR). **Assinar VIP grava**
  `profiles.vip_until` direto (PATCH + invalida `_MK_VIP_CACHE`) SEM Pix. Flash
  informativo "modo teste do dono — publicado/ativado sem cobrança" e aviso
  âmbar no topo de `/cliente/troca` e `/cliente/troca/vip` quando MASTER.
- Clientes comuns continuam no fluxo normal de cobranca (PUB-/DES-/VIP- com QR).
- Testes: test_marketplace.py **40 OK** (novos: `test_publicar_master_sem_qr_
  ativa_direto`, `test_publicar_master_com_destaque_sem_qr`, `test_vip_master_
  sem_qr_ativa_direto` — assert que ativa via PATCH e NAO cria pagamento);
  regressao test_coins.py **26 OK**; py_compile OK.
- **PENDENTE (dono)**: rodar local ou re-deploy no Render (v2.10.2 no /health)
  e testar ao vivo com o email MASTER (publicar sem QR, destaque, VIP sem QR,
  vitrine troca.html); apos validar, retomar as pendencias anteriores
  (validações v2.7.x/v2.8.x/v2.9.x ao vivo, Google OAuth publish).

## LOG v2.10.1 (23/09/2026) - MARKTRADE: mundo em select (16 mundos), remoção do tipo de PvP e sprite automático do Wiki Tibia
- Pedido do dono (ajustes sobre o marketplace da v2.10.0).
- bot.py (VERSION 2.10.1): campo **Mundo** virou `<select>` com os **16 mundos**
  (`_MK_MUNDOS`, logo após `_mk_ativo`): Auroria, Belaria, Bellum, Drakaria,
  Eldrian, Elysian, Infernum I, Infernum II, Infernum III, Lunarian, Malveria,
  Mystian, Obsidian, Solarian, Tenebrium, Vesperia. POST valida o mundo
  (`world not in _MK_MUNDOS` → flash "Selecione um mundo válido para o
  anúncio." + redirect) e NÃO valida mais "existe" (mundo já é select).
- Campo **"Tipo de PvP" removido** do form e do payload (POST não envia mais
  `tipo_pvp`); coluna `tipo_pvp` da v124 fica no banco (default vazia), sem
  migration nova. painel.py (VERSION 2.10.1): `/api/troca` não devolve mais
  `pvp`. Vitrine troca.html (bapzx-portfolio): removidos `pvpDot`, `.dot` e
  CSS `.pvp`; `SERVER_COLORS` mapeia os 16 mundos (verde/âmbar/azul/roxo/slate);
  serverHtml só com `<b>world</b>`.
- **Sprite automático do Wiki Tibia**: novo helper `_mk_itemsprite(item_name)`
  (bot.py) — mediawiki API `prop=images` e `imageinfo iiurlwidth=96` em
  `https://www.tibiawiki.com.br/w/api.php`, User-Agent `BAPZX-MARKTRADE/VERSION`,
  timeout 8s, cache `_SPRITE_CACHE` (cap 800; entrada é sempre um `tuple`
  `(timestamp, url)`, evita colisão cache-hit vs cache-miss). Chamado no POST
  quando `sprite` vazio; falha nunca derruba (retorna ""). Validado ao vivo no
  navegador/requests: "War Hammer" → `https://www.tibiawiki.com.br/images/2/25/War_Hammer.gif`, "Guardian Axe" → `images/6/67/Guardian_Axe.gif`, item
  inexistente → "". Hint: "Deixe em branco para buscar a imagem automaticamente
  no Wiki Tibia".
- Correção de arquivo corrompido: linha 1 do bot.py estava `ja subimport base64`
  (corrompida) → restaurada para `import base64`.
- Testes: regressão **test_marketplace.py AGORA COM 37 testes (37 OK)** (novos:
  `test_mk_mundos`, `test_mk_itemsprite_sucesso`, `test_mk_itemsprite_cache`,
  `test_mk_itemsprite_falha_e_vazio`, `test_publicar_mundo_invalido_rejeita`
  (302), `test_publicar_mundo_ok_nao_valida_mundo` (payload sem `tipo_pvp`),
  `test_publicar_sprite_vazio_busca_auto` — busca automática e sprite vai no
  payload); `test_coins.py` **26 OK**; `py_compile` OK (bot.py, painel.py,
  test_marketplace.py). Ajustes de teste: `_FakeResp.raise_for_status()`
  adicionado; `TestMkBot.setUpClass` ganhou `TESTING=True`,
  `PROPAGATE_EXCEPTIONS=True` e `secret_key="teste-marketplace"` (necessário
  com o novo populate antes de dar `app.secret_key = wandb.KEY_SECRET`, pois o
  secret default já não vale mais — ver bot.py ~linha 102). Fixture LISTING
  (linha 44) ainda imita linha real do banco com `tipo_pvp` = "" e `world`
  "honbra"→"Auroria"; asserts negativos de pvp nas linhas 638/692.
- **Migração v124 APLICADA pelo dono** em 23/09/2026 (confirmado); arquivo
  `C:\DEV\Supabase\supabase_migracao_v124.sql`. Sem migration nova nesta
  versão.
- **PENDENTE (dono)**: re-deploy no Render com v2.10.1 (conferir "2.10.1" no
  /health) e RE-deploy do bapzx-portfolio (troca.html) no GitHub Pages, depois
  validar ao vivo o fluxo completo: publicar anúncio com mundo do select →
  sprite automático no anúncio → PIX → webhook ativa → selo VIP →
  /admin/marketplace → vitrine troca.html. Sexta-feira = auditoria de
  segurança leve (agenda recorrente).

## LOG v2.10.0 (23/09/2026) - MARKTRADE: marketplace de anuncios (bot + painel + RBAC)
- Pedido do dono: os grupos de trade pediam um espaco para anuncios; feito o
  modulo `MARKTRADE` (v2.10.0).
- bot.py (VERSION 2.10.0): area do cliente `/cliente/troca` (publicar
  anuncio: jogo, categoria, titulo, descricao, preco em GP por vidro flexivel,
  imagens), `/cliente/troca/<aid>` (detail com selo VERIFICADO/SELLER# e
  botao PIX), listagem com filtros; `_mk_gp` (formata GP, 2 decimais;
  None/vazio -> "Aceita ofertas"); `preco_txt` usa `_mk_gp` sem sufixo " gp".
  PIX Mercado Pago com `external_reference` prefixado `PUB-<listing>` /
  `DES-<listing>` (publicacao+destaque num PIX so) / `VIP-<email>`; selo VIP e
  ativacao de anuncio SOMENTE via webhook/query real no MP (nunca ao abrir o
  QR). `_marketplace_confirm` cobre PUB/DES/VIP; branch do webhook fica ANTES
  do gate `reference.isdigit()`. Limpeza de construcoes fragieis em
  `cliente_troca`: removidos `if False else`, walrus `vip_until` e mistura
  `%`-format com f-string (form e corpo de `cliente_troca_pagar` agora puros
  f-string).
- painel.py (VERSION 2.10.0): modulo ADM `/admin/marketplace` (no meio do
  admin, entre COINS e Seguranca): config de precos/limites/duracoes
  (default: R$ 2,99 publicacao / +R$ 5,00 destaque / R$ 12,99 VIP / limite 3
  anuncios / duracao 30 dias), lista de anuncios com status e botoes
  ativar/bloquear/desbloquear/encerrar/verificar + teste VIP; coluna correta
  `limite_publicacoes` no helper `_mk_limite`, no form e no handler POST;
  sidebar item MARKTRADE (Vendas, icone "tag") + `_ICONS["tag"]`; auditoria
  `marketplace_config`/`marketplace_acao`/`marketplace_vip`.
  Helpers novos: `_mk_linha`, `_mk_preco`, `_mk_limite`, `_mk_mkt_status`,
  `_mk_tipo_lbl`, `_mk_status_badge`, `_mk_gp_admin`.
- rbac.py: perms `ver_marketplace` e `gerenciar_marketplace` (labels +
  PERM_TRACK "marketplace"); ADMINISTRADOR/MASTER cobrem via ALL.
- Migration `supabase_migracao_v124.sql` (C:\DEV\Supabase) - PENDENTE do dono
  no SQL Editor: `marketplace_config` (linha unica id=1: preco_publicacao R$
  2,99, preco_destaque R$ 5,00, preco_vip R$ 12,99, limite_publicacoes 3,
  duracao_*_dias 30, status), `marketplace_listings` (anuncios: user_id,
  item_name, description, character_name, world, contact, category,
  tipo_anuncio venda|compra|troca, status pendente|ativa|expirada|encerrada|
  bloqueada, is_destaque, destaque_until, expires_at, preco, aceita_ofertas,
  sprite, tipo_pvp, verificado + indices), `marketplace_pagamentos`
  (external_reference unico no formato PUB-<listing>/DES-<listing>/
  VIP-<email>, tipo, listing_id, user_id, valor, status, mp_id, qr_code) e
  `profiles.vip_until`. Admin mostra aviso com o caminho do arquivo quando a
  tabela falta.
- Vitrine publica no portfolio (`troca.html`) pronta para consumir os
  anuncios publicados.
- Validado: py_compile OK (bot.py/painel.py/rbac.py);
  `test_marketplace.py` NOVO com 30 testes - TODOS OK (helpers do painel,
  GET/POST admin com mocks, webhook VIP, `_marketplace_confirm` PUB/DES/VIP,
  render `/cliente/troca` com mocks); regressao `test_coins.py` 26 OK.
- Pendente dono: aplicar v124 no Supabase; re-deploy no Render; validar ao
  vivo (publicar anuncio, PIX, webhook confirmando, selo VIP, /admin/marketplace).

## LOG v2.9.0 (22/09/2026) - Redesign da área do cliente (dashboard SaaS dark)
- Pedido do dono: "redesign /cliente" — visual profissional (tema dark, roxo,
  verde #4ade80 positivo, azul ações), responsivo 1920→390px, acessível, SEM
  tocar em backend/rotas/auth/CSRF/integrações.
- bot.py (VERSION 2.9.0): AUTH_LAYOUT reescrito + `_render_layout()` (tokens
  `@@TITLE@@/@@BRAND@@/@@TOP@@/@@BODY@@/@@WHATSAPP@@` via `.replace()` — NÃO
  `.format()`, o CSS não tem mais chaves escapadas); helpers `_title_initials`,
  `_cliente_header(user, active)`, `_status_badge(status)`, `_fmt_brl(value)`,
  `_cliente_profile(email)`, `_cliente_tickets(email)`. Rotas: `/cliente`
  (boas-vindas "Olá, {primeiro}! 👋" + 4 KPIs reais — total/em andamento/
  concluídos/tickets — + tabela pedidos recentes com badges + card último
  pedido + empty state com CTA → PORTFOLIO_URL + ajuda + card perfil + nota
  sobre e-mail do pedido), `/cliente/perfil` e `/cliente/suporte` usam o novo
  header; suporte com âncoras `#novo`/`#chamados`; detail ticket corrigido de
  `.format()` para `%` (evita erro de chaves). `_status_badge` mapeia
  entregue→Concluído, aberto→Pendente. `_fmt_brl` corrigido: particionava por
  vírgula quando o format BR já dá ponto decimal ("22.50,") → agora
  `f"{n:,.2f}".partition(".")` + milhar com ponto ("R$ 2.250,00").
- Validado: py_compile OK (bot.py/painel.py); test_coins.py **26 testes OK**;
  test client — `/cliente` `/cliente/suporte` `/cliente/perfil` `/acesso` 200;
  `/cliente` sem sessão 302→/login; detail inexistente 404; detail com mock do
  Supabase 200 (badge respondido + Resposta); respostas vazias sem bloco;
  valores R$ corretos; avatar com iniciais; Playwright — dark theme ativo
  (bg #0b0f1a, header sticky), responsividade: KPIs 4 cols → 3 cols (medium) →
  2 cols (mobile), header colapsa <480px (brand-tag some), nav wrap.
- Pendente dono: re-deploy no Render e validar ao vivo a área /cliente
  (logado Google, com pedidos, sem pedidos, suporte, perfil, logout, mobile).

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

