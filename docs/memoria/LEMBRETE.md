# LEMBRETE — próxima sessão (auditoria de segurança documentada + SEO acompanhar GSC)

> Lembrete ativo da sessão anterior. Ao terminar cada item, marque `[x]`.
> Não repetir o que já está marcado.

## ✔ Concluído na reta (25–26/09/2026)

### Portfolio (26/09 — hero profissional)
- [x] **Hero novo no ar**: emblema Crystal Coin (GIF Tibia, flutuação suave)
      no lugar do fogo; ícones SVG no lugar do tofu 🪙 (parágrafo + botão).
      Validado ao vivo via screenshot. (commit portfolio `2ed6357`)

### Estrutura (26/09 — reorg por responsabilidade, fase 1)
- [x] **Nova árvore**: `acesso/` `vendas/` `legal/` `marktrade/` (+`dados/etl/`)
      `tools/` `tests/` (+`e2e/`) `docs/{memoria,audits,runbooks}`
      `integracoes/sheets/`. `bot.py`/`painel.py` seguem na raiz (entry do
      Render). 87 OK + 26 OK após a mudança.
- [ ] **Fase 2 (futura, com dono)**: fatiar `bot.py`/`painel.py` nos contextos
      (validar start command no Render antes); `db/migrations`; renames.

### Segurança (26/09 — auditoria leve de sexta, DOCUMENTAL)
- [x] **Auditoria AppSec estática completa** salva em
      `bapzx/docs/audits/BAPZX_SECURITY_AUDIT_2026-09-26.md`: 15 pontos revisados,
      4 entregas no formato do dono. Críticos 0 / Altos 0 / Médios 2 (M1 CSP
      unsafe-inline, M2 SSRF latente no `_mk_sprite_host`) / Baixos 5 (B1 deps
      sem pin, B2 webhook MP, B3 rate limit em memória, B4 /api/track ~11MB,
      B5 info de versão) / Info 5 (I1 grupos CORS, I2 debug=1, I3 DASHBOARD_KEY
      `==`, I4 fallback storage, I5 state OAuth). Sem alteração de código.
- [ ] **Decidir com o dono**: aplicar fixes M1/M2 + B1–B4 na próxima sessão
      (nomes sugeridos no relatório), ou manter como documentado.

### SEO (iniciativa nova — ver MEMORIA_1.md, LEIA SEMPRE POR PRIMEIRO)
- [x] **MEMORIA_1.md criada** na raiz com as 9 ações de SEO: análise,
      prioridade, como implementar + diagnóstico do site. AGENTS.md agora
      manda lê-la por primeiro. (commits `db9a76f` e `659dac0`)
- [x] **sitemap.xml criado e no ar** (item 8): 10 páginas + os 11 anúncios
      ativos 35–45 (`anuncio.html?id=N`). Confirmado 200 no Pages.
- [x] **robots.txt criado e no ar** (item 4): `Allow: /` + aponta o sitemap.
      Confirmado 200 no Pages. (commit portfolio `bfefdc9`)
- [x] **Keyword por página (item 9) + Auditoria técnica (item 6) FEITOS**:
      meta description em TODAS as 10 páginas (faltavam 6), canonical +
      Open Graph/Twitter em todas, `og-image.png` (1200×630), título dinâmico
      com preço + meta desc dinâmica + schema.org Product/Offer injetado no
      anuncio.html (commits portfolio `c37fc3a` e `0a187e2`). Validado ao
      vivo: "Sanguine Crossbow — 1.350.000 Gold | MARKTRADE — BAPZX".
- [x] **SEO — 8 de 9 itens FEITOS**: 8 sitemap, 4 robots (bfefdc9); 9 keywords,
      6 auditoria (c37fc3a/0a187e2); 1 SC verificado (49f2c41); 5 velocidade
      lazy/dims (ac9ca57); 7 analytics CORS track.js (d0c98c1);
      3 llms.txt (11c8b2f). Site v3.9 (7044aa8).
- [x] **Search Console (item 1) — VERIFICADO + sitemap ACEITO**: meta tag
      `google-site-verification` no index.html (commit `49f2c41`); dono enviou
      o `sitemap.xml` no painel (26/09) — 1ª tentativa deu "não foi possível
      ler" (transitório, CDN ainda propagando), reenvio ACEITO. Arquivo
      validado 200/XML ok simulado Googlebot.
      Opcional: solicitar indexação via Inspeção de URL (index, troca, anuncio).
- [ ] **Acompanhar**: revisar o Search Console ~1 semana após o envio do
      sitemap e registrar ganhos reais (impressões/cliques) no ROADMAP. Se o
      dono quiser GA4 de verdade, precisa criar propriedade (conta Google dele).

### MARKTRADE (26/09 — filtros consertados v2.10.21 + categoria deletada v2.10.22)
- [x] **Filtro de Vocação consertado**: `/api/troca` agora devolve `voc`
      normalizado (`_mk_vocs`: ficha local + fallback Wiki); `troca.html`
      casa por inclusão. Botão "Limpar filtros" do estado vazio consertado;
      `hideOffers` morto removido do restore. Testes 89 OK + coins OK.
- [x] **Categoria do anúncio deletada** (sem uso): fora do POST publicar,
      dos payloads `/api/troca` e `/api/troca/<id>`, dos cards e do detalhe
      (+CSS). Mantidas: categoria da ficha local e do catálogo. 87 OK + 26 OK.
- [ ] **Dono: re-deploy no Render (v2.10.22) + GitHub Pages
      (troca.html/anuncio.html)** e validar ao vivo (chips de Vocação,
      publicar sem categoria, cards/detalhe sem chip).
- [x] **v2.10.20** + Render online: MK_SPRITE_HOST aceita lista
      (cloudinary,supabase), 3 bugs do publicar corrigidos (hidden
      mk_modo_preco=preco_fixo, preço só-números, WhatsApp fora do card).
- [x] **Vitrine real**: 11 anúncios ativos 35–45 (War Hammer destaque + 10
      Sanguine), sprites no Supabase, doações 32–34 deletadas. Validação ao
      vivo da ficha do Sanguine Crossbow (id 41): rótulo "Ataque" + Range + Hit%.
- [x] **UI MARKTRADE no site inteiro**: styles.css v3.8 com tokens do
      MARKTRADE (bg #0b0f1a, borda --border-2, radial, cards/shadows) valendo
      em todo o portfolio; troca/anuncio com :root próprio preservado.
      Testes 85 OK (marketplace) + 26 OK (coins).

### Ações do dono já feitas
- [x] Deploy do Render (v2.10.20 no /health) + envs Cloudinary.

## ⬜ A fazer na próxima sessão (por ordem de importância)

0. [ ] **(se dono aprovar) Aplicar fixes da auditoria de segurança 26/09**:
       M2 allowlist de host + MIME no `_mk_sprite_host`; B1 pin em
       requirements.txt; B2 assinatura no webhook MP; B4 MAX_CONTENT_LENGTH.
       (M1 CSP sem vetor XSS — pode aguardar.)
1. [ ] **Continuousar SEO — Search Console (item 1)** (pedir conta do dono,
       tag de verificação, enviar sitemap). Em seguida item 9 → item 6 (ver
       checklist completo na MEMORIA_1.md — ordem de execução no fim dela).
2. [ ] **Rodapé v3.8 / versão**: conferir se falta sincronizar VERSION do
       portfolio com o padrão "'Portfólio BAPZX · v3.8'".