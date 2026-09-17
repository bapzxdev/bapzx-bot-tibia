-- BAPZX bot-negocio v2.7.1
-- Serviços manuais: cálculo do valor cobrado = valor_hora * horas - desconto
-- Novas colunas em public.servicos_manuais.
-- Rodar no Supabase > SQL Editor > New query e executar o bloco inteiro.

alter table public.servicos_manuais add column if not exists valor_hora numeric(12,2) not null default 0;
alter table public.servicos_manuais add column if not exists desconto numeric(12,2) not null default 0;

-- Backfill: registros antigos (antes do cálculo automático) recebem o valor/hora
-- estimado (valor total / horas) e desconto 0, mantendo o valor total salvo.
update public.servicos_manuais
set valor_hora = round(cast(valor as numeric(12,2)) / horas, 2)
where valor_hora = 0 and horas > 0;