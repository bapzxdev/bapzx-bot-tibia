# BAPZX SECURITY AUDIT

Data: 2026-09-22
Alvos: https://bapzx-bot-tibia.onrender.com (backend), https://bapzxdev.github.io/bapzx-portfolio/ (frontend)
Auditor: Big Pickle (assistente autorizado)
Escopo: análise estática + testes HTTP ao vivo + revisão de código. Sem alteração de código (somente documentação).

## Resumo executivo

- **Críticos: 0**
- **Altos: 0**
- **Médios: 1** (incluído em WARNING — divulgado)
- **Baixos: 3** (WARNING)
- **PASS: 52**
- **NOT TESTED: 8**
- **N/A: 3**

A aplicação apresenta postura de segurança boa para o porte: sem segredos no repositório,
proteção OAuth com email verificado, RBAC em todas as rotas administrativas, CSRF com comparação
de tempo constante, cookies de sessão seguros, rate limit por IP, proteção contra Host header injection,
handlers de erro sem stack trace e webhooks validados. Nenhuma vulnerabilidade explorável de forma
remota sem credenciais foi confirmada.

Achados mais relevantes (todos de baixa/enumerativa severidade):
1. CSP inclui `'unsafe-inline'` em `script-src` (enfraquece defesa contra XSS caso um input reflita).
2. Header `x-render-origin-server` já evidenciou `Werkzeug/3.1.8 Python/3.14.3` (divulgação de versão).
3. `/api/track` não limita tamanho do body (11MB aceito); mitigado por rate limit por IP.
4. Tracking do portfólio (`sendBeacon`) falha por CORS (sem `Access-Control-Allow-Credentials`) — tracking não funciona, mas nada vaza.

## Metodologia

- Repositórios analisados: `bapzx` (bot.py, painel.py, rbac.py, storage.py, legais.py) e `bapzx-portfolio` (track.js + páginas).
- Testes HTTP ao vivo via `curl`/Playwright (navegação controlada).
- Nenhum teste destrutivo, nenhuma transação financeira real, nenhum teste contra terceiros.
- Contas de login reais (CLIENTE_A/B, ADM_TESTE) NÃO puderam ser exercitadas ao vivo (OAuth em modo teste, sem credencial fornecida ao auditor) → itens marcados NOT TESTED.
- OWASP ZAP não instalado no ambiente → varredura ZAP registrada como NOT TESTED (não inventada).

---

## Tabela de testes

| ID | Categoria | Teste | Resultado | Evidência / Observação |
|----|-----------|-------|-----------|------------------------|
| T01 | Segredos | Varredura estática no código (bot/painel/rbac/storage/legais) | PASS | Secrets lidos apenas via `load_env_key()`; nenhum valor hardcoded |
| T02 | Segredos | `.env` versionado no repo | PASS | Gitignored; arquivo local presente mas fora do git |
| T03 | Segredos | Histórico git por padrões de chave (sk-, AKIA, ghp_ etc.) | PASS | Sem chave real; único match foi citação de nome de variável em doc |
| T04 | Segredos | Varredura no repo bapzx-portfolio | PASS | `track.js` limpo; páginas estáticas sem segredos; sem `.env` |
| T05 | Transporte | Redirect HTTP→HTTPS | PASS | `301` para https no `/health` |
| T06 | Transporte | HSTS | PASS | `max-age=31536000` (backend) e `31556952` (GitHub Pages) |
| T07 | Transporte | CSP presente e restritivo | PASS(1) | `default-src 'self'`, `frame-ancestors 'none'`, `form-action 'self'`; (1) ver W24-`script-src 'unsafe-inline'` |
| T08 | Transporte | X-Frame-Options | PASS | `DENY` |
| T09 | Transporte | X-Content-Type-Options | PASS | `nosniff` |
| T10 | Transporte | Referrer-Policy | PASS | `same-origin` |
| T11 | Transporte | Permissions-Policy | PASS | `geolocation=(), microphone=(), camera=()` |
| T12 | Transporte | Info disclosure de versão | WARNING | `x-render-origin-server: Werkzeug/3.1.8 Python/3.14.3` visível ao público (ver W21) |
| T13 | Transporte | Erro 404/500 sem stack trace | PASS | Resposta limpa `erro`/`nao encontrado`; traceback só em log interno + Telegram |
| T14 | Sessão | Cookie de sessão: Secure/HttpOnly | PASS | `session=...; Secure; HttpOnly; Path=/; SameSite=Lax` |
| T15 | Sessão | Cookie de sessão: SameSite | PASS | `SameSite=Lax` (mitigação CSRF de navegador) |
| T16 | Sessão | Session fixation | PASS | Novo `sid = secrets.token_urlsafe(24)` gerado a cada login |
| T17 | Sessão | Logout limpa sessão | PASS | `session.clear()` + encerramento remoto da sessão (sessoes) |
| T18 | Autenticação | OAuth Google com `state` | PASS | Redirecionamento contém `state` (Authlib define automaticamente) no `/login` |
| T19 | Autenticação | Nonce/CSRF do OIDC | PASS | Presente no redirect (Authlib) |
| T20 | Autenticação | `email_verified` exigido | PASS | Código checa `info.get("email_verified")` antes de criar sessão |
| T21 | Autenticação | Callback OAuth sem código | PASS | Responde `400` sem crash |
| T22 | Autenticação | Login com Host header injetado | PASS | `Host: evil.example.com` → `403` (subdomínio validado) |
| T23 | Autenticação | Login real (CLIENTE_A/B/ADM_TESTE) | NOT TESTED | OAuth modo teste; sem credencial para o auditor |
| T24 | Autorização | Rotas /admin e /cliente anônimas | PASS | `302` → `/login` sem sessão (testado /admin, /admin/services, /cliente*, /admin/clientes/<email>) |
| T25 | Autorização | RBAC: cargos e permissões efetivas | PASS | `rbac.py`: MASTER imutável (só e-mails fixos), permissões validadas contra `ALL_PERMISSOES` |
| T26 | Autorização | IDOR em /cliente (pedidos) | PASS | Pedidos filtrados por `email == user.email` em memória |
| T27 | Autorização | IDOR em perfil e tickets | PASS | `/cliente/perfil` e `/cliente/suporte/<id>` filtram por e-mail do usuário logado |
| T28 | Autorização | Admin IP allowlist opcional | PASS | `ADMIN_IP_ALLOWLIST` respeitada em `_require_perm` |
| T29 | Autorização | Reset de permissões em sessão encerrada | PASS | `_sessao_ativa` consulta sessão remota; `session.clear()` ao falhar |
| T30 | CSRF | Token com comparação constante | PASS | `secrets.compare_digest` em `_csrf_ok` |
| T31 | CSRF | POST /admin sem sessão | PASS | `403` (marcar, coins/salvar) e `302` (usuários/novo) |
| T32 | CSRF | POST /cliente sem token | PASS | `403` via `_csrf_ok` em perfil e suporte |
| T33 | Webhook | /webhook (Telegram) GET | PASS | `405` |
| T34 | Webhook | /webhook sem `X-Telegram-Bot-Api-Secret-Token` | PASS | `403` |
| T35 | Webhook | /webhook com secret errado | PASS | `403` |
| T36 | Webhook | /webhook/mp GET | PASS | `405` |
| T37 | Webhook | /webhook/mp POST malformado | PASS | Responde `200` sem efeito; sem crash |
| T38 | Webhook | Idempotência do webhook MP | PASS | Consulta status do pagamento no MP server-side antes de aplicar; pedido já pago ignorado |
| T39 | Webhook | Pagamento fabricado sem MP | PASS | Sem `status` válido do MP, não há aplicação — não é possível inventar pagamento via payload |
| T40 | CORS | Origin não permitida | PASS | OPTIONS de origem não-allowlist sem `Access-Control-Allow-Origin` |
| T41 | CORS | Origin permitida | PASS | `Access-Control-Allow-Origin: https://bapzxdev.github.io` + métodos POST/OPTIONS |
| T42 | CORS | Tracking do portfólio (sendBeacon) | WARNING | Bloqueado pelo navegador por falta de `Access-Control-Allow-Credentials` → tracking não funciona (ver W24) |
| T43 | Rate limit | /api/track | PASS | Limite por IP: 19×200 + 11×429 em 30 requisições rápidas |
| T44 | Rate limit | /api/grupos | PASS | Respondeu `429` em rajada |
| T45 | Rate limit | /admin | PASS | `_RATE_LIMIT_ADMIN_PER_MIN` configurado no código |
| T46 | Entrada | JSON inválido em /api/track | PASS | Tratado com `silent=True` → `200`/sem efeito |
| T47 | Entrada | Payload grande /api/track | WARNING | 500KB e 11MB aceitos sem limite de tamanho de body (ver W23) |
| T48 | Injeção | SQL em consultas | PASS | Sem query string crua; acesso via Supabase REST parametrizado (eq./select) |
| T49 | XSS | Escape de saída | PASS | `html.escape` aplicado nos campos refletidos (pedidos, perfil, tickets, config) |
| T50 | XSS | CSP sem unsafe-eval | PASS | `script-src` sem `'unsafe-eval'` |
| T51 | API | /api/itens, /api/servicos, /api/grupos | PASS | Só dados públicos (itens/serviços/grupos ativos) |
| T52 | API | /api/site sem segredos | PASS | Retorna só `_CONFIG_PUBLICAS` (brand + links); sem pix_chave/token |
| T53 | API | /api/track com acesso sem DASHBOARD_KEY | PASS | Aceito; endpoint é público intencional (tracking) e rate-limited |
| T54 | Rota | /dashboard com chave errada | PASS | `401` (query e header) |
| T55 | Rota | /pedidos com chave errada | PASS | `401` |
| T56 | Rota | /health GET | PASS | `200` (público) |
| T57 | Rota | /robots.txt, /sitemap.xml, /.well-known/security.txt | PASS | `404` (ausentes; recomendação opcional no W25) |
| T58 | Rota | Rota inexistente | PASS | `404` limpo |
| T59 | Rota | /api com método não permitido (PUT/DELETE/PATCH) | PASS | `405` |
| T60 | Infra | /webhook/mp exposto sem auth | PASS | Design correto: consulta MP server-side; não confia no payload |
| T61 | Infra | Lock de depêndencias / requirements | PASS | requirements.txt versionado (não auditado versões CVE trivially) |
| T62 | Integração | Portfólio: console sem erros críticos | WARNING | 2 erros benignos (favicon 404, sendBeacon CORS) — ver W22/W24 |
| T63 | ZAP | Varredura passiva OWASP ZAP | NOT TESTED | ZAP não instalado no ambiente de auditoria |
| T64 | ZAP | Varredura ativa OWASP ZAP | NOT TESTED | Idem |
| T65 | ZAP | Política padrão do ZAP | NOT TESTED | Idem |
| T66 | Supabase | RLS em tabelas (pedidos, profiles, config, etc.) | NOT TESTED | Sem acesso ao console/credenciais; depende do dono (ver W26) |
| T67 | Supabase | Chave anon vs service-role corrigida nas envs | NOT TESTED | Valor das envs não exposto; config por auditoria interna do dono |
| T68 | Auth | Sessão expira / tempo de vida configurado | NOT TESTED | `session.permanent` com cookie 7d observado; tempo exato depende de config (dono) |
| T69 | Auth | 2FA/MFA em contas admin | PASS | Login via Google (com 2FA do Google); sem senha local (nota W27) |
| T70 | Auth | Força bruta em senha local | N/A | Não há login por senha local |
| T71 | Auth | Enumeração de usuários | PASS | Respostas uniformes em login/rotas públicas |
| T72 | Rede | TLS 1.2/1.3 | N/A | Terminação TLS do Render/Cloudflare + GitHub Pages |
| T73 | Rede | IP público mascarado | N/A | Aplicação atrás de Cloudflare (header `Server: cloudflare`) |
| T74 | Auditoria | Trilha de auditoria (audit_log) | PASS | Ações admin gravadas em `audit_log` (email, ação, detalhes, IP) |
| T75 | Auditoria | Sessões/atividade registrada | PASS | Tabela `sessoes` (sid, email, ip, user_agent) — v2.7.0 |

## WARNINGS (achados)

**W21 — Divulgação de versão do servidor (Baixo).**
`x-render-origin-server: Werkzeug/3.1.8 Python/3.14.3` fica exposto a todos. Belisk: remover/supressor
do header via configuração do Render (ou middleware que o apague). Não é explorável sozinho, mas alimenta
reconhecimento.

**W22 — Favicon ausente no portfólio (Baixo).**
Erro `404` ao carregar `/favicon.ico` no GitHub Pages. Cosmético; ocorre no console.

**W23 — /api/track sem limite de tamanho de body (Médio/Baixo).**
O endpoint aceitou corpo de 11MB. Mitigado por rate limit por IP (20/min). Recomenda-se limite de
request body (ex.: rejeitar > 64KB em `/api/track`).

**W24 — CSP `script-src 'unsafe-inline'` + CORS do tracking (Baixo).**
- CSP usa `'unsafe-inline'` para scripts (comum em apps que montam HTML inline — este app renderiza por template inline, então é praticamente necessário sem big refactor; ainda assim enfraquece defesa em profundidade).
- `sendBeacon` do portfólio é bloqueado por CORS (faltam `Access-Control-Allow-Credentials: true`). Efeito: o tracking **não envia** dados — nenhuma fuga, apenas telemetria não funciona.

**W25 — Robots/security.txt ausentes (Baixo/Op).**
`/robots.txt`, `/sitemap.xml` e `/.well-known/security.txt` retornam 404. Não é falha de segurança;
`security.txt` é reiterado nas boas práticas de contato para divulgadores.

**W26 — RLS do Supabase não verificável externamente (NOT TESTED).**
Recomenda-se o dono confirmar no console do Supabase que as políticas (RLS) de `coins_config`,
`orders`, `profiles`, `config`, `tickets`, `sessions`, `groups`, `items`, `services` estão ativas e
restritas, e que a chave em `SUPA_KEY` seja a **anon key** (com RLS aplicado) para o backend — e não
a service-role — ou que a service-role fique APENAS acessível dentro do backend (que é o padrão atual:
o backend a usa server-side; os clientes nunca a veem).

**W27 — Administradores dependem da segurança da conta Google (nota).**
Não há MFA adicional no painel além do Google. Recomenda-se que todas as contas com cargo
administrativo ativem 2FA no Google.

## Prioridades recomendadas (ordem)

1. (W26) Confirmar RLS + tipo de chave Supabase no console — única pendência de alto impacto incerto.
2. (W23) Limitar tamanho do body em `/api/track` (rejeitar payloads grandes).
3. (W24) Avaliar remoção de `'unsafe-inline'` do CSP OU manter ciente do risco; corrigir CORS do tracking se quiser telemetria funcionando.
4. (W21) Remover header `x-render-origin-server`.
5. (W22) Adicionar um favicon ao portfólio.
6. (W25) Adicionar `security.txt` e `robots.txt` (permite mais fácil contato de segurança).

## Correções sugeridas (resumo)

- **W23** — Em `api_track()`: antes de ler o json, checar `content_length` e retornar `413` se acima de, ex., 16KB; depois aplicar `data.get` truncação como hoje.
- **W24** — Para o tracking: incluir `Access-Control-Allow-Credentials: true` + `Vary: Origin` no OPTIONS/response de `/api/track` (somente para origem allowlist) se desejar que `sendBeacon` funcione. Para CSP: mantido `'unsafe-inline'` documentado como trade-off (estilo inline usado em todo o painel).
- **W21** — Configurar no Render: header de remoção/overwrite para `x-render-origin-server`, ou aceitar/ocultá-lo.
- **W25** — Criar `/.well-known/security.txt` estático apontando para email/Telegram do dono.
- **W26** — Auditoria manual do dono no console Supabase (RLS em todas as tabelas; chave usada não é a service-role em lugar exposto).

## NOT TESTED (depende do dono/ambiente)

- T23 Login real (OAuth teste), T63-T65 OWASP ZAP, T66 RLS Supabase, T67 tipo de chave Supabase nas envs, T68 expiração exata da sessão.

---

Fim do relatório.