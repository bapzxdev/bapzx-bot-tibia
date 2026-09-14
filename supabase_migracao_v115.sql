-- BAPZX bot-negocio v1.15.0
-- Painel de administração: itens à venda, visualizações (visitas) e auditoria.
-- Rode no Supabase SQL Editor.

-- 1) Tabela de itens à venda (loja do site)
create table if not exists public.itens (
  id         uuid    not null default gen_random_uuid() primary key,
  nome       text    not null,
  descricao  text    not null default '',
  preco      text    not null default '',
  imagem     text    not null default '',
  ativo      boolean not null default true,
  categoria  text    not null default 'geral',
  ordem      integer not null default 0,
  criado_em  timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

-- 2) Visualizações do site (páginas do portfólio)
create table if not exists public.visitas (
  id       bigint generated always as identity primary key,
  pagina   text    not null default '/',
  referer  text    not null default '',
  pagina_resolucao text not null default '',
  criado_em timestamptz not null default now()
);

-- 3) Auditoria de ações do administrador
create table if not exists public.audit_log (
  id         bigint generated always as identity primary key,
  email      text    not null,
  acao       text    not null,
  detalhes   text    not null default '',
  ip         text    not null default '',
  criado_em  timestamptz not null default now()
);

-- 4) Bucket público para imagens dos itens
insert into storage.buckets (id, name, public)
values ('itens', 'itens', true)
on conflict (id) do nothing;

-- 5) Política: leitura pública das imagens do bucket 'itens'
drop policy if exists "Public read imagens itens" on storage.objects;
create policy "Public read imagens itens"
  on storage.objects for select
  using (bucket_id = 'itens');

-- 6) Índices para consultas frequentes do painel
create index if not exists ix_visitas_criado_em on public.visitas (criado_em);
create index if not exists ix_audit_criado_em    on public.audit_log (criado_em);
create index if not exists ix_itens_ativo_ordem  on public.itens (ativo, ordem);