# MEMORIA MIGRATION - Onde ficam os arquivos do Supabase

Regra de organização (definida pelo dono em 22/09/2026): **todo arquivo
relacionado ao Supabase deve morar na pasta `C:\DEV\Supabase`**, e não dentro
do repositório do projeto BAPZX. O repositório (git) serve para código;
`C:\DEV\Supabase` é a pasta canônica dos SQLs.

Ajuste feito em 22/09/2026: as migrations `supabase_migracao_v*.sql`
(111, 114, 115, 116, 118, 119, 120, 121, 122, 123) e os scripts
`criar_tabela_supabase.sql` e `migracao_status.sql` foram REMOVIDOS do
repositório e ficam só em `C:\DEV\Supabase`. A pasta não é um repositório
git — é a sua organização local para se encontrar (tudo num lugar só).

## Onde cada coisa fica

- **`C:\DEV\Supabase\`** — todas as migrations SQL do banco:
  - `supabase_migracao_vNNN.sql` (novas versões sempre são criadas AQUI);
  - `criar_tabela_supabase.sql` — DDL da tabela `public.pedidos`;
  - `migracao_status.sql` — checks de migração/estado do banco.
- **Repo `bapzx`** — NÃO versionar .sql de Supabase. Se um arquivo SQL novo
  for gerado, criá-lo direto em `C:\DEV\Supabase`.
- **`scripts/migrar_pedidos.py`** — ficou NO repo: é script Python que roda
  junto do projeto (migração de `pedidos.json` → Supabase via código), não é
  SQL.

## Aplicação das migrations (fluxo do dono)

1. O SQL é criado/salvo em `C:\DEV\Supabase\supabase_migracao_vNNN.sql`.
2. O dono abre o arquivo e cola no **SQL Editor** do Supabase (console) para
   aplicar.
3. Mensagens no painel (ex.: aviso no `/admin/coins`) podem citar o nome do
   arquivo (ex.: `supabase_migracao_v123.sql`) — o arquivo está em
   `C:\DEV\Supabase`, não no repo.

## Notas

- Histórico de migrations aplicadas / pendentes fica registrado em
  `MEMORIA_PENDENCIAS.md` e `ROADMAP-15DIAS.md` (docs, não nos SQLs).
- Se algo "quebrar", a primeira coisa a conferir é a pasta `C:\DEV\Supabase`
  (fonte única) e o estado no console do Supabase.