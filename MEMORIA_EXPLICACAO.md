# Memória de explicação — Como trocar as credenciais do Supabase no Render

Este procedimento é para quando o bot em produção (Render) estiver com a URL/chave
do Supabase diferentes das do `.env` local. Sintoma: o `/api/itens` do site dá
erro 500 em produção, ou o painel admin não carrega as tabelas, mesmo com o
`/health` respondendo `bot ok` no Render.

A forma mais simples e segura é a pelo site do Render. Não precisa mexer em código,
não precisa reiniciar nada manualmente — o Render reinicia sozinho ao salvar.

---

## Passo a passo — onde clicar

1. Abra o navegador e entre no site do Render:
   `https://dashboard.render.com`

2. Faça login com a conta Google que criou o projeto.

3. Na página inicial (Dashboard), você verá a lista de serviços. Você vai clicar no
   serviço do bot. O nome aparece como um cartão. Procure por um nome parecido com
   **`bapzx-bot-tibia`** (o cartão que fica com "Web Service"). Clique nele.

   > Print para conferir que está no lugar certo: a tela seguinte tem um menu
   > lateral (ou aba horizontal) com várias opções.
   > Você está no lugar certo se a parte principal mostrar algo com "Latest Deploy",
   > "Live" ou "Health Check Status".

4. No menu do serviço, clique em **`Environment`**.
   (A tradução do Render costuma ficar em inglês: o menu tem itens como
   Overview, **Environment**, **Logs**, Events, etc.)

   > Você está no lugar certo se aparecer a lista de variáveis:
   > "Key" e "Value". Pode estar vazio ou com valores antigos.

5. Procure na lista pela linha cuja coluna Key é **`SUPABASE_URL`**.
   - Se a linha existir: clique no campo **Value** dela e apague o valor antigo
     (pode selecionar tudo e apagar).
   - Se NÃO existir: clique no botão **`Add Environment Variable`**
     (um botão que fica na parte de cima da lista). Na linha nova, escreva na
     coluna Key: `SUPABASE_URL`.

   Depois, no Value, coloque exatamente:
   ```
   https://wtgzsurppwwrzhctnnfa.supabase.co
   ```
   Cuidado para não deixar espaço no começo ou no fim.

6. Faça o mesmo para a linha cuja Key é **`SUPABASE_KEY`**:
   - Se existir, clique no Value e apague o valor antigo.
   - Se não existir, use "Add Environment Variable" de novo.
   - Escreva na Key: `SUPABASE_KEY`
   - No Value, cole exatamente:
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0Z3pzdXJwcHd3cnpoY3RubmZhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTAwNjg0MywiZXhwIjoyMTA0NTgyODQzfQ.LVFxUfrT1jqdxSTlXCTw1SiR68Qcy8brEznNyUxTNrw
   ```

7. ATENÇÃO — não apague outras linhas da lista. Só altere/adicione essas duas.
   Se alguma outra variável tiver nome diferente (ex.: `SUPABASE_KEY2`,
   `SupabaseUrl`), não mexa — essas não são usadas.

8. Depois de terminar, o botão de salvar fica no **canto de baixo da página**:
   um botão azul **`Save Changes`**. Clique nele.

   > O Render vai mostrar um "confirm" e pode pedir para clicar de novo no
   > **`Save Changes`** (confirmação).
   > Pode demorar um pouco: ele fica "Updating..." e depois "Live" de novo.

9. Não precisa rodar deploy manual após isso — salvar as variáveis já reinicia o
   serviço sozinho. Se aparecer a dúvida de "Restart", basta deixar o processo seguir.

---

## Como verificar se deu certo

1. Espere o serviço voltar para **"Live"** (a bolinha verde no topo).
2. Abra no navegador: `https://bapzx-bot-tibia.onrender.com/health`
   - Deve aparecer algo com `bot ok` e a versão (ex.: `v1.15.0`).
3. Abra no navegador: `https://bapzx-bot-tibia.onrender.com/api/itens`
   - Deve aparecer algo como: `{"itens":[],"ok":true}`
   - Se aparecer `{"ok":false,...}` ou `erro`, as credenciais ainda não estão certas.
4. Abra a página de Itens do site (ex.: `https://bapzxdev.github.io/bapzx-portfolio/itens.html`).
   - Deve carregar o botão de "Comprar" como "em preparação" e NÃO mostrar erro.
5. O painel admin (login Google) deve carregar o dashboard com os totais zerados
   (0 itens, 0 visitas) em vez de dar erro 500.