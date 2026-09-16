-- BAPZX bot-negocio v2.3.0
-- Cupons de desconto configuráveis no painel (item 10 do roadmap do dono).
-- Rode no Supabase SQL Editor. Idempotente (pode rodar de novo sem erro).

-- 1) Tabela de cupons
create table if not exists public.cupons (
  id            uuid    not null default gen_random_uuid() primary key,
  codigo        text    not null unique,
  tipo          text    not null default 'percentual' check (tipo in ('percentual', 'fixo')),
  valor         numeric not null default 0,
  validade      date,                          -- null = sem prazo
  limite_usos   integer not null default 0,    -- 0 = ilimitado
  usos          integer not null default 0,
  produto_id    uuid,                          -- null = qualquer item (itens.id)
  servico_id    uuid,                          -- null = qualquer serviço (servicos.id)
  grupo_id      bigint,                        -- null = qualquer grupo (grupos.id)
  ativo         boolean not null default true,
  criado_em     timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

create index if not exists ix_cupons_ativo       on public.cupons (ativo);
create index if not exists ix_cupons_validade    on public.cupons (validade);
create index if not exists ix_cupons_produto_id  on public.cupons (produto_id);
create index if not exists ix_cupons_servico_id  on public.cupons (servico_id);
create index if not exists ix_cupons_grupo_id    on public.cupons (grupo_id);