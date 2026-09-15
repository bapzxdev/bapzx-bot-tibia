-- BAPZX bot-negocio v2.0.0
-- BAPZX ACCESS (RBAC): usuários da equipe, grupos do WhatsApp e produto de
-- intermediação. Rode no Supabase SQL Editor.

-- ============================================================
-- 1) Tabela de usuários da equipe (RBAC)
--    cargo: MASTER(não usar aqui) | ADMIN | MANAGER | FINANCEIRO |
--           OPERADOR | MODERADOR | SUPORTE | CLIENTE
--    permissoes: lista JSON de permissões individuais (se vazia, usa o
--                padrão do cargo). MASTER vem só de MASTER_EMAILS no .env.
-- ============================================================
create table if not exists public.users (
  email         text primary key,
  nome          text not null default '',
  cargo         text not null default 'CLIENTE',
  permissoes    jsonb not null default '[]'::jsonb,
  ativo         boolean not null default true,
  criado_em     timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);
create index if not exists ix_users_cargo on public.users (cargo);

-- ============================================================
-- 2) Grupos do WhatsApp (seção "Nossos Grupos" na landing)
-- ============================================================
create table if not exists public.grupos (
  id         bigint generated always as identity primary key,
  nome       text    not null,
  link       text    not null default '',
  ativo      boolean not null default true,
  ordem      integer not null default 0,
  criado_em  timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- Seed padrão: 4 grupos (links preenchidos pelo dono no painel /admin/grupos)
insert into public.grupos (nome, link, ativo, ordem) values
  ('Coroa',     '', true, 1),
  ('Rubinot',   '', true, 2),
  ('Pokepixel', '', true, 3),
  ('PokeIdle',  '', true, 4)
on conflict do nothing;

-- ============================================================
-- 3) Produto de Intermediação (R$ 5) na loja de itens do site
-- ============================================================
insert into public.itens (nome, descricao, preco, ativo, categoria, ordem)
values (
  'Intermediação BAPZX',
  'Intermediação segura para suas transações in-game. Valor por transação intermediada.',
  'R$ 5,00',
  true,
  'Intermediação',
  0
)
on conflict do nothing;