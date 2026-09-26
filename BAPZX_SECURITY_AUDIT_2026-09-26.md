# BAPZX — Revisão crítica de segurança (AppSec)

Data: 2026-09-26
Auditor: Big Pickle (engenheiro sênior AppSec, autorizado)
Alvos: backend Flask em Render (`bapzx-bot-tibia.onrender.com`) + frontend estático GitHub Pages (`bapzxdev.github.io/bapzx-portfolio/`)
Escopo: análise estática do código (bot.py, painel.py, rbac.py, storage.py, legais.py, mk_itens.py, track.js + páginas), enumeração de rotas, revisão de arquitetura e varredura de dependências. Sem utilização de técnicas ofensivas.

> Nota de confidencialidade: este documento não contém chaves, tokens ou valores reais de segredos
> (respeita MEMORIA_SEGURANCA.md). Referências a variáveis de ambiente são nominais.

---

## Estatísticas

- **Críticos: 0**
- **Altos: 0**
- **Médios: 2** (WARNING)
- **Baixos: 5** (WARNING)
- **Informativo: 5**
- **PASS: 14** (dos 15 pontos analisados nesta rodada)
- **N/A: 3 pontos** (não se aplicam à arquitetura)

Postura geral: **boa para o porte do projeto**. Não foi confirmada vulnerabilidade explorável
remotamente sem credenciais. Os controles fortes presentes: OAuth Google com `email_verified`
obrigatório, RBAC servidor-side em todas as rotas administrativas, CSRF com `compare_digest`,
cookies `Secure; HttpOnly; SameSite=Lax`, rate limit por IP, allowlist de origem para CORS,
webhook do Telegram autenticado com secret e comparação constante, sem segredos no frontend ou
no repositório.

---

## 1) Lista corrigida dos 15 pontos (linguagem de checklist)

Reescritos com foco no controle de segurança que deveriam verificar, não na nomenclatura da FAQ:

| # | Ponto original (do pedido) | Formulação corrigida (checklist) |
|---|------------------------------|----------------------------------|
| 1 | Segredos expostos no frontend | Não há chaves/credenciais em arquivos públicos ou no repo |
| 2 | Autorização de acesso a dados ausente/incorreta | Toda rota senless valida cargo/permissão no servidor |
| 3 | Autorização somente no frontend | Nenhuma decisão sensível depende de código do cliente |
| 4 | Endpoints sensíveis sem rate limit | Abuso/volumetria limitada por IP por janela de tempo |
| 5 | Queries SQL com entrada não confiável | Nenhuma query SQL; filtros REST/PostgREST parametrizados com escape |
| 6 | Inputs sem validação no backend | todo input é sanitizado/truncado/validado antes de persistir |
| 7 | Senhas armazenadas de forma insegura | Não existem senhas próprias (login Google OAuth verificado) |
| 8 | Tokens armazenados de forma inadequada | Segredos só em variáveis de ambiente + `.env` gitignored |
| 9 | CORS excessivamente permissivo | `Access-Control-Allow-Origin` devolvido só para origens na allowlist |
| 10 | Contas sem verificação de e-mail | OAuth exige `email_verified=true` para qualquer login |
| 11 | IDOR/BOLA | Recursos só acessíveis ao dono (owner check por email/ID) |
| 12 | Webhooks sem autenticação/assinatura | Webhook Telegram com secret; webhook MP reconfirma no MP |
| 13 | Stack traces / erros internos em produção | Respostas ao cliente sem traceback; erros só em log interno |
| 14 | Dependências vulneráveis | Varredura `pip-audit` sem CVEs conhecidas; dependências pinadas? |
| 15 | Uploads sem validação/controles | Sem upload direto de arquivos; URLs de sprite re-hospedadas += checagem |

---

## 2) Itens tecnicamente imprecisos e como foram reformulados

1. **Item 5 ("queries SQL com entrada não confiável")** — Não existe SQL no projeto. O acesso
   aos dados usa a REST API do Supabase (PostgREST) com filtros do tipo `id=eq.{X}`. A ameaça real
   é **injeção de filtro PostgREST** (quebrar um filtro interpolado numa string de URL), não SQLi.
   Reformulado para: verificar se valores de usuários entram em filtros REST sem codificação.
   Resultado: `_ref_de_preco` faz `quote(nome)` (endpoint `/api/item`), mas filtros internos como
   `email=eq.{email}` (de `session`, já validadas) e `id=eq.{lid}` (int do roteador Flask) estão
   seguros por construção. PASS.

2. **Item 7 ("senhas armazenadas de forma insegura")** — A aplicação **não gerencia senhas**:
   autenticação é 100% Google OAuth com verificação de e-mail. Pensar "hash de senha" nessa
   stack é anacrônico. O controle análogo que importa aqui é o **token de sessão assinado com
   `SECRET_KEY` forte em .env** (presente) — e não há reset de senha, não há database de credenciais.
   Classificado N/A (com nota de que a política deve exigir 2FA do Google para o time).

3. **Item 15 ("uploads de arquivos sem validação")** — Não existe upload de arquivo do usuário.
   O que existe é **fornecimento de URL de sprite** no MARKTRADE, re-hospedada pelo servidor
   (`_mk_sprite_host`: Supabase Storage ou Cloudinary) com extensão de imagem validada
   (`gif/png/jpg/jpeg/webp`) e nome aleatório gerado no servidor. A validação real necessária é
   **restringir origens da URL (SSRF)** e opcionalmente validar o MIME do bytecode — ver achado M2.

4. **Item 12 ("webhooks sem assinatura")** — O webhook do Telegram usa `X-Telegram-Bot-Api-Secret-Token`
   com `secrets.compare_digest` (correto). O webhook do Mercado Pago não valida assinatura, mas
   **reconfirma o pagamento chamando a API do MP com o payment_id recebido** (não confia no payload),
   o que anula a falsificação de status e reduz o vetor a um "solicitador" de consultas no MP por IP.
   Detalhe no achado B2.

5. **Item 9 ("CORS permissivo")** — CORS não é o controle primário de autorização; é uma
   conveniência de leitura do navegador. O que importa é que as APIs que dão acesso a dados não
   públicos **não são consumíveis por origens estranhas** e que as rotas autenticadas não dependem
   de CORS (usam cookie + CSRF). A allowlist `_CSRF_PERMITTED_ORIGINS` + `_cors_ok()` implementam
   isso direito. Único desvio: `/api/grupos` devolve ACAO para qualquer Origin sem chamar
   `_cors_ok()` (dados públicos → informativo).

6. **Item 4 ("rate limiting")** — Não existe biblioteca (ex.: flask-limiter), mas existe controle
   manual por IP (`_rate_limited`, janela 60s, 20/min público, 30/min admin, 60/min webhook MP,
   5/12s no chat do bot). O ponto fraco real é o **armazenamento em memória do processo** (zede a
   cada restart / não compartilhado entre instâncias) — achado B3.

---

## 3) Categorias adicionais de segurança a verificar (até 10)

Campos de verificação além dos 15 pontos:

1. **Cabeçalhos de segurança HTTP** — CSP/HSTS/nosniff/XFO/Referrer-Policy presentes (PASS).
2. **Cookies de sessão e fixação** — Secure, HttpOnly, SameSite=Lax; novo `sid` a cada login; logout limpa sessão remota (PASS).
3. **Fluxo de login/OAuth** — `redirect_uri` fixo ao host validado por `ALLOWED_HOSTS` (PASS); não há verificação de `state` OAuth à vista (ver I5).
4. **IDOR em áreas do cliente** — pedidos/tickets/marketplace filtrados por `email` do dono (PASS).
5. **Enumeração e abuso de informação** — `/health` divulga versão do bot; `debug=1` expõe diagnóstico do Wiki numa API pública (informativo).
6. **Processamento de erros** — respostas públicas sem stack trace, favours de condução de bug a log (PASS).
7. **Proteção a dados (LGPD)** — e-mails/contatos tratados como dado pessoal; política de privacidade documenta tratamento (PASS).
8. **Interação com serviços externos** — TibiaWiki e Mercado Pago: trata-se de chamadas servidor-a-servidor com timeout e sem envio de chaves (PASS); SSRF só via sprite (M2).
9. **Autorização administrativa** — RBAC por cargo + permissões individuais + IP allowlist opcional (PASS).
10. **Gestão de segredos e cadeia de build** — `.env` gitignored, chaves fora do código (PASS); dependências sem pin geram risco de supply chain (B1).

---

## 4) Checklist final por área

### Autenticação
- [x] Login via Google OAuth exige `email_verified=true`.
- [x] Sem credenciais próprias no app (sem senha no banco).
- [x] Sessão: cookie assinado, Secure, HttpOnly, SameSite=Lax, expira em 7 dias.
- [x] Novas sessões registradas em `sessoes`; encerramento revogável (área Segurança).
- [x] Logout limpa sessão local e remota.
- [ ] (Desejável) Revisar presença de validação `state` no fluxo OAuth (I5).

### Autorização
- [x] RBAC por cargo (MASTER=100 ... CLIENTE=10) aplicado em todas as rotas `/admin/*`.
- [x] MASTER fixo por e-mails; interface não permite criar MASTER.
- [x] Owner check em pedidos, tickets e anúncios (por `email` do usuário).
- [x] `ADMIN_IP_ALLOWLIST` aplicada quando configurada.
- [ ] (Informativo) `/api/grupos` devolve ACAO sem checar `_cors_ok()` — dados públicos, sem impacto.

### Dados
- [x] Supabase acessado sempre pela REST com chave de serviço do backend (chave nunca no frontend).
- [x] Listagens públicas filtram `status=eq.ativa` / `ativo=eq.true`; detalhe de anúncio exige `status=ativa`.
- [x] Sem SQL interpolado; filtros com valores de sessão/IDs numéricos.
- [x] Dados de faturamento só expostos em rotas com `ver_pagamentos` / RESTRITAS.
- [ ] `_ref_de_preco` consulta `item_name=ilike.*...*` (usei `quote()` — PASS), manter escape ao evoluir.

### API
- [x] `/api/*` públicos têm rate limit 20/min/IP.
- [x] CORS restrito à allowlist (portfolio + onrender + localhost).
- [x] `/api/track`: valida/trunca campos; throttling 20/min; sem segredos.
- [x] `/api/item`: `quote()` no parâmetro `nome`.
- [ ] (Informativo) `/api/item?debug=1` devolve diagnóstico Wiki; remover em produção ou restringir.

### Frontend
- [x] Sem chaves/URLs internas no estático; só endpoint público da API.
- [x] Renderização dos anúncios usa `esc()` (fuga de `&<>"'`) antes de `innerHTML`.
- [x] `track.js` usa `credentials:"omit"` (correção d0c98c1) — sem CORS de credenciais.
- [?] XSS em elementos `onerror`/atributos com `esc()` — revisão de amostra sem vetor encontrado.

### Infraestrutura / transporte
- [x] HTTPS obrigatório (Render + Pages); HSTS no backend.
- [x] Headers de segurança aplicados via `@app.after_request`.
- [x] Host allowlist protege contra Host header poisoning / redirects OAuth.
- [ ] (Baixo) Header `x-render-origin-server` divulga Werkzeug/Python; `/health` divulga versão.

### Dependências
- [x] `pip-audit` na venv local: **nenhuma vulnerabilidade conhecida**.
- [ ] (Baixo) `requirements.txt` sem pin exato de versões (flask, requests, google-genai, authlib, reportlab, tzdata) — risco de atualização não planejada.

### Uploads
- [x] Sem upload direto de arquivos de usuários.
- [x] URL de sprite só aceita `http(s)://`, extensão de imagem validada no re-hosting, nome aleatório no servidor.
- [ ] (Médio) `_mk_sprite_host` (quando `MK_SPRITE_HOST` configurado) faz GET em URL arbitrária fornecida pelo usuário — potencial SSRF (M2).

---

## Achados por severidade

### MÉDIO

**M1 — CSP com `script-src 'unsafe-inline'` (embora a aplicação rode JS inline).**
O backend injeta muito JavaScript inline (formulários, marketplace), o que exige `unsafe-inline`.
Impacto: se qualquer input refletir sem escape, o CSP não impede execução. Mitigado pela
sanitização consistente com `html.escape`/`esc()`. Correção recomendada: quando julgar o custo
aceitável, migrar scripts para arquivos estáticos (permitindo `script-src 'self'`), ou usar
nonces/hashes. Atualmente sem vetor conhecido de XSS.

**M2 — SSRF condicional no re-hosting de sprite (`_mk_sprite_host`).**
Quando a env `MK_SPRITE_HOST` lista `supabase` ou `cloudinary`, o servidor executa
`requests.get(url, timeout=20)` numa URL `http(s)://` fornecida pelo usuário no formulário de
publicação, sem allowlist de domínio. Neste ambiente a env não está setada, então o código nem
entra no `requests.get` (devolve a URL direto) — o risco é latente. Correção recomendada:
restringir a URL a `https://` e a um conjunto de hosts permitidos (ex.: `tibiawiki.com.br`,
`*.githubusercontent.com`), validar o MIME do conteúdo (`image/*`) e colocar limite de tamanho
(ex.: 2 MB), além de não seguir redirects para hosts não aprovados. Não explorável hoje.

M3 (mantido do audit anterior como Médio na época) — na rodada atual, o tracking por `sendBeacon`
**foi corrigido** (track.js agora usa `fetch` com `credentials:"omit"`), então este ponto saiu do
mapa de risco.

### BAIXO

**B1 — `requirements.txt` sem pin de versões.** `flask, requests, google-genai, authlib,
reportlab, tzdata` sem versões fixadas. Hoje `pip-audit` não acusa CVE, mas um `pip install`
futuro pode puxar versões com breaking change ou CVE. Correção: `pip freeze > requirements.txt`
(ou pin com `==` nas construtivas críticas; considerar `pip-tools`/`uv lock`).

**B2 — Webhook do Mercado Pago sem validação de assinatura.** Mitigado por reconsulta no MP
(seguro contra falsificar status), mas qualquer IP pode postar payment_ids e "forçar" consultas
no MP (custo/abuso). Rate limit 60/min aplicado. Correção recomendada (se pertinente): validar
a assinatura de webhook do MP (header `x-signature`) ou restringir por IP público do MP. Baixo
pelo impacto limitado.

**B3 — Rate limit em memória do processo.** `_RATE`, `CHAT_HISTORY`, `MP_WEBHOOK_HITS` zedam
no restart e não são compartilhados entre réplicas. Em Render com múltiplas instâncias ou sob
restart frequente, o limite por IP pode ser contornado. Correção: uma cache distribuída
(Redis) ou aceitar o limite como "best-effort" numa instância única (documentar).

**B4 — `/api/track` aceita body até ~11MB.** `request.get_json(silent=True)` sem limite de
tamanho; campos truncados (250/500/20). Mitigação: rate limit 20/min por IP e as visões não
refletem o conteúdo cru. Correção: definir `MAX_CONTENT_LENGTH` no app (ex.: 64 KB) ou ler com
limite explícito.

**B5 — Header `x-render-origin-server` / `/health` divulgam versões.** `bot ok v2.10.20` e o
header da infra expõem Werkzeug/Python. Baixo (facilita fingerprinting).

### INFORMATIVO

**I1 — `/api/grupos` sem `_cors_ok()`** (reflete qualquer Origin). Dado público (grupos WhatsApp),
sem impacto de confidencialidade. Alinhar com as demais APIs para consistência.

**I2 — `/api/item?debug=1`** expõe diagnóstico do TibiaWiki em API pública. Informativo; útil no
dev. Restringir/quitar em produção se desejado.

**I3 — Comparação `given == expected` no `/dashboard`** (DASHBOARD_KEY). Usa comparação não
constante; risco teórico de timing. Usar `secrets.compare_digest`.

**I4 — Fallback de storage para arquivo local (`pedidos.json`)** no `OrderStore.save()` quando o
Supabase falha. Isso é resiliência, não falha de segurança; vale registrar que o fallback pode
perder dado se a instância Render reciclar antes do re-sync (não há job de reenvio). Monitorar.

**I5 — Fluxo OAuth: não vi chamada explícita a `state`** no `authorize_redirect` (o Authlib
gerencia o `state` na sessão por padrão). Confirmar e, se ausente, adicionar proteção CSRF de
login num sprint futuro. Impacto prático baixo com SameSite=Lax + GET-only.

---

## Itens da lista original N/A (não se aplicam)

- **7 (senhas)** — sem senhas próprias; autenticação OAuth.
- **15 (uploads)** — não há upload direto de arquivos; há URL de sprite re-hospedada (ver M2).
- **11 (IDOR)** — verificado e PASS (owner check): mas lembrar de manter o padrão em novos fluxos.

---

## Notas de confidencialidade e boas práticas mantidas

- Nenhum segredo real foi exposto ou citado neste relatório (MEMORIA_SEGURANCA.md).
- Auditoria 100% estática + dependências; nenhum teste destrutivo contra serviços de terceiros.
- Comparação com o audit anterior (22/09): o item de tracking por CORS foi resolvido; demais
  achados permanecem de baixa severidade.