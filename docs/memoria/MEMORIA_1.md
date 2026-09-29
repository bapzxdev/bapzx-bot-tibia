# MEMORIA_1 — SEO / Visibilidade do BAPZX (LEIA SEMPRE POR PRIMEIRO)

> **Regra fixa**: em TODA sessão, esta memória é a **PRIMEIRA** a ser lida
> (antes de MEMORIA.md do projeto e dos protocolos continuidade). Criada em
> 25/09/2026 como parte da iniciativa de SEO do site.
> Conteúdo: as 9 ações de SEO que o dono quer no BAPZX, com análise de
> relevância real para o negócio e plano de implementação.

---

## CONTEXTO DA PLATAFORMA (fatos que pesam nas decisões)

- **Site público** = site estático **GitHub Pages** `bapzx-portfolio`
  (URL: `bapzxdev.github.io/bapzx-portfolio/`). Sem domínio próprio ainda.
- **Bot/painel** = Flask no **Render** (`bapzx-bot-tibia.onrender.com`):
  login da loja, APIs /api/troca*, /api/item, páginas legais.
- **MARKTRADE** = marketplace integrado (troca.html + anuncio.html + APIs do
  Render). Anúncios: tabela `marketplace_listings` no Supabase.
- **Tráfego hoje**: esforçado em grupos, não orgânico. SEO é novo front.
- **IDs ativos no marketplace**: 35 (War Hammer, destaque) + 36–45 (Sanguine).
- **track.js** envia visita ao Render quase em tempo real (fetch keepalive,
  credentials omit — CORS corrigido em 26/09).

### Diagnóstico rápido do site (já conferido em 25/09/2026)

| Página | `<title>` | meta description | comentário |
|---|---|---|---|
| index.html | ✅ | ✅ | ok |
| rubini.html | ✅ | ❌ | falha |
| service.html | ✅ | ❌ | falha |
| itens.html | ✅ | ✅ | ok |
| grupos.html | ✅ | ✅ | ok |
| faq.html | ✅ | ❌ | falha |
| contato.html | ✅ | ❌ | falha |
| como-comprar.html | ✅ | ❌ | falha |
| troca.html | ✅ | ✅ | ok |
| anuncio.html | ✅ (genérico) | ✅ (genérico) | precisa título dinâmico via JS |

- **Não existem**: robots.txt, sitemap.xml, canonical, Open Graph, schema
  Product/Offer, llms.txt.
- **Velocidade**: site estático no GitHub Pages (CDN rápida); peso vem do
  Google Fonts + sprites GIF.

---

## AS 9 AÇÕES — ANÁLISE, PRIORIDADE E COMO FAZER NO BAPZX

Legenda relevância: 🔥 enorme para este negócio · ⭐ média · ☝️ baixa/nicho.
Prioridade de execução 1 a 9 (1 = primeiro).

### 1. Google Search Console ⭐ → 🔥 (PRIORIDADE 2)
- **O que é**: serviço gratuito do Google que mostra como o site aparece na
  busca, erros de indexação, quais queries trazem clique e pede reindexação.
- **Relevância**: é o cérebro de todo SEO. Sem ele, você trabalha no escuro.
- **Como implementar**:
  1. Criar conta em https://search.google.com/search-console → "Adicionar
     propriedade" com o **URL do GitHub Pages** (não é preciso domínio).
  2. Verificação por **tag HTML**: inserir a meta `google-site-verification`
     no `<head>` do `index.html`, ou por DNS TXT (GitHub Pages bloqueia DNS
     só para domínio próprio; tag é mais simples).
  3. Enviar o `sitemap.xml` (item 8).
  4. Pedir "Inspecionar URL" da home e das principais para forçar indexação.
- **Esforço**: 20–30 min, 100% gratuito.

### 2. Google Meu Negócio (Business Profile) ☝️ (PRIORIDADE 9 — ADIAR)
- **O que é**: o perfil que aparece no Google Maps/pesquisa local, com
  endereço, horário, avaliações.
- **Relevância p/ BAPZX**: 🔴 **Baixa** — só faz sentido para negócio com
  endereço/atendimento presencial. A BAPZX é 100% online (Telegram, WhatsApp),
  sem CNPJ/local físico; o Google exige endereço verificável e pode recusar
  ou suspender. Vender moeda virtual de jogo também esbarra em política do
  Google. Pior custo/benefício de todas as 9.
- **Recomendação**: NÃO implementar agora. Voltamos a avaliar se existir
  endereço físico/CNPJ. Registrar como pendência avaliável.

### 3. llms.txt ☝️ (PRIORIDADE 7 — rápido)
- **O que é**: arquivo (site.com/llms.txt) que descreve o site em texto
  simples para **chatbots/LLMs** (ChatGPT, Claude, Gemini) entenderem o
  negócio — novo padrão, sem consenso oficial.
- **Relevância**: hoje o tráfego por busca em LLM é mínimo e instável;
  a maioria dos crawlers ainda ignora. Mas o custo é ~5 min: cria valor e
  não atrapalha.
- **Como implementar**: criar `llms.txt` na raiz do GitHub Pages com visão
  geral (o que a BAPZX vende, como comprar, contato) e links para as páginas
  principais. Sem segredos (é público).
- **Esforço**: 5 min.

### 4. robots.txt ⭐ → 🔥 (PRIORIDADE 4)
- **O que é**: instruções de crawl para o Google/Bing. GitHub Pages **serve
  robots.txt se existir na raiz** (não por default).
- **Relevância**: essencial para "higiene": evita indexar páginas internas do
  Render (`/admin`, `/login`, APIs) e concentra o crawl no que importa.
- **Como implementar** (`robots.txt` na raiz do portfolio):
  ```
  User-agent: *
  Allow: /
  Disallow: /admin
  Disallow: /login
  Sitemap: https://bapzxdev.github.io/bapzx-portfolio/sitemap.xml
  ```
  Observação: `Disallow` em `/admin`/`/login` só funciona se estes pertencerem
  ao Render (não ao GitHub Pages). Como são domínios diferentes, o ideal é
  também servir robots.txt no Render bloqueando `/admin` e `/login`.
- **Esforço**: 10 min.

### 5. Testar velocidade do site ⭐ (PRIORIDADE 3)
- **O que é**: medir com Lighthouse/PageSpeed bottom e otimizar.
- **Relevância**: é sinal de ranqueamento e decisão de compra. Site estático
  no GitHub Pages já é rápido; o que pesa é **Google Fonts** (request extra
  bloqueante) e sprites grandes.
- **Como implementar**:
  1. Rodar PageSpeed Insights na home E nas de produto (troca.html/anuncio).
  2. Ações baratas: `font-display:swap`, `preconnect` para
     `fonts.googleapis.com`/`fonts.gstatic.com`, lazy-load dos sprites
     (`loading="lazy"`), definir width/height das imagens.
- **Esforço**: 30 min + ajustes.

### 6. Website SEO checker / auditoria técnica + títulos ⭐ → 🔥 (PRIORIDADE 1)
- **O que é**: auditoria técnica completa (erros de tags, headings, mobile,
  metas, canonical, Open Graph, schema).
- **Relevância**: é o fundamento — corrige o que impede a indexação e libera
  o potencial das outras 8. **Títulos já existem em todas as páginas** (menos
  a tarefa de torná-los dinâmicos), então o checklist atual é:
- **Checklist para executar**:
  - [ ] meta description faltando em **6 páginas**: rubini, service, faq,
        contato, como-comprar (ver tabela acima) — escrever uma linha única
        de 150–160 chars com a keyword (item 9).
  - [ ] `canonical` em todas as páginas (aponta para a própria URL sem
        query) — evita conteúdo duplicado com `?id=` do anuncio.
  - [ ] **Open Graph + Twitter cards** (título, descrição, imagem) — faz o
        link renderizar bem no WhatsApp/Discord/Telegram (o MARKTRADE já é
        compartilhado nesses apps!).
  - [ ] **Schema.org** `ItemList`/`Product`/`Offer` no marketplace: o anúncio
        (troca.html e anuncio.html) ganha rich results de preço/produto. Isso
        é o que diferencia o MARKTRADE no Google.
  - [ ] Título dinâmico no `anuncio.html`: hoje é genérico ("Anúncio —
        MARKTRADE — BAPZX"); setar `document.title = <Nome do item> + " — " +
        <preço formatado> + " | MARKTRADE BAPZX"` após o fetch da API.
  - [ ] `h1` único por página; hierarquia h2/h3 limpa (conferir).
  - [ ] `alt`/`aria-label` nos sprites e imagens.
- **Esforço**: 1–2h; é a maior alavanca.

### 7. Google Analytics (GA4) ⭐ (PRIORIDADE 5)
- **O que é**: medição de tráfego (origem, páginas, conversão).
- **Relevância**: já existe `track.js` próprio (visita → Render), mas GA4 é
  padrão do mercado, mostra origem/SEO e acompanha conversão. Com LGPD
  brasileira, precisa de aviso de cookies/consentimento (ver /privacidade).
- **Como implementar** (se não quiser depender do track proprio):
  1. Criar propriedade GA4 em analytics.google.com → obter `G-XXXXXXX`.
  2. Inserir tag gtag no `<head>` de todas as páginas (ou via gtag.js).
  3. Manter track.js como está (não conflita; GA só mede).
  4. Adicionar aviso curto de cookies/consentimento (link para /privacidade).
- **Esforço**: 30–40 min. Alternativa: melhorar o track.js atual (src, page,
  evento) em vez de GA — mais barato e já existe.

### 8. XML Sitemap ⭐ → 🔥 (PRIORIDADE 2, junto do Search Console)
- **O que é**: mapa com todas as URLs do site para o Google indexar rápido.
- **Relevância**: essencial — especialmente os **anúncios** (URLs com
  `anuncio.html?id=N`) que sont páginas de produto. GitHub Pages serve
  `sitemap.xml` estático sem problema.
- **Como implementar** (`sitemap.xml` na raiz):
  - Listar: as 10 páginas do site + as URLs dos `id` ativos do marketplace
    (35 e 36–45 hoje — ver CONTEXTO).
  - `<lastmod>` da data de `created_at` do anúncio.
  - Declarar no robots.txt e enviar no Search Console.
  - **Manutenção**: re-gerar quando criar anúncio (pode virar função do
    bot/painel ao publicar; hoje dá para gerar manualmente/script).
- **Esforço**: 15 min inicial + regeneração.

### 9. Palavra-chave no negócio 🔥 (PRIORIDADE 1 — define o resto)
- **O que é**: definir a intenção de busca real de quem compra.
- **Relevância**: é a base de todas as metas e títulos. Não inventar: usar o
  que a comunidade realmente busca (Tibia/OpenTibia — público de nicho).
- **Proposta de keyword primária por página**:
  | Página | Keyword primária sugerida |
  |---|---|
  | index | "BAPZX coins Tibia" / "comprar coins Rubinot" |
  | rubini | "comprar RC Rubinot" / "Rubini coins preço" |
  | service | "service Tibia nível" / "up level Rubinot" |
  | itens | "vender itens Tibia" / "itens Rubinot" |
  | troca/marktrade | "marketplace Tibia" / "trocar itens Tibia" |
  | faq/como-comprar/contato | "como comprar coins Tibia" (perguntas de busca) |
- **Regra**: cada página = **1 keyword**, usada em: título, `h1`, primeiro
  parágrafo e meta description. Comprimento do título ~50–60 chars.
- **Esforço**: 30 min de escrita após decidir o alvo.

---

## ORDEM DE EXECUÇÃO RECOMENDADA (do fundamento ao extra)

1. **Palavra-chave** (item 9) — 20 min. Decide os textos.
2. **Auditoria técnica + descrições + canonical + OG + schema + título
   dinâmico** (item 6) — 1–2h. O maior ganho.
3. **Search Console + sitemap.xml** (itens 1 e 8) — 45 min. Libera
   indexação e medição.
4. **robots.txt** (item 4) — 10 min. Higiene do crawl.
5. **Velocidade** (item 5) — 30 min. PageSpeed → swap de fontes/lazy.
6. **Analytics** (item 7) — 30 min. Medição (ou evoluir track.js).
7. **llms.txt** (item 3) — 5 min. Bônus barato.
8. **Google Meu Negócio** (item 2) — ADIADO (sem endereço/físico; rev. no fim).

---

## STATUS DE IMPLEMENTAÇÃO (atualizado em 25-26/09/2026)

| Item | Ação | Status |
|---|---|---|
| 8. XML Sitemap | `sitemap.xml` criado (10 páginas + anúncios 35–45) e no ar | ✅ FEITO (commit bfefdc9) |
| 4. robots.txt | `robots.txt` criado (Allow: / + aponta sitemap) e no ar | ✅ FEITO (commit bfefdc9) |
| 9. Palavra-chave | keyword definida e aplicada em título/description de todas as páginas | ✅ FEITO (commit c37fc3a) |
| 6. Auditoria técnica | description nas 10 páginas, canonical, OG/Twitter, título dinâmico c/ preço + meta desc dinâmica + schema Product no anuncio.html, og-image.png | ✅ FEITO (commits c37fc3a e 0a187e2) |
| 1. Search Console | propriedade (Prefixo de URL) criada + meta tag `google-site-verification` no index.html (commit 49f2c41) + verificado + sitemap.xml ENVIADO e ACEITO (reenvio em 26/09 após erro transitório de leitura; arquivo validado 200/XML ok ao Googlebot) | ✅ FEITO (dono) |
| 5. Velocidade | lazy-load + width/height nos sprites (troca, anuncio, itens); preconnect + display=swap já existiam | ✅ FEITO (commit ac9ca57) — PageSpeed API sem chave (quota 429), indicadores CLS/lazy validados ao vivo |
| 7. Analytics | track.js corrigido: CORS (beacon → fetch keepalive + credentials omit). Visitas voltaram a ser registradas (ids 30–33 em 26/09) | ✅ FEITO (commit 11c8b2f) — opção "evoluir track.js" escolhida em vez de GA4 |
| 3. llms.txt | `llms.txt` criado na raiz (visão do site + páginas + diretrizes p/ agentes de IA) + referência no robots.txt | ✅ FEITO (commit 11c8b2f) |
| 2. Google Meu Negócio | ADIADO (sem endereço físico) | ⏸️ suspenso |

### Implementado na auditoria (item 6) — detalhes
- **Meta description** em todas as 10 páginas (antes faltavam 6: rubini, service,
  faq, contato, como-comprar; itens/grupos/index eram genéricas — melhoradas).
- **Canonical** e **Open Graph/Twitter cards** em todas (meta og:image aponta
  `og-image.png`, criada 1200×630 no padrão do site).
- **Título/description dinâmicos** no anuncio.html: `document.title` =
  `<Item> — <preço> Gold | MARKTRADE — BAPZX`; og:description e
  meta[name=description] atualizados após o fetch da API.
- **Schema.org Product/Offer** injetado via JS no anuncio.html (nome, preço,
  imagem, seller BAPZX) — base para rich result no Google.
- Título da página: `"<Nome> — <preço> Gold | MARKTRADE — BAPZX"`.

## DECISÕES E RECOMENDAÇÕES A REGISTRAR

- **Maior alavanca agora**: auditoria técnica + keywords + sitemap/SC
  (itens 6, 9, 8, 1). Google Meu Negócio é o único descartável hoje.
- **schema.org Product/Offer no marketplace** é o diferencial competitivo do
  MARKTRADE no Google (preço + produto nos resultados).
- **Domínio próprio** (ex.: bapzx.com.br) multiplica o SEO (canonical limpo,
  SC limpo, confiança) — registrar no ROADMAP como projeto futuro de alto
  impacto.
- **não commitar** arquivos com keys/tokens; SEO é público — nunca colocar
  dados sensíveis em robots/sitemap/llms.
- Atualizar esta memória após implementar cada item (marcar [x] e data).

## PROTOCOLO DE REENTRADA (SEO)
  - Onde paramos: TODOS os itens executáveis FEITOS e no ar — 8 (sitemap), 4
    (robots), 9 (keywords), 6 (auditoria), 1 (SC verificado E sitemap.xml
    enviado pelo dono em 26/09), 5 (velocidade), 7 (analytics via track.js
    corrigido), 3 (llms.txt). Item 2 (Google Meu Negócio) suspenso. Resta só
    o passo opcional do 1: solicitar indexação de home/troca/anuncio via
    Inspeção de URL (acelerar primeiro rastreio).
  - Próximo passo: revisar o Search Console em ~1 semana — impressões,
    cliques, queries e erros de indexação (registrar ganhos reais no
    ROADMAP). O sitemap demora dias para ser lido; as sementes de tráfego
    são os grupos + WhatsApp (SEO é médio prazo).
  - Arquivos tocados (26/09): portfolio — troca.html, anuncio.html, itens.html
    (lazy/dims), track.js (CORS), llms.txt (novo), robots.txt, index/grupos
    (v3.9); raiz — MEMORIA_1.md, ROADMAP-15DIAS.md, LEMBRETE.md.
    Commits portfolio: ac9ca57, d0c98c1, 11c8b2f, 7044aa8.
  - Bloqueios: GA4 exigiria conta Google do dono (hoje track.js próprio basta).
  - Dias restantes: n/a (iniciativa contínua, não é contagem dos 15 dias).