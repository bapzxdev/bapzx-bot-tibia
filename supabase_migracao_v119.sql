-- BAPZX bot-negocio v2.1.0
-- Separa "Serviços" (Intermediação) da tabela de itens do jogo.
-- Rode no Supabase SQL Editor. Idempotente (pode rodar de novo sem erro).

-- 1) Tabela de serviços (espelha a estrutura de itens)
create table if not exists public.servicos (
  id         uuid    not null default gen_random_uuid() primary key,
  nome       text    not null unique,
  descricao  text    not null default '',
  preco      text    not null default '',
  imagem     text    not null default '',
  ativo      boolean not null default true,
  categoria  text    not null default 'geral',
  ordem      integer not null default 0,
  criado_em  timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

create index if not exists ix_servicos_ativo_ordem on public.servicos (ativo, ordem);

-- 2) Migration: Intermediação sai de 'itens' e vai para 'servicos'
insert into public.servicos (nome, descricao, preco, ativo, categoria, ordem)
values (
  'Intermediação BAPZX',
  'Intermediação segura para suas transações in-game. Valor por transação intermediada.',
  'R$ 5,00',
  true,
  'Intermediação',
  0
)
on conflict (nome) do nothing;

delete from public.itens
 where nome = 'Intermediação BAPZX'
   and categoria = 'Intermediação';

-- 3) Bucket público para imagens dos serviços (mesmo padrão de itens)
insert into storage.buckets (id, name, public)
values ('servicos', 'servicos', true)
on conflict (id) do nothing;

drop policy if exists "Public read imagens servicos" on storage.objects;
create policy "Public read imagens servicos"
  on storage.objects for select
  using (bucket_id = 'servicos');