# BAPZX Tibia Coins Bot â€” MemÃ³ria do projeto

- Onde paramos (11/09, v1.11.3): usuario do GitHub renomeado de lucascristianini1-netizen para bapzxdev a pedido do dono (URL do portfolio agora e https://bapzxdev.github.io/bapzx-portfolio/); PORTFOLIO_URL atualizado no bot, remotes locais dos 3 repos apontam para bapzxdev, referencias em manual.txt/docs/launchers atualizadas (o GitHub redireciona as URLs antigas). Continua tudo da auditoria v1.11.2 (Google Login + Area do Cliente validados ao vivo; XSS do /dashboard corrigido; referer exato no /admin/marcar; sessao 7d + headers de seguranca; TELEGRAM_WEBHOOK_SECRET ativo no Render - webhook so aceita com o header certo). Pendente: publish do app Google antes de clientes reais; itens/prices reais do portfolio (dono vai ajustar); Fase C/1a venda (vetada pelo dono). (dono logou no /admin; pedido de teste id 17 visto em /cliente e /admin e removido; area do cliente lista pedidos do e-mail do login). DEPOIS: auditoria completa de seguranca (a pedido do dono) - sem segredos vazados em nenhum repo; deps sem CVE (Authlib 1.8.0 ja corrige os exploits de 2026, Flask 3.1.3). 4 falhas corrigidas na v1.11.2: (1) XSS no /dashboard (campos do pedido escapados, como nas paginas novas), (2) /admin/marcar compara o host de origem exato via urlparse (antes era substring, dava pra burlar), (3) sessao permanente por 7 dias (PERMANENT_SESSION_LIFETIME 7d + session.permanent) + headers de seguranca (nosniff, DENY, same-origin), (4) webhook do Telegram protegido por TELEGRAM_WEBHOOK_SECRET (X-Telegram-Bot-Api-Secret-Token com compare_digest; setWebhook envia secret_token; sem a env, comportamento antigo). Testes verdes: test_v170 (v1.11.2), test_auth_v111 (+4 checagens novas de seguranca), test_planilha_v180. Pendente: adicionar TELEGRAM_WEBHOOK_SECRET na env do Render + restart; publish do app Google antes de clientes reais; excluir client OAuth velho (desktop); itens/prices reais do portfolio; Fase C/1a venda (vetada pelo dono).

## PROTOCOLO DE REENTRADA (atualizado no último check-out)

- **v2.10.19 (25/09, cascata de hospedagem do sprite: Supabase Storage → Cloudinary → hotlink direto)**: o dono pediu "da pra fazer os 3?" — sim, como cascata. Novo `_mk_sprite_host(url)` em bot.py (chamado no `cliente_troca_publicar` depois do `_mk_itemsprite`): se a env `MK_SPRITE_HOST` for `supabase`, baixa o GIF do Wiki e sobe num bucket público do Supabase (`mk-sprites`, criado via API com SUPA_KEY, público) e devolve a URL `.../storage/v1/object/public/mk-sprites/...`; se for `cloudinary`, baixa e sobe via `image/upload` (não `image/fetch`) exigindo envs `CLOUDINARY_CLOUD_NAME`+`API_KEY`+`API_SECRET` (assinatura SHA-1); senão devolve a URL original do Wiki (hotlink direto). **Nunca derruba** — se o provedor falhar, cai no hotlink. **`_mk_sprite_cdn` de painel.py neutralizado** (pass-through): o Cloudinary `image/fetch` está quebrado (o Wiki devolve 403 para o servidor do Cloudinary; hotlink no navegador funciona — validado 200 no Playwright). A URL final agora é gravada já hospedada no banco. VERSION bot+painel **2.10.19**. Validado ao vivo: bucket `mk-sprites` criado (lista: `itens`, `servicos`, `mk-sprites`); teste real `Mace` → Wiki `.../2/26/Mace.gif` → Supabase `.../public/mk-sprites/mk-sprite-2662771d1acda8d4.gif` (renderizou 32×32 no Playwright em contexto `<img>` real); `War Hammer` → `mk-sprite-db4d715e02a3898c.gif` (content-type `image/gif`, 200); sem env `MK_SPRITE_HOST` devolve a URL original sem baixar. Novos testes em test_marketplace: `test_mk_sprite_host_sem_enum_volta_direto`, `test_mk_sprite_host_supabase_sobe_no_bucket`, `test_mk_sprite_host_supabase_falha_cai_no_direto`, `test_mk_sprite_host_cloudinary_sem_env_cai_no_direto` — **81 OK** (era 77); test_coins **26 OK**; py_compile OK. **Configuração no Render para o dono**: para habilitar Supabase (recomendado, já tem a chave) basta setar `MK_SPRITE_HOST=supabase`; Cloudinary exige as 3 envs acima (aí `MK_SPRITE_HOST=cloudinary`); se não quiser CDN, deixar sem a env (hotlink direto). A env antiga `MK_IMG_CDN_BASE` agora é ignorada (image/fetch falha). Pendências: setar `MK_SPRITE_HOST` no Render + re-deploy (segue v2.10.8) e validar ao vivo com um anúncio novo; dono ainda precisa revalidar o layout da tela de detalhes com item real.

- **25/09 (zeroamento do MARKTRADE + redesign do layout da tela "Detalhes do anúncio")**: a pedido do dono ("remove os testes que já tem zera tudo e os que eu criei tbm pra gente testar"), **zerado o banco do marketplace**: script `%TEMP%\opencode\zera.py` (NÃO versionado) apagou via Supabase REST **12 anúncios** em `marketplace_listings` (ids 1, 12, 22-31 — War Hammer, Sanguine Coil e o lote de testes) e **1 registro** em `marketplace_pagamentos` (id=1 cancelado) — todos DEL → 204. Atenção: a listagem de `marketplace_pagamentos` falhou no 1º script porque a tabela **não tem coluna `item_name`** (400) — refeito com `select=*` e apagado por `id=eq.1`. Depois, **redesign do layout da tela "Detalhes do anúncio"** (`anuncio.html` do portfolio), pedido com briefing de front-end sênior (Tailwind/UI dark gamer): reescrito o CSS estrutural mantendo as classes (o JS `renderizar` não mudou). Card principal `.detail` com borda sutil `rgba(44,61,94,.38)` + sombra `0 12px 36px`; `.d-grid` `330px minmax(0,1fr)` gap 24px (`align-items:start`); **Ficha/item do Wiki agora em 2 colunas simétricas** `.d-grid-kv{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}` (antes `auto-fit minmax(220px)` com bordas inferiores que cruzavam) — cada `.d-row` virou **célula** (flex column, fundo `rgba(24,35,58,.55)`, borda `rgba(44,61,94,.30)`, radius 12, sem linhas tortas/sobrepostas), label `.d-k` uppercase 11px 700, valor `.d-v` semibold; `.d-item-title` etc mantidos; sombras sutis agora em todos os sub-cards (`.d-desc`, `.d-contact-box`, `.d-wiki`, `.d-important`, `.d-share`, `.mini-card` com hover). Responsivo: `max-width:840px` → coluna única com **item antes das infos** (`order:2`/`order:1`); `max-width:560px` → ficha em 1 coluna. Validado ao vivo com servidor stub local (porta 8790 simulando `/api/troca` e `/api/item`, API_BASE reescrita): JS e CSS sintaticamente OK (node --check + chaves balanceadas), página carregou "Royal Crossbow", **13 `.d-row`** renderizadas, grid 2 colunas 242px/242px gap 10px, sombras ativas, sem overflow horizontal (465px em 480px de viewport). Commit pushado: portfolio **`anuncio.html` redesign layout** (bapzxdev/bapzx-portfolio, commit `ceefc5c`; o anterior `46ea453` removeu o "Obtido de"). Pendências: re-deploy no Render (segue v2.10.8, código atual 2.10.18) + env `MK_IMG_CDN_BASE` já definida pelo dono (cloud `a6ncfcm0`) — validar ao vivo após o redeploy se `/api/troca` devolve sprite com prefixo `https://res.cloudinary.com/a6ncfcm0/image/fetch/...`; dono vai publicar um anúncio novo para testar o auto-sprite (base 100% zerada agora); layout da tela de detalhes a conferir com item real.

- **v2.10.18 (25/09, sprite automático do Wiki religado + gatilho Cloudinary + backfill + remoção do "Obtido de")**: plano aprovado pelo dono ("vamos fazer esse plano como numero 1 e deixar engatilhado o cloudinary pra caso haja bloqueios ok?"). **(1) Auto-GIF no POST**: em `cliente_troca_publicar` (bot.py:3521) quando `sprite` vem vazio agora chama `_mk_itemsprite(item_name)` automaticamente e grava o GIF oficial do TibiaWiki (a ponte `_mk_itemsprite`, bot.py:638, já existia e voltou a ser chamada). **(2) Cloudinary engatilhado**: novo `_mk_sprite_cdn()` (painel.py:3258) — se a env `MK_IMG_CDN_BASE` estiver definida (ex.: `https://res.cloudinary.com/<cloud>`) reescreve o sprite para `<base>/image/fetch/<url>` na API `/api/troca` (painel.py:3228) e `/api/troca/<id>` (painel.py:3470); sem a env, devolve a URL original do Wiki (sem chave no código; nenhum segredo versionado). **(3) Backfill**: script `_mk_backfill_sprites.py` (NÃO versionado) varreu ativas/pendentes sem sprite, resolveu via `_mk_itemsprite` e atualizou no Supabase — 1 anúncio corrigido (id=30 Demon Shield); Total 9, 8 já tinham sprite. **(4) "Obtido de" removido**: em `anuncio.html` (portfolio) a etiqueta `["drop","Obtido de"]` saiu de `fichaLocalBlock`, e a Ficha do item agora mostra só dados do item (sem monstros que dropam). VERSION bot+painel **2.10.18**. Validado: py_compile OK; test_marketplace **77 OK** (novos testes `test_publicar_sprite_vazio_busca_auto_e_grava` e `test_publicar_sprite_do_form_tem_prioridade`); test_coins **26 OK**; `_mk_itemsprite` ao vivo resolveu Mace/Axe/Demon Helmet/War Hammer/Golden Helmet/Royal Crossbow ("Poção Mágica" → "" como esperado); `_mk_sprite_cdn` sem env devolve URL normal; node --check JS troca.html + anuncio.html OK (extração de script inline). Commits pushados: bapzx **v2.10.18**, portfolio **anuncio.html (sem "Obtido de")**. Pendência: re-deploy no Render (segue v2.10.8, 10 versões atrás) + GitHub Pages; se o Wiki bloquear hotlink, basta setar `MK_IMG_CDN_BASE` no Render que o Cloudinary assume os sprites automaticamente.

- **v2.10.17 (25/09, página inteira do MARKTRADE no padrão premium)**: a pedido do dono ("consegue aplicar na página inteira do marktrade? ... deixa o publicar um pouco menor"), apliquei a estética v2.10.16 para **toda a página /cliente/troca** via novo `_MK_PAGE_CSS` (bot.py, injetado no body antes do welcome): `.welcome` (borda dourada + fundo navy + sombra, h2 com glow esmeralda), `.kpi` (fundo navy-escuro, borda dourada sutil, radius 16, sombra, glow no número, base metálica), `.panel` (fundo navy-escuro, borda dourada sutil, radius 18, sombra profunda), botões `.welcome .btn` e `.panel-hd a.btn` (incluindo o "Renovar/Assinar" que é `ghost small` — regra `.panel-hd a.btn.ghost.small` por especificidade) agora com **gradiente esmeralda→ciano texto branco** (espinha do botão new), `.table-wrap`/`th` com borda dourada sutil. Botão **"Publicar agora" (.mk-publish-btn) reduzido**: font 15px (era 16), padding 12x16 (era 14x18), radius 11 — "um pouco menor", como pedido. VERSION bot+painel **2.10.17**. Validado: py_compile OK; test_marketplace **75 OK** + test_coins **26 OK**; página renderizada no navegador (servidor http local) e estilos conferidos via getComputedStyle: welcome/kpi/panel com borda dourada + fundo gradiente navy + sombra, botões público + renovar + publicar com gradiente esmeralda→ciano e texto branco. Commits pushados: bapzx **v2.10.17**. Pendência: re-deploy no Render (segue v2.10.8, 9 versões atrás) + GitHub Pages; validar ao vivo.

- **v2.10.16 (25/09, card "Destacar meu anúncio" premium + botão "Publicar agora" com gradiente)**: pedido do dono com descrição de UI (ref. image_0.png, arquivo não encontrado no PC — seguido a descrição). `_MK_FORM_CSS` (bot.py): card `.mk-destaque-box` virou premium — cantos 16px, **borda metálica dourada sutil** `rgba(212,175,55,.30)` (intensifica p/ .75 + glow dourado em `:checked`), fundo gradiente escuro `#18233a→#101a2c`, sombra projetada; **checkbox circular customizado** (input escondido + `.mk-destaque-dot` 22px círculo) que ao marcar preenche com **gradiente verde→ciano** (`#34d399→#22d3ee`) + glow e exibe **✓ branco** no centro via `::after`; **estrela dourada SVG** (`#fbbf24`) com `drop-shadow` dourado (substitui o emoji ⭐); título "Destacar meu anúncio" branco puro em Sora 700; preço `(+ R$ X)` **verde neon** (`#4ade80` 800); nota de descrição em cinza `--muted`; layout espaçoso (padding 16x18, gap 14). Botão submit ganhou **`.mk-publish-btn`**: largura 100%, gradiente rico **verde esmeralda→ciano** (`#059669→#10b981→#06b6d4`), **texto branco** bold 16px Sora, radius 12, sombra colorida `rgba(5,150,105,.35)`. HTML do bloco destaque reestruturado: `<label>` c/ input + `.mk-destaque-box` (dot + star svg + txt titulo/preço/nota). VERSION bot+painel **2.10.16**. Validado: py_compile OK; test_marketplace **75 OK** + test_coins **26 OK**; página renderizada com mocks e aberta no navegador — estilos conferidos via getComputedStyle (card, botão gradiente+branco, dot gradiente no `:checked`, ✓ opacity 1, borda dourada + glow). Commits pushados: bapzx **v2.10.16** (card + botão). Pendência: re-deploy no Render (v2.10.8 → 2.10.16, 8 versões atrás) + GitHub Pages.

- **v2.10.15 (25/09, vitrine e Publicar anúncio sem categoria e sem URL de imagem)**: a pedido do dono, **(1)** removido o **filtro "Categoria"** da vitrine (`troca.html` do portfolio): seção de chips `icat` (Soul Core, Make Believe, Rares, Primal Ordeal, Fansite, Soul War, Rotten Blood) apagada + toda a lógica JS `icat` removida (`contarFiltros`, `restoreState` sem a chave, `applyFilters` só `["tipo","voc"]`, `syncChips` sem branch, `setFilter` sem multi-select); **(2)** no **formulário Publicar anúncio** (bot.py `/cliente/troca`) removido o `<select name='category'>` (Automático/7 categorias) e o campo **"URL da imagem do item (opcional)"** (`name='sprite'`); nota do item simplificada (só padroniza nome). Não alterado (decisão): o POST continua lendo `category`/`sprite` do form (vazios → auto-detect de categoria no Wiki segue rodando em silêncio; sprite vai "") e o chip de categoria do card/detalhe segue no ar (anúncios antigos ainda exibem). VERSION bot+painel **2.10.15**. Validado: py_compile OK; test_marketplace **75 OK** (test_cliente_troca_renderiza ajustado: sem `name='category'`, sem "Automático (Wiki Tibia)", sem `name='sprite'`/URL, sem "Wiki Tibia"); test_coins **26 OK**; node --check JS troca.html OK. Commits pushados: bapzx **v2.10.15**, portfolio **troca.html sem filtro categoria**. Pendência: re-deploy no Render (ainda v2.10.8/6 versões atrás... na verdade v2.10.14 também está no bapzx, Render segue v2.10.8) + GitHub Pages e validar ao vivo filtros sem categoria e publicar sem campo de imagem.

- **v2.10.14 (25/09, distância + punhos no banco local e Publicar anúncio sem
  ficha)**: **(1)** adicionadas ao banco local `mk_itens.py` as **armas de
  distância** (18 Armas de Arremesso + 28 Bestas + 36 Arcos, categorias novas
  "Armas de Arremesso"/"Bestas"/"Arcos" no schema de 15 campos: extras
  `maos`/`alcance`/`hit`) e os **punhos** (36 itens, categoria "Armas",
  formato combat weapon com extras `maos`/`def`/`mod_def`). TSVs transcritos
  em `C:\Users\BapszX\AppData\Local\Temp\opencode\` (arremesso.tsv, bestas.tsv,
  arcos.tsv, punhos.tsv). Gerador `_mk_gera_capacetes.py` com `TSV_ARMAS_DIST`
  + `parse_distancia_tsv`; `linha()` grava SEMPRE os 3 extras das armas para
  não deslocar índices. `mk_itens.py` agora com **1169 itens** (522 armas).
  Rótulos dinâmicos no bot.py (`rotuloDano`) e painel `_ficha_local` cobrem as
  categorias novas: distância → rótulo "Ataque" (campo 6) + linhas "Mãos"/
  "Alcance"/"Hit%"; combate → "Dano Médio"; painel `_ficha_local` usa extras
  `maos/alcance/hit` quando distância, senão `maos/def/mod_def`. Zero
  divergências na transcrição das 4 seções (18/18, 28/28, 36/36, 36/36).
  **(2)** a pedido do dono, removido o **card de detalhes (`mk-pub-ficha`)** do
  formulário Publicar anúncio (`/cliente/troca`): o autocomplete de nomes
  continua (dropdown `mk-pub-ac-drop`), mas ao aplicar o item agora só preenche
  o campo `item_name` — o CSS `.mk-pub-ficha` (9 linhas) e o bloco de
  renderização da ficha (`rotuloDano` + linhas + `ficha.innerHTML`) foram
  removidos de `_MK_AC_CSS`/`_MK_AC_SCRIPT` (bot.py). **(3)** os **8 anúncios
  de teste (ids 14-21)** foram removidos do Supabase e **8 novos (ids 22-29)**
  criados via script `_mk_renova_8.py` (NÃO versionar) com itens da base local
  para validar a ficha no Detalhes: War Hammer (Dano Médio 45), Cobra Crossbow
  (Ataque +7), Royal Star (Ataque 64), Amazon Helmet (Armadura 7), Demon
  Shield (Defesa 46, troca/destaque), Worn Soft Boots (destaque), Black
  Candle (Fetiches), Spellbook of Enlightenment (Defesa 29). VERSION bot.py e
  painel.py **2.10.14**. Validado: py_compile OK; script `_mk_renova_8.py`
  removeu 14-21 (204) e criou 22-29; listagem confirmada (10 rows: 2 encerradas
  + 8 ativas novas); ficha local confirmada para os 8 itens; test_marketplace
  + test_coins **101 OK**. Pendência: re-deploy no Render (ainda em v2.10.8,
  agora 6 versões atrás) + GitHub Pages, validar ao vivo autocomplete sem
  ficha e a ficha local dos 8 anúncios novos no Detalhes.

- **v2.10.12 (24/09, todas as categorias do envio: pernas, spellbooks, botas,
  aljavas e fetiches no banco local)**: coladas as 4 seções restantes do envio
  do dono e transcritas nos módulos gitignored `_mk_pernas_dados.py` (66
  pernas), `_mk_spellbooks_dados.py` (30), `_mk_botas_dados.py` (66),
  `_mk_aljavas_dados.py` (8) e `_mk_fetiches_dados.py` (76). `mk_itens.py`
  agora com **701 itens** (54 armas + 151 capacetes + 165 armaduras + 85
  escudos + 66 pernas + 30 spellbooks + 66 botas + 8 aljavas + 76 fetiches),
  schema de 12 campos com `categoria` completa. Gerador
  `_mk_gera_capacetes.py` ganhou as 5 categorias novas e o merge de fetiches
  (`_fk_bonus`: Bônus vence; se "Nenhum."/"Nenhum"/"" usa Atributos; se ambos
  none, vazio). Layout por categoria (decisão): pernas/botas `arm`→dano_medio
  (rótulo Armadura) + tier; spellbooks `def`→dano_medio (rótulo Defesa), sem
  tier; aljavas `volume`→dano_medio (rótulo Volume), sem slots/tier; fetiches
  nivel "0", vocação "Todas", sem dano_medio/slots/tier, bonus = Atributos
  quando Bônus none. Rótulo dinâmico do bot.py e do anuncio.html já cobria
  todos (Spellbooks→Defesa, Aljavas→Volume, demais→Armadura) — sem mudança de
  JS. Casos especiais mantidos: Boots of Waterwalking/Pair of Soft Boots/Worn
  Soft Boots com arm vazio; Cursed Coin bonus vazio; Torch com "Pirate Gunner"
  duplicado no drop; Pumpkinhead peso "(apagada) 9.50 oz - (acesa) 12.50".
  VERSION bot.py e painel.py **2.10.12**. Validado: py_compile OK; node
  --check no JS (bot + anuncio) OK; rótulos conferidos fim-a-fim via node (6
  casos: Pernas→Armadura, Spellbooks→Defesa, Aljavas→Volume, Botas→Armadura,
  Fetiches→Armadura, Escudos→Defesa); test_marketplace **74 OK** (+7: schema
  12 campos com as 9 categorias e total 701, perna, botas, botas sem arm,
  spellbook, aljava, fetiche com bonus de Atributos, fetiche sem bonus);
  test_coins **26 OK** (100 total). Pendência: re-deploy no Render + GitHub
  Pages (Render ainda em v2.10.8 — agora 4 versões atrás: 2.10.9, 2.10.10,
  2.10.11 e 2.10.12) e validar ao vivo o autocomplete/ficha das novas
  categorias (ex.: "spellbook" → Defesa 23, "quiver" → Volume 6, "fabulous" →
  Fabulous Legs Armadura 9).

+ - **v2.10.11 (24/09, escudos + schema de 12 campos com categoria)**: a pedido
  do dono, adicionados os **85 escudos** colados por ele ao banco local —
  `mk_itens.py` agora com **455 itens** (54 armas + 151 capacetes + 165
  armaduras + 85 escudos). Dados em `_mk_escudos_dados.py` (gitignored,
  transcritos do envio com slots/def/bonus/protecao/peso/drop; as **8 aljavas**
  listadas junto na seção de escudos foram deixadas de fora e entram pelo
  módulo de aljavas quando o dono mandar a seção). **Schema novo de 12
  campos**: `[nome, nivel, vocacao, tipo_dano, bonus, protecao, dano_medio,
  slots, tier, peso, drop, categoria]` — toda a base ganhou a coluna
  `categoria` ("Armas", "Capacetes", "Armaduras", "Escudos"). Rótulo dinâmico
  do `dano_medio` agora decide por **categoria**: Armas→"Dano Médio",
  Escudos/Spellbooks→"Defesa", Aljavas→"Volume", demais→"Armadura".
  Escudos: `tipo_dano=""`, `dano_medio`=Def (rótulo "Defesa"), `tier=""`.
  Código: `painel._ficha_local` campos +"categoria"; `bot.py` `_MK_AC_SCRIPT`
  `rotuloDano(it)` (com fallback legado por tipo_dano); `anuncio.html`
  (portfolio) `rotuloDano(ficha)` no bloco da ficha local. Gerador
  `_mk_gera_capacetes.py` atualizado (categoria no dict, armas do HEAD com 11
  ou 12 campos, filtro por categoria, contadores no cabeçalho). VERSION
  bot.py e painel.py **2.10.11**. Validado: py_compile OK; node --check no JS
  (bot + anuncio); test_marketplace **67 OK** (+3: test_ficha_local_escudo
  Demon Shield = "Defesa" 46, test_ficha_local_escudo_sem_def Adamant Shield,
  test_db_itens_schema_12_campos_sem_duplicados); test_coins **26 OK** (93
  total). Rótulos conferidos fim-a-fim via node com dados reais (Demon
  Shield→Defesa 46, Amazon Armor→Armadura 13, Hailstorm Rod→Dano Médio 65,
  Adamant Shield→Defesa vazio). Pendência: re-deploy no Render + GitHub Pages
  (Render ainda em v2.10.8, 3 versões atrás); **aguardando o dono colar as
  demais seções do envio (pernas, spellbooks, botas, aljavas, fetiches)**
  para as próximas categorias.

+- **v2.10.10 (24/09, armaduras no banco local)**: adicionadas as **165
+  armaduras** que o dono colou (`_mk_armas_dados.py`, gitignored — transcritas
+  do envio com arm/slots/tier/peso; sem coluna de sprite). Gerador
+  `_mk_gera_capacetes.py` agora lê as **54 armas do HEAD** (itens com
+  `tier=""`, pois capacetes/armaduras têm tier preenchido) + **151 capacetes**
+  do TSV + **165 armaduras** do módulo de dados. `mk_itens.py` reescrito com
+  **370 itens** (schema novo idêntico ao anterior: armas `tipo_dano`=elemento,
+  `dano_medio`=atk; capacetes/armaduras `tipo_dano=""`, `dano_medio`=Arm,
+  rótulo dinâmico "Armadura"). Caso especial mantido: Spectral Dress com `arm`
+  vazio (ficha mostra campo vazio). Nenhuma mudança de código/UI necessária
+  (lógica de rótulos já era dinâmica desde v2.10.9). Novos testes
+  `test_ficha_local_armadura` e `test_ficha_local_armadura_sem_arm`.
+  VERSION bot.py e painel.py **2.10.10**. Validado: py_compile OK;
+  test_marketplace **64 OK**; test_coins **26 OK** (90 total). Pendência:
+  re-deploy no Render e no GitHub Pages (Render ainda em v2.10.8); validar ao
+  vivo autocomplete em armadura (ex.: "amazon armor" → Armadura 13).
+
 - **v2.10.9 (24/09, capacetes + schema unificado "nome level voc tipo de dano
  bonus protecao dano medio slots tier peso dropa de")**: a pedido do dono, o
  banco local `mk_itens.py` foi alinhado ao schema que ele usará: agora
  **205 itens** (54 armas Rods/Wands + 151 capacetes). Schema novo por item:
  `[nome, nivel, vocacao, tipo_dano, bonus, protecao, dano_medio, slots,
  tier, peso, drop]` (`def` foi REMOVIDO; `tier` entrou; `elemento`→`tipo_dano`,
  `resistencia`→`protecao`, `atk`→`dano_medio`). **Capacetes**: `tipo_dano=""`
  e o campo `dano_medio` guarda o **Arm** (rótulo dinâmico "Armadura"); armas
  mantêm atk (rótulo "Dano Médio"). Sem coluna de sprite (decisão do dono).
  Geração via `_mk_gera_capacetes.py` (gitignored) a partir do TSV transcrito
  da lista que o dono colou (`C:\Users\BapszX\AppData\Local\Temp\opencode\
  capacetes.tsv`; corrigido typo "Nigém."→"Ninguém." e Demon Helmet lvl 3→0).
  Botões: `painel._ficha_local` campos atualizados; `bot.py` `_MK_AC_SCRIPT`
  (ficha no Publicar anúncio) com novos labels + tema dinâmico Dano Médio/
  Armadura e Tier; `anuncio.html` (portfolio) `mapLbl`→etiq. dinâmica
  (tipo_dano vazio ⇒ "Armadura"). VERSION bot.py e painel.py **2.10.9**.
  Validado: py_compile OK; test_marketplace **62 OK** (+1 test_ficha_local_
  capacete); test_coins **26 OK**. Pendência: re-deploy no Render e no GitHub
  Pages; validar ao vivo autocomplete em capacete (ex.: "amazon" → Armadura 7).

- **v2.10.8 (24/09, autocomplete de itens + ficha local no detalhe)**: a
  pedido do dono, o campo "Item *" do formulário de Publicar anúncio
  (`/cliente/troca`, form POST `/cliente/troca/publicar`) ganhou
  **autocomplete + ficha do item** a partir de um banco de itens local. Novo
  módulo **`mk_itens.py`** com `_MK_ITENS_DB` (54 itens: 14 Rods + 40 Wands,
  campos nome/nivel/vocacao/elemento/bonus/resistencia/atk/def/slots/peso/drop);
  o `bot.py` importa e injeta via `_MK_ITENS_JSON` (json.dumps) no
  `_MK_AC_SCRIPT` (JS inline com dropdown filtrado, navegação por
  setas/Enter/Escape, ficha com Nível/Vocação/Elemento/Bônus/Resistência/
  Ataque/Defesa/Slots/Peso/Obtido de). O campo `item_name` virou
  `id='item_name'` + `autocomplete='off'`; CSS `_MK_AC_CSS` (`.mk-pub-ac`,
  `.mk-pub-ac-drop`, `.mk-pub-ficha`). Corrigido no JS o índice da lista
  filtrada vs. array completo (data-i). **O autocomplete é SÓ no Publicar
  anúncio** — o `troca.html` do portfólio foi REVERTIDO para o estado anterior
  (busca sem dropdown/ficha). **Ficha local no Detalhes do anúncio**: o
  `painel.py` ganhou `import unicodedata`, `from mk_itens import _MK_ITENS_DB`
  e `_ficha_local(nome)` (normalização sem acentos; dict stringificado ou
  `None`); GET `/api/item` devolve `ficha_local`; GET `/api/troca/<id>` inclui
  `ficha_local` no payload. `anuncio.html` renderiza a seção "Ficha do item —
  Dados da nossa base de itens" (Nível/Vocação/Elemento/Bônus/Resistência/
  Ataque/Defesa/Slots/Peso/Obtido de) antes da ficha do Wiki. Testado ao vivo
  (sangui → Sanguine Coil Nv 600 Sorcerers; hail → Hailstorm Rod Nv 33 Druids)
  e detalhe mock id=99 renderiza ficha local completa no navegador.
  VERSION bot.py e painel.py **2.10.8**. py_compile OK; test_marketplace **61
  OK**; test_coins **26 OK**. Pendência: deploy no Render.

- **v2.10.5 (23/09, página de detalhes do anúncio + info do item via Wiki)**: a pedido do dono, clicar em um anúncio na listagem agora abre uma **página de detalhes dinâmica** `anuncio.html` (novo, no portfolio) — novas rotas públicas no painel.py: **GET `/api/troca/<id>`** (anúncio individual com `status` incluído, usa `_fetch_public` com `id=eq.<id>&status=eq.ativa` `range_="0-0"`; 404 + CORS se não achar) e **GET `/api/item?nome=`** (cache 2min) que devolve `info` (tier/nível/vocação/armor/peso/imbuement/resistências/atributos/classificação/vende para/compra de/tipo_item via `parse` + `redirects=1` + parse da `{{Infobox_Item` no TibiaWiki server-side, limpeza de wikilinks via `_limpa_wiki`; retry com UA neutro em 403/429) e `referencia` (min/max/média/quantidade/última data calculado dos **anúncios ativos do mesmo item** no próprio marketplace via `ilike.*nome*` — nunca inventa preço; `None` sem dados). `troca.html`: cards viraram `<a href="anuncio.html?id=...">` (mantendo badge VIP/estilo; `a` com `text-decoration:none`), e **filtros persistidos em `sessionStorage`** (STORAGE_KEY `marktrade-filtros`, `saveState`/`restoreState` + `syncChips()` ao carregar) para o usuário voltar do detalhe com a lista como deixou. `anuncio.html`: visual dark igual troca.html, botão "← Voltar para os anúncios" no padrão do site, trata loading/erro/id inválido/404, mostra preço/ofertas, mundo, anunciante (verificado), contato, descrição, seção "Sobre o item" (ficha do Wiki) e "Preço de referência" (histórico dos anúncios do mesmo item); `status` "Ativo/Vendido/Expirado" com emoji; título da aba dinâmico. Testes: **+10 novos** em test_marketplace (api_troca detalhe encontrado/não encontrado/rate-limit/CORS origem fora, api_item sem nome/com info, iteminfo parseia infobox/sem tier/falha+vazio, ref_de_preco média/vazio). VERSION painel.py **2.10.5** (bot.py permanece 2.10.4 — sem mudança funcional no bot). py_compile OK; test_marketplace **56 OK**; test_coins **26 OK**; JS check troca.html + anuncio.html OK; navegador mock validado de ponta a ponta (listagem → filtro Soul Core → clique no card → detalhe com tier/atributos/preço referência → voltar → filtro restaurado; id inválido e 404 tratados). **Próximo passo (dono): re-deploy no Render (verde, v2.10.5 no /health) e validar ao vivo: clicar num anúncio real → página de detalhes com foto/atributos/preço de referência; usar o "Voltar" e confirmar filtros preservados.**

- **v2.10.4-dados (23/09, troca.html dark + VIP no topo)**: página `troca.html` do
  portfolio reescrita seguindo o padrão visual dark da Área do Cliente (tokens
  do AUTH_LAYOUT do bot.py: --bg #0b0f1a, --panel #111a2c, etc.), com menu
  lateral de filtros à esquerda (Categoria Item/House, Hide taking offers como
  única opção switch do topo, Mundo 16 mundos, Tipo de anúncio Venda/Compra,
  Categoria do item 7 categorias, Vocação 5 vocações, Tier 0–10; **removidos
  por pedido do dono**: Tipo de PvP, Continente e BattlEye; filtros ficaram
  sempre abertos com balões de 2 em 2 (sem accordion) que filtram na hora ao
  clicar), anúncios VIP no topo (badge ⭐ fora do título? não: badge em flow
  acima do tipo/data, não sobrepõe mais a data; header "Destaques (VIP)" e
  barra "Anúncios recentes" com a mesma estrutura; preço com símbolo de moeda
  do jogo 💰 gold coins), contador de anúncios, estados loading/erro/vazio e
  drawer de filtros no mobile. Filtros sem campo no payload (/api/troca só
  tem aceita_ofertas, world, tipo, preço, história) ficam como UI por enquanto
  (filtram para vazio quando ativos) até o backend prover os campos. VERSION
  bot+painel **2.10.3** (v2.10.4 sem bump de versão, só dados). 66 testes OK
  (marketplace+coins), py_compile OK, JS check OK.
  Commits: portfolio `ca7a808`+`97aa254`+`08c784d`+`513f387`, bot `dd8b964`
  (todos pushados). Render já re-deployado — /api/troca retorna is_destaque e
  2 anúncios (WAR AXE, war hammer) exibidos como VIP ao vivo.

- **v2.10.3 (23/09, data/hora BR no MARKTRADE)**: coluna "Publicado" de
  "Meus anúncios" (bot.py `cliente_troca`) agora usa `_mk_fmt_dt` (dd/mm/aaaa
  hh:mm) e a listagem de pagamentos do painel usa `_fmt_dt_amigavel`. Ambos
  convertem UTC->America/Sao_Paulo com fallback fixo UTC-3 (ZoneInfo
  "America/Sao_Paulo" falha no Windows sem o pacote `tzdata`; fallback evita
  mostrar a hora crua). ⚠ NÃO usar `Set-Content`/`Out-File` para editar
  .py com acentos: corrompe encoding (BOM+mojibake). Sempre usar Edit tool.
  VERSION bot+painel **2.10.3**. py_compile OK; test_marketplace **40 OK**;
  test_coins **26 OK**. **Próximo passo (dono): re-deploy no Render (v2.10.3
  no /health) e testar ao vivo: publicar sem QR (modo teste do dono, email
  MASTER) + conferir data/hora dd/mm/aaaa hh:mm.**

- **v2.10.2 (23/09, modo teste do dono no MARKTRADE)**: quando o e-mail logado
  está em `MASTER_EMAILS` (fallback `ADMIN_EMAILS`; dono =
  lucascristianini1@gmail.com), a área do cliente **não gera Pix/QR**: publicar
  anúncio ativa direto (status `ativa`, destaque/`destaque_until` se marcado,
  via PATCH no Supabase) e assinar VIP grava `profiles.vip_until` direto (+
  invalida `_MK_VIP_CACHE`), ambos com flash "modo teste do dono — publicado/
  ativado sem cobrança". Clientes normais continuam no fluxo PIX (PUB-/DES-/
  VIP-). Aviso âmbar "modo teste do dono" no topo de `/cliente/troca` e
  `/cliente/troca/vip` quando MASTER. VERSION bot+painel **2.10.2**. Testes:
  test_marketplace.py **40 OK** (novos: publicar MASTER ativa direto sem QR;
  com destaque; VIP MASTER sem QR) e test_coins.py **26 OK**; py_compile OK.
  **Próximo passo (dono): rodar local ou re-deploy no Render (v2.10.2) e
  testar ao vivo com o e-mail MASTER.**

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

