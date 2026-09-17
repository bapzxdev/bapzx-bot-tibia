-- BAPZX bot-negocio v2.7.0
-- Área Service (diário de serviços manuais do dono)
-- + Área Segurança (histórico de login, sessões ativas e logouts)
-- + coluna whatsapp no perfil (clientes).
-- Rodar no Supabase > SQL Editor > New query e executar o bloco inteiro.

-- ============================================================
-- 1) Services manuais (área exclusiva do dono, "meus services")
--    data: dia do serviço | valor: preço cobrado | forma_pagamento: pix|coins
--    status: pendente|concluido
-- ============================================================
create table if not exists public.servicos_manuais (
  id              bigint generated always as identity primary key,
  email           text not null default '',
  data            date not null default current_date,
  hora            text not null default '',
  servico         text not null default '',
  nome_cliente    text not null default '',
  whatsapp        text not null default '',
  valor           numeric(12,2) not null default 0,
  forma_pagamento text not null default 'pix',
  horas           numeric(4,1) not null default 0,
  observacao      text not null default '',
  status          text not null default 'pendente',
  criado_em       timestamptz not null default now(),
  atualizado_em   timestamptz not null default now()
);
create index if not exists ix_servicos_manuais_data on public.servicos_manuais (data desc);
create index if not exists ix_servicos_manuais_status on public.servicos_manuais (status);

-- ============================================================
-- 2) Sessões de login (histórico de acesso + segurança)
-- ============================================================
create table if not exists public.sessoes (
  id            bigint generated always as identity primary key,
  sid           text not null default '',
  email         text not null default '',
  ip            text not null default '',
  user_agent    text not null default '',
  criado_em     timestamptz not null default now(),
  ultimo_acesso timestamptz not null default now(),
  encerrado_em  timestamptz,
  ativo         boolean not null default true
);
create index if not exists ix_sessoes_email on public.sessoes (email);
create index if not exists ix_sessoes_criado on public.sessoes (criado_em desc);
create index if not exists ix_sessoes_sid on public.sessoes (sid);

-- ============================================================
-- 3) WhatsApp no perfil do cliente (área Clientes)
-- ============================================================
alter table public.profiles add column if not exists whatsapp text default '';

-- Verificação: as tabelas acima devem aparecer em
--   supabase_migracao → Table Editor.
