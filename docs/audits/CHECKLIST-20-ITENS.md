# CHECKLIST 20 ITENS DE SEGURANÇA × BAPZX (03/10/2026)

Origem: print do dono com 20 controles. Mapeamento contra o código atual
(bot.py/painel.py/rbac.py) e a auditoria `BAPZX_SECURITY_AUDIT_2026-09-26.md`.

Legenda: ✅ implementado · 🔶 parcial/falha conhecida · ➖ N/A por arquitetura

| # | Item | Status | Evidência / onde está |
|---|---|---|---|
| 1 | HTTPS | ✅ | TLS do Render + HSTS `max-age=31536000` (bot.py, `security_headers`, v2.0.2) |
| 2 | Senhas com Hash | ➖ | Sem senhas no app — só login Google (OAuth). Nada para hashear |
| 3 | MFA | 🔶 | Delegado ao Google (2FA da conta). Sem MFA próprio p/ admins |
| 4 | Rate Limit | 🔶 | Por endpoint em memória (`_rate_limited`, painel.py). Zera no restart (B3) |
| 5 | Validação de Inputs | ✅ | Todos os POSTs validam (mundo, tier, preço, WhatsApp, CSRF, arquivos) |
| 6 | Sanitização de dados | 🔶 | `html.escape` em tudo (XSS do /dashboard corrigido v1.11.2). Resta CSP `unsafe-inline` (M1, sem XSS conhecido) |
| 7 | SQL Injection | ➖ | App não monta SQL — só Supabase REST. SQL existe só nas migrations manuais |
| 8 | Migrations | ✅ | v111→v126 versionadas em `C:\DEV\Supabase`, regra em MEMORIA_MIGRATION.md |
| 9 | Rollback | 🔶 | Código: git revert + redeploy OK. Banco: migrations sem DOWN — sem rollback de DB definido |
| 10 | Controle de Acesso | ✅ | RBAC "BAPZX ACCESS" (cargos + permissões individuais + audit de 21 rotas) |
| 11 | Expiração de sessão | ✅ | Sessão 7 dias + encerrar sessão remota (`/admin/seguranca`, tabela `sessoes`) |
| 12 | Secrets | ✅ | Envs no Render, `.env` gitignored, scan sem vazamento (2 tokens de chat revogados em 13/09) |
| 13 | CORS | 🔶 | Allowlist condicional (`_cors_ok`). I1: `/api/grupos` reflete Origin (dado público, baixo risco) |
| 14 | LOGS | ✅ | `audit_log` (bot + admin) com busca/filtros/CSV + alerta Telegram em 500 real |
| 15 | Backups | 🔶 | Backup de código zip (v1.16.2 + RESTAURAR.txt). Sem rotina de backup do banco Supabase |
| 16 | Criptografia | 🔶 | TLS em trânsito + repouso do Supabase. Sem cripto a nível de app (ex.: WhatsApp em texto) |
| 17 | Dependências | ✅ | `requirements.txt` pinado em 03/10/2026 (incl. `urllib3==2.8.0` que corrigiu 3 CVEs do 2.7.0); `pip-audit` limpo; rotina mensal anotada no arquivo |
| 18 | PMP (mínimo privilégio / patch) | 🔶 | RBAC granular ✅, mas ADMINISTRADOR=ALL e MASTER bypass; sem processo formal de patch |
| 19 | Monitoramento | 🔶 | Alerta Telegram em 500 + sino/notificações. Monitor externo: runbook pronto em `docs/runbooks/UPTIME-MONITOR.md` — falta o dono criar a conta grátis (5 min) |
| 20 | Plano de Recuperação | 🔶 | RESTAURAR.txt cobre código. Sem runbook de DR do banco |

## O que falta implementar (resumo para o dono)

1. **PMP formal + pin de deps** (17/18, barato): pinar `requirements.txt` + rotina mensal de `pip-audit`.
2. **Rollback de banco** (9): escrever DOWN das migrations críticas ou snapshot antes de aplicar.
3. **Rotina de backup do banco** (15): export agendado do Supabase (ou conferir PITR do plano).
4. **Monitor de uptime externo** (19, grátis): UptimeRobot/Better Uptime no `/health`.
5. **MFA próprio p/ admins** (3, opcional): hoje o Google cobre; avaliar se precisa de camada extra.
6. **Runbook de DR** (20): 1 página — "banco caiu / Render caiu / conta Google travou: o que fazer".
7. Pendentes da auditoria 26/09: M2 (allowlist sprite host), B2 (assinatura webhook MP), B4 (limite body track).
