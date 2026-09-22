# MEMORIA COMPRA - Regra de calculo de preco de Tibia Coins

Regra oficial de calculo usada no bot e na IA para converter quantidade de
Tibia Coins em valor em Reais.

## Formula base

O preço oficial é **parametrizado pelo dono** no dashboard (módulo COINS,
v2.8.0): a tabela `coins_config` (linha única id=1) guarda `preco_mil`
(quanto custam 1.000 TC). O valor padrão é R$ 90,00 por 1.000 TC, e enquanto a
migration `supabase_migracao_v123.sql` não for aplicada o bot usa este fallback
legado.

Com `preco_mil` = 90, a formula base fica:

    valor = quantidade x 90 / 1000

(Mas o bot e o painel leem `preco_mil` de `coins_config` — se o dono mudar o
preço no dashboard, a formula vira `quantidade x preco_mil / 1000`.)

## Passo a passo (exemplo com 700 TC)

1. Quantidade desejada: 700 TC
2. Multiplicar a quantidade por 90: 700 x 90 = 63.000
3. Dividir por 1.000: 63.000 / 1.000 = 63
4. Valor final: R$ 63,00

Outros exemplos:
- 500 TC = 500 x 90 / 1.000 = R$ 45,00
- 1.000 TC = 1.000 x 90 / 1.000 = R$ 90,00
- 800 TC = 800 x 90 / 1.000 = R$ 72,00
- 1.500 TC = 1.500 x 90 / 1.000 = R$ 135,00

## Regra de prioridade

- Quantidades que existem na Tabela de Precos oficial (dicionario PRICES no
  bot.py: 100, 250, 500, 1.000 e 2.500 TC) usam o valor da tabela.
- Qualquer outra quantidade usa a forma base acima (quantidade x preco_mil /
  1.000), mostrando o calculo passo a passo.
- O preco (PRICES e preco_mil) e 100% sobreposto pelo que estiver em
  `coins_config.preco_mil` do Supabase (v2.8.0), se a tabela existir. O painel
  `/admin/coins` e a fonte oficial; sem a migration, vale o fallback de R$ 90.

## Limites de compra

- O pedido e bloqueado pelo bot (`_coins_check`) se `coins_config.status =
  'pausado'` ou se a quantidade ficar fora de `[min_compra, max_compra]`
  (padrao 100 a 50000). Sem a tabela, nenhum bloqueio e aplicado (legado).

## Onde esta aplicada

1. Painel administrativo (`painel.py` -> `/admin/coins`): cards de COINS
   disponiveis / Preco por 1.000 / Status / Ultima atualizacao; form de edicao
   (estoque, preco, limites, status, observacao); calculadora JS
   `qtd x preco_mil / 1000`; historico em `coins_historico` (toda mudanca).
2. Prompt da IA (bot.py -> ask_ai): responde precos fora da tabela com a forma,
   mostrando o calculo passo a passo, usando preco_mil dinâmico.
3. Registro do pedido (bot.py -> calc_price, usado em extract_order_details):
   grava o preco calculado (dinâmico via preco_mil) na criacao do pedido —
   o preco fica congelado na ordem.
4. Tabelas de preco do bot (bot.py -> price_table_text / price_table_compact)
   e a persona (persona.txt via load_persona/_persona_precos): sempre usam o
   preco_mil atual.
5. Este arquivo funciona como memoria do projeto junto com o MEMORIA.md.