-- BAPZX bot-negocio v2.8.0
-- Módulo COINS (área administrativa): gestão manual de estoque, preço/1.000,
-- limites de compra, status da venda, observação e histórico de alterações.
-- Rodar no Supabase > SQL Editor > New query e executar o bloco inteiro.

-- ============================================================
-- 1) coins_config — linha única (id = 1) com a situação atual das COINS
--    estoque:  quantidade de COINS disponíveis para venda (manual)
--    preco_mil: preço em R$ por 1.000 COINS (usado pelo bot para calcular)
--    min_compra / max_compra: limites de quantidade por pedido
--    status:    'ativo' = vendas liberadas | 'pausado' = vendas pausadas
--    observacao: nota interna do administrador
-- ============================================================
create table if not exists public.coins_config (
  id              bigint generated always as identity primary key,
  estoque         numeric(14,2) not null default 100000,
  preco_mil       numeric(12,2) not null default 90,
  min_compra      numeric(14,2) not null default 100,
  max_compra      numeric(14,2) not null default 50000,
  status          text not null default 'ativo',
  observacao      text not null default '',
  atualizado_em   timestamptz,
  atualizado_por  text not null default '',
  criado_em       timestamptz not null default now()
);

-- linha única padrão (a criação do painel dá upsert em id=1)
insert into public.coins_config (id, estoque, preco_mil, min_compra, max_compra, status, observacao)
values (1, 100000, 90, 100, 50000, 'ativo', '')
on conflict (id) do nothing;

-- ============================================================
-- 2) coins_historico — registro de cada alteração feita no painel
--    qtd_anterior/qtd_nova e preco_anterior/preco_novo guardam o antes e o
--    depois (null quando o campo não mudou naquela edição).
-- ============================================================
create table if not exists public.coins_historico (
  id              bigint generated always as identity primary key,
  admin           text not null default '',
  qtd_anterior    numeric(14,2),
  qtd_nova        numeric(14,2),
  preco_anterior  numeric(12,2),
  preco_novo      numeric(12,2),
  alteracao       text not null default '',
  criado_em       timestamptz not null default now()
);
create index if not exists ix_coins_historico_criado on public.coins_historico (criado_em desc);
create index if not exists ix_coins_historico_admin on public.coins_historico (admin);

-- Verificação: as tabelas acima devem aparecer em
--   supabase_migracao → Table Editor.