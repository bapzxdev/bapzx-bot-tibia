# Uptime monitor gratuito (item 19 do checklist 20 itens)

## Por que
Hoje só descobrimos queda quando alguém tenta usar (ou pelo erro 500 no
Telegram). Um monitor externo pinga o site de tempos em tempos e avisa no
e-mail/Telegram quando cai. Plano gratuito cobre 50 monitores.

## Passo a passo (5 min, conta do dono)

1. Criar conta grátis em https://uptimerobot.com (ou https://betterstack.com).
2. Add New Monitor:
   - Monitor Type: `HTTP(s)`
   - Friendly Name: `BAPZX Bot`
   - URL: `https://bapzx-bot-tibia.onrender.com/health`
   - Monitoring Interval: `5 minutes`
   - Keyword check (opcional, recomendado): keyword `bot ok` (alerta se a
     página responder sem o texto = app no ar mas com erro).
3. Em Alert Contacts: adicionar seu e-mail (e Telegram, se quiser — o
   UptimeRobot tem integração nativa com Telegram).
4. Salvar. Pronto: se o Render cair ou o app travar, você recebe o alerta.

## Observações
- O `/health` é leve (só devolve a versão), então o ping não gera custo.
- Cold start do Render (plano free) pode dar 1 timeout isolado após
  inatividade — é normal; o alerta só importa se repetir.
- Quando criar, anote a data aqui: monitor criado em ____/____/________.
