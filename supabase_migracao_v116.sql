-- BAPZX bot-negocio v1.16.0
-- Clientes (perfil + bloqueio), Pagamentos, Tickets e Configurações.
-- Rode no Supabase SQL Editor.

-- 1) Colunas novas em profiles (personagem/mundo salvo no perfil, bloqueio de cliente)
alter table public.profiles add column if not exists personagem text not null default '';
alter table public.profiles add column if not exists mundo text not null default '';
alter table public.profiles add column if not exists bloqueado boolean not null default false;

-- 2) Tickets de suporte (cliente abre chamado, admin responde/encerra)
create table if not exists public.tickets (
  id            bigint generated always as identity primary key,
  email         text    not null,
  assunto       text    not null default '',
  mensagem      text    not null default '',
  status        text    not null default 'aberto',   -- aberto | respondido | encerrado
  prioridade    text    not null default 'normal',   -- normal | alta | urgente
  resposta      text    not null default '',
  respondido_em timestamptz,
  respondido_por text   not null default '',
  criado_em     timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
create index if not exists ix_tickets_email   on public.tickets (email);
create index if not exists ix_tickets_status on public.tickets (status);

-- 3) Configurações de chave-valor (preços, notificações)
create table if not exists public.config (
  chave         text primary key,
  valor         text not null default '',
  atualizado_em timestamptz not null default now()
);
insert into public.config (chave, valor) values
  ('precos', '{"100":"R$ 9,00","250":"R$ 22,50","500":"R$ 45,00","1000":"R$ 90,00","2500":"R$ 225,00"}'),
  ('notificar_pedido', '1')
on conflict (chave) do nothing;

-- 4) Índices auxiliares
create index if not exists ix_pedidos_status on public.pedidos (status);
create index if not exists ix_pedidos_email  on public.pedidos (email);