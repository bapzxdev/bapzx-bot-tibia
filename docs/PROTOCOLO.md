PROTOCOLO DE CONTINUIDADE
================================================================================
Regra da dupla "assistente + dono" para NUNCA nos perdermos: em qualquer nova
sessão, saber em 10 segundos onde paramos e exatamente o que fazer a seguir.
Obrigatório nos 15 dias de construção até a venda e depois dela também.

================================================================================
1. CHECK-IN (toda sessão começa assim)
================================================================================
Ao abrir o opencode, a conversa declara projeto e dia, por exemplo:
  "bot-negocio, dia 4 de 15, continuar"

O assistente DEVE, nesta ordem:
  a) ler AGENTS.md (raiz) e PROTOCOLO.md;
  b) ler ROADMAP-15DIAS.md e conferir o contador de dias (log diário);
  c) ler as memórias do projeto (MEMORIA.md, MEMORIA_COMPRA.md e
     MEMORIA_SEGURANCA.md, quando existirem);
  d) ler o bloco "PROTOCOLO DE REENTRADA" do projeto;
  e) responder em até 5 linhas: Onde paramos / Próximo passo / Dias restantes.

================================================================================
2. DURANTE A SESSÃO
================================================================================
Atualizar as memórias conforme as coisas acontecem (decisões, testes,
versões, pendências). Nunca acumular registros para o final.

================================================================================
3. CHECK-OUT (toda sessão termina assim)
================================================================================
Antes de encerrar, o assistente DEVE:
   a) atualizar o bloco PROTOCOLO DE REENTRADA no docs/memoria/MEMORIA.md do projeto:
     onde paramos / próximo passo (começando com verbo) / arquivos tocados /
     bloqueios / dias restantes;
  b) registrar o dia no LOG DIÁRIO do ROADMAP-15DIAS.md;
  c) commitar e dar push (um commit por bloco lógico), se houver alterações;
  d) encerrar e confirmar.

PALAVRA MÁGICA DE CHECK-OUT:
  "FIM DE SESSÃO"
  Quem ler o bloco de reentrada sabe que ele está atualizado.

================================================================================
BLOCO PROTOCOLO DE REENTRADA (template - fica no topo de cada MEMORIA.md)
================================================================================
## PROTOCOLO DE REENTRADA (atualizado no último check-out)
  - Onde paramos: <resumo de 1-2 linhas>
  - Próximo passo: <verbo> <objetivo exato>
  - Arquivos tocados: <lista>
  - Bloqueios: <nenhum | o que travou>
  - Dias restantes: <N de 15>

================================================================================
REGRAS DE SANIDADE
================================================================================
- O "próximo passo" NUNCA é inventado: ele sai do bloco de reentrada,
  das pendências do MEMORIA.md ou do ROADMAP.
- Pedido fora do roteiro: o assistente faz, registra no log do dia e
  atualiza o ROADMAP se o plano mudar.
- Bloqueio encontrado: registrar no bloco de reentrada. O CHECK-IN seguinte
  sempre pergunta primeiro: "quer resolver o bloqueio ou pular?"
- Segurança: nada de chaves/tokens/dados de venda em arquivo, conversa de
  demo, commit ou backup (ver MEMORIA_SEGURANCA.md).