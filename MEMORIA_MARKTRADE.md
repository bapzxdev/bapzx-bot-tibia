# MEMORIA_MARKTRADE

> Instruções de trabalho exclusivas para a página **MARKTRADE / Troca de Itens**.

## PROTOCOLO DE TRABALHO: UMA PÁGINA POR VEZ

### PÁGINA ATUAL

A página que vamos trabalhar AGORA é exclusivamente:

**https://bapzxdev.github.io/bapzx-portfolio/troca.html**

- Nome da página: MARKTRADE / Troca de Itens.
- Faz parte do fluxo desta página (pedido do dono, implementado na v2.10.5) a
  **tela de detalhes do anúncio** `anuncio.html` — ela é o destino do clique em
  um card da listagem (`.mk-card` virou `<a href="anuncio.html?id=...">`) e
  volta via "← Voltar para os anúncios" (padrão do site), preservando os
  filtros da listagem em `sessionStorage`.

### VERSÃO ATUAL (v2.10.5)

- **Sprite pequeno no detalhe**: `.d-sprite img` usa `height:88px` (era 190px,
  ficava gigante) — `bapzx-portfolio/anuncio.html`.
- **Chip de tier sobre o sprite**: classes `.d-tier-chip` (detalhe) e
  `.mk-tier-chip` (card da listagem) mostram o tier real do item.
- **API `/api/troca` e `/api/troca/<id>`** agora retornam `tier` por anúncio
  (via `_iteminfo`, cache 2 min) — `bapzx/painel.py`.
- Card da listagem (`troca.html`) injeta o chip de tier usando `a.tier`.

### REGRA PRINCIPAL

- **NÃO** avance para nenhuma outra página do projeto até o dono responder
  explicitamente: **"OK, pode ir para a próxima"**.
- Enquanto não houver esse OK, o foco deve permanecer **100% na página troca.html**.
- Mesmo encontrando problemas, melhorias ou inconsistências em outras páginas,
  **NÃO** alterá-las nem começar a trabalhar nelas.
- É permitido **mencionar** que algo está fora da página atual, apenas como
  observação para depois.

### OBJETIVO

Deixar a página atual **completamente pronta** antes de passar para a próxima.

Analisar e trabalhar na página considerando:

- Layout
- Responsividade para celular, tablet e desktop
- UI/UX
- Visual
- Tipografia
- Espaçamentos
- Cores
- Botões
- Cards
- Formulários
- Navegação
- Estados de carregamento
- Estados vazios
- Estados de erro
- Estados de sucesso
- Acessibilidade
- Usabilidade
- Performance
- JavaScript
- HTML
- CSS
- Integração com APIs/backend, quando existir
- Links e navegação
- Consistência visual com o restante do projeto
- Segurança, quando aplicável

### COMO TRABALHAR

1. Fazer uma **auditoria COMPLETA** da troca.html primeiro.
2. **Não sair alterando tudo imediatamente.**
3. Primeiro identificar:

- O que já está funcionando.
- O que está quebrado.
- O que está incompleto.
- O que pode ser melhorado.
- O que está visualmente inconsistente.
- O que pode causar problemas no celular.
- O que pode causar problemas no desktop.
- O que depende de backend/API.
- O que precisa de confirmação do dono antes de ser alterado.

4. Organizar os problemas por prioridade:

- **CRÍTICO**
- **IMPORTANTE**
- **MELHORIA**
- **OPCIONAL**

### EXECUÇÃO

- Após a auditoria, corrigir os problemas da página atual.
- Fazer alterações **SOMENTE** naquilo relacionado à troca.html e aos arquivos
  diretamente necessários para que essa página funcione.
- Se for preciso alterar CSS ou JavaScript **compartilhado** por várias
  páginas, tomar cuidado para **não quebrar as outras**.
- Antes de alterar algo que possa afetar outras páginas: **explicar o impacto
  e pedir confirmação do dono**.

### REGRA DE ESCOPO

Considerar troca.html como uma **"sala fechada"**.

**NÃO** fazer:

- Refatoração geral do projeto.
- Redesign de outras páginas.
- Alterações em páginas que não são necessárias para troca.html.
- Mudanças aleatórias no header/footer global.
- Mudanças em funcionalidades sem relação com a página atual.
- Implementação de novas páginas.
- Melhorias "por conta própria" em outras áreas.

### APÓS CADA ALTERAÇÃO

Verificar novamente a página. Testar:

- Desktop
- Mobile
- Navegação
- Botões
- Formulários
- JavaScript
- Carregamento
- Estados de erro
- Estados vazios
- Integrações
- Console do navegador, quando possível

**Não considerar concluída** uma tarefa só porque o código não tem erro de
sintaxe. Validar o **comportamento real** da página.

### NÃO INVENTAR FUNCIONALIDADES

Se alguma funcionalidade não estiver claramente definida no projeto, **não
inventar regra de negócio**. Exemplos:

- como uma troca deve funcionar;
- quais campos são obrigatórios;
- como os anúncios devem ser publicados;
- qual API deve ser chamada;
- quais permissões o usuário possui.

Nesses casos: **parar e perguntar ao dono**.

### QUANDO CONSIDERAR A PÁGINA PRONTA

Somente considerar troca.html concluída quando:

- não houver problemas críticos conhecidos;
- os principais problemas de UX estiverem resolvidos;
- a página estiver responsiva;
- os fluxos principais estiverem funcionando;
- os erros estiverem tratados;
- os estados de carregamento/erro/vazio fizerem sentido;
- não houver alterações pendentes conhecidas.

Então apresentar um resumo:

- Página concluída
- O que foi corrigido.
- O que foi melhorado.
- O que foi testado.
- O que ainda depende do dono.
- Eventuais limitações.

E **PARAR**. Não avançar para outra página.

### LIBERAÇÃO DA PRÓXIMA PÁGINA

- Somente com o dono escrevendo explicitamente: **"OK, pode ir para a próxima"**.
- Quando o OK for dado, **perguntar** qual página deve ser trabalhada em
  seguida, caso ainda não tenha sido informado.

### REGRA FINAL

- Uma página por vez.
- Uma etapa por vez.
- Não assumir que pode avançar.
- Não considerar silêncio como aprovação.
- Não considerar uma pequena melhoria como autorização para mexer no restante.
- Prioridade absoluta neste momento é: **troca.html**.
- **Começar pela auditoria da página e mostrar o diagnóstico antes de fazer
  mudanças grandes.**