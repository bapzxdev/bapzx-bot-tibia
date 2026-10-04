ROADMAP - 15 DIAS PARA VENDER (prazo estendido: +2 meses -> meta 16/11/2026)
================================================================================
Estado atual (17/09/2026): bot v2.7.1 (Service com valor cobrado automÃ¡tico
= valor/hora Ã— horas âˆ’ desconto + correÃ§Ã£o do bug de totais estourados do
`_parse_brl`; v2.7.0 Service + SeguranÃ§a concluÃ­das e v121 APLICADA pelo dono;
resta aplicar a migration v122 no SQL Editor), portfÃ³lio v3.7 no ar, v120 de
cupons APLICADA, memÃ³rias no lugar. Meta: programa pronto, seguro e vendendo
Tibia Coins.
PRAZO (a pedido do dono, 16/09): bloco estendido em +2 meses â€” nova meta
16/11/2026 (era 24/09/2026). Contador de dias restantes no bloco de
reentrada; log diÃ¡rio no final.

LEGENDA: [ ] a fazer | [x] feito | [~] em andamento | [!] bloqueado
================================================================================
FASE A - Colocar ordem na casa (dias 1-3)
================================================================================
[x] Webhook, pedido estruturado, persistÃªncia no Supabase
[x] Comandos (/preco, /vendedor, /ajuda, /quemsomos) + IA sem asteriscos
[x] 4 dados de compra explÃ­citos (char, quantidade, mundo, Pix)
[x] Dashboard de vendas (/dashboard)
[x] Regra de preÃ§o (1.000 TC = R$ 90) + MEMORIA_COMPRA.md
[x] MemÃ³ria de seguranÃ§a + token rotacionado
[~] Migrar pedidos.json para o Supabase (histÃ³rico completo) -> FEITO
[x] Migrar pedidos.json para o Supabase (scripts/migrar_pedidos.py)
[ ] Pedido assÃ­ncrono: cliente informa mundo/char depois do valor

================================================================================
FASE B - Validar a venda de verdade (dias 4-7) [!] validaÃ§Ã£o com cliente
      real VETADA pelo dono atÃ© tudo ajustado (11/09); testes seguem
      simulados/desenvolvimento
===============================================================================
[!] Resposta da IA confirmada em atendimento real
[x] Fluxo de pagamento: pedido pendente -> texto Pix -> /pago -> /entregue com aviso ao cliente
[x] CondiÃ§Ãµes de entrega definidas (11/09): trade in-game em atÃ© 10 minutos
    apÃ³s a confirmaÃ§Ã£o do pagamento. Limite por venda ainda a revisar.
[x] Texto final de confirmaÃ§Ã£o (11/09): resumo do pedido (tc, valor, mundo,
    char, validade do QR, e-mail) enviado junto com o QR gerado.
[~] Pix automÃ¡tico via Mercado Pago (v1.6.0) implementado e testado local;
    validaÃ§Ã£o com cliente real VETADA por enquanto

================================================================================
FASE C - DivulgaÃ§Ã£o (dias 8-12) [!] VETADA pelo dono atÃ© tudo ajustado (11/09)
===============================================================================
[x] Link pÃºblico e QR code do bot prontos (landing no / + QR e botÃ£o no
    https://bapzx-bot-tibia.onrender.com/ e link t.me/bapzx_bot)
[!] Ficha de divulgaÃ§Ã£o (o que falar, onde postar)
[!] Post em comunidades/grupos de Tibia
[!] Avaliar o WEB DIVULGADOR para divulgaÃ§Ã£o programada
[~] Planilha de clientes (Google Sheets): modelo v2 pronto + Plano B + AUTOMAÃ‡ÃƒO
    v1.8.0 implementada e testada (bot -> Apps Script Web App -> linha por
    id_pedido, cria/atualiza). Falta SOMENTE a parte manual do dono: colar
    CODIGO_APPS_SCRIPT.js em Apps Script, rodar configurar() com o SHEET_TOKEN
    e implantar o Web App; colar a URL em SHEET_WEBAPP_URL (.env + Render).

================================================================================
FASE D - OperaÃ§Ã£o (dias 13-15)
===============================================================================
[x] Scan de seguranÃ§a com OWASP ZAP (13/09) â€” primeiro scan entregue; Ãºnico
    achado corrigido (v1.14.16: 404/405 limpos sem aviso ao dono)
[ ] Limpar dados de teste do banco (manter sÃ³ o que for real)
[ ] RevisÃ£o final de segredos e exposiÃ§Ã£o (perguntas do SEC-001)
[ ] Meta da PRIMEIRA VENDA acompanhada no /dashboard
[ ] Ajustar persona/preÃ§os com base no que aconteceu

================================================================================
LOG DIÃRIO (preencher no check-out de cada sessÃ£o)
================================================================================
Dia 1 (09/09): bot estruturado testado/planejado; primeiro deploy no Render.
Dia 2 (10/09): v1.2.1 -> v1.4.0 (comandos, 4 dados, dashboard), v1.4.1
                (regra de preÃ§o), memÃ³rias (compra + seguranÃ§a) e rotaÃ§Ã£o do
                token Telegram. PROTOCOLO.md e ROADMAP criados.
Dia 3 (10/09): migraÃ§Ã£o do pedidos.json para o Supabase concluÃ­da
                (script scripts/migrar_pedidos.py; 5 histÃ³ricos inseridos,
                total de 11 no banco, arquivo local esvaziado). Fase A
                encerrada. PrÃ³ximo: Fase B (validar venda real e definir
                identificaÃ§Ã£o de pagamento via Pix).
Dia 4 (10/09): fluxo de pagamento implementado â€” colunas de status no
                Supabase (migracao_status.sql), texto Pix, /pago e /entregue
                no chat do dono, dashboard com faturado sâ”¤ de pagos e
                coluna status. Testado local (pedido 1500 tc -> pago ->
                entregue). Prâ”ximo: validar com primeiro cliente real
                + adicionar PIX_KEY.
Dia 6 (11/09, v1.11.1): v1.11.0 Google Login (OAuth) + areas de CLIENTE e ADMIN; CONCLUIDO E VALIDADO AO VIVO: supabase_migracao_v111.sql aplicado, credencial Google criada (Web app + redirect URI), envs no Render, o dono LOGOU com o Google no /admin como admin e na /cliente (Minha conta) com pedido de teste (apos removido). Portfolio v3.0 multi-paginas com card Area do cliente. Pendente: publish do app Google pra clientes reais, itens/prices reais do portfolio, Fase C/1a venda (vetada).
Dia 6 (continuacao, v1.11.2): AUDITORIA COMPLETA de falhas/seguranca (a pedido do dono): sem segredos vazados em nenhum repo; deps sem CVE (Authlib 1.8.0 corrige os exploits 2026, Flask 3.1.3); 4 falhas corrigidas: XSS no /dashboard (escapado), referer exato no /admin/marcar (urlparse), sessao permanente 7 dias + headers nosniff/DENY/same-origin, secret no webhook Telegram (TELEGRAM_WEBHOOK_SECRET). Testes tudo verde.
Dia 6 (continuacao, v1.11.3): usuario do GitHub renomeado para bapzxdev (portf folio agora em https://bapzxdev.github.io/bapzx-portfolio/); PORTFOLIO_URL do bot atualizado, remotes locais e referencias (manual.txt, docs, launchers) migrados para bapzxdev. TELEGRAM_WEBHOOK_SECRET ativo no Render verificado ao vivo (webhook 403 sem o header certo).
Dia 7 (12/09, v1.12.0): VALIDACAO DE PERSONAGEM no pedido (pedida pelo dono). Antes de salvar, o bot consulta a API publica do RubiNot (/api/characters/search?name=...); achou -> mostra nome/level/vocacao/mundo e pede confirmacao; mundo do cliente diferente do oficial -> avisa e so confirma com ok; nao achou -> bloqueia pedindo correcao; API fora -> segue normal. Confirmado, salva char/mundo OFICIAIS. Interruptor por env RUBINOT_VALIDATE (default on). Suites test_rubinot_v112 (8 cenarios) + v1.7.0 + auth todas verdes. Pendente: deploy no Render + teste ao vivo do fluxo com confirmacao.
Dia 7 (continuacao, v1.13.0): testes ao vivo revelaram e resolveram: (1) webhook do Telegram SEM secret -> respostas reais do Telegram davam 403; re-registrado com secret. (2) RubiNot bloqueia o IP do Render (403 HTML proprio) tanto com requests quanto curl_cffi -> consulta inviavel do servidor. (3) Fix parse "rc". (4) v1.13.0: confirmacao MANUAL obrigatoria quando API fora ("Confere os dados acima? Responda SIM ou NÃƒO."). Fluxo validado ao vivo: SIM salva (id 21), NAO cancela; Supabase zerado dos testes. Pendente: decidir se contata staff do RubiNot por acesso a API; publish Google OAuth; Fase C vetada.
Dia 10 (12/09, v1.14.0): 3 melhorias aprovadas pelo dono implementadas e com testes verdes: (1) BOTOES INLINE no Telegram - confirmacao de personagem com [SIM]/[NAO] clicaveis e menu no /start com [Comprar RC] [/preco] [/vendedor]; handler de callback_query (answer + editMessageReplyMarkup). (2) FEEDBACK POS-ENTREGA apos /entregue (nota 1-5 e/ou comentario) salvo no pedido (colunas feedback/feedback_score - migracao supabase_migracao_v114.sql a aplicar no Supabase) e avisado ao dono. (3) RELATORIO MENSAL: /relatorio (dono) + envio automatico todo dia 1 via thread. Pendente: aplicar migracao SQL, testar tudo ao vivo, publish Google OAuth, manual.txt e 1a venda (Fase C vetada).
Dia 10 (continuacao s2, v1.14.1): AUDITORIA DE SEGURANCA a pedido do dono (e-mails estranhos). NENHUM segredo real vazado (repos, historico, arvore, backup, .env gitignored); colaborador unico = dono; commits todos do dono; login Google ativo; cookie de sessao com SECRET_KEY padrao REJEITADO em prod. V1.14.1 aplicou reforcos: throttle por IP no /webhook/mp (429) e validacao de host no /login (ALLOWED_HOSTS). Deps sem CVE; GitHub vulnerability alerts desativados (nao era Dependabot). E-mails estranhos provavelmente phishing de terceiros -> a confirmar pelo dono (remetente/assunto).
Dia 10 (continuacao s3, v1.14.2): mensagem de boas-vindas atualizada a pedido do dono: "Boa tarde! Seja bem-vindo a BAPZX." + comandos principais /compra /site /info + service R$20/h. Novos comandos /compra, /site, /info implementados; menu inline [Comprar RC] [/site] [/info] [/vendedor]. Testes verdes; deploy no Render.
Dia 10 (continuacao s4, v1.14.3): CORRECAO DO MOJIBAKE reportado pelo dono ("confirmaÃƒÂ§ÃƒÂ£o", letras erradas). Causa: bot.py com strings duplamente codificadas (UTF-8/cp1252) â€” 58 literais corrigidos (37 via tokenize, 15 via busca de bytes, 6 manuais: emojis SERVICO/HELP/NOVO PEDIDO, prompt IA "PREÃ‡OS", dashboard "Ãºltimos/Ãºltimos", "estÃ¡ no mundo"). Audit cp1252 final: 0; bytes hex das mensagens conferidos. Migracao supabase feedback/feedback_score APLICADA pelo dono e verificada. Teste ao vivo iniciado: /webhook aceitou pedido TESTE-VIVO (200); callback char_sim deu 500 em prod (a investigar no retorno; sem repro local). Suites todas verdes. Pendente: investigar 500 do char_sim, concluir fluxo ao vivo (inline/feedback/relatorio), publish Google OAuth, 1a venda (Fase C vetada).
Dia 10 (continuacao s5, v1.14.6, 12/09): fluxo completo do teste ao vivo CONCLUIDO. /pago e /entregue voltaram a funcionar apos dono inserir TELEGRAM_OWNER_CHAT_ID na env do Render (antes 'Comando indisponivel'); valido ao vivo: id 22 pendente->pago->entregue, /relatorio 200. Loop end-to-end no Supabase: order->char_sim->email->/pago->/entregue->feedback (nota 5 + texto em feedback/feedback_score). char_sim dava 500 intermitente apos salvar (sem repro local com Supabase real) -> v1.14.5 blindou chamadas ao Telegram (try/except) e v1.14.6 errorhandler global loga+avisa dono no Telegram (ultima rodada char_sim 200). Suite v170 reconstruida (21 checagens OK). Portfolio v3.1 no ar: hero vendedor, Como funciona, Confianca, FAQ objecoes, Venda de Itens fora do menu (sem dados reais). ajustes 1.14.4: BAPZX = 'loja que revende Rubini Coins' em /info, persona e site. Pendentes: limpeza pedidos de teste 22/32/33/35; publish Google OAuth e 1a venda (Fase C vetada); monitorar 500 (errorhandler).
Dia 10 (fechamento, v1.14.7, 12/09): nova mensagem de entrada de compra (COMPRA_TEXT) exatamente no formato do dono - 3 dados (char, quantidade, pagamento Pix), exemplo sem mundo, /preco e entrega 10min; prompt da IA alinhado (3 dados, sem mundo). Parser continua aceitando 'mundo X' se o cliente escrever; confirmacao manual mostra 'Mundo: -' sem mundo. Deploy OK (/health v1.14.7; /compra 200 ao vivo). Suite v170: 21 OK. Pendentes: limpeza pedidos teste (22/32/33/35/36), publish Google OAuth, 1a venda (Fase C vetada).
Dia 10 (fechamento 2, v1.14.8, 12/09): sequencia de compra com 2 mensagens - (1) COMPRA_TEXT 3 dados (v1.14.7) e (2) nova SITE_TEXT com links clicaveis Markdown (preco, entrega, site oficial BAPZX, compra, vendedor) enviada depois do COMPRA_TEXT em /compra e menu_comprar; /site e menu_site tambem usam o novo texto. send_message ganhou parse_mode=Markdown (validado na API do Telegram: HTTP 200). Deploy OK (/health v1.14.8). Suite v170: 21 OK. Pendentes: limpeza pedidos teste (22/32/33/35/36), publish Google OAuth, 1a venda (Fase C vetada).
Dia 10 (fechamento 3, v1.14.9, 12/09): /preco reescrito no formato pedido (tabela BAPZX COINS com ,00, Pagamento Pix, Entrega trade in-game 10min, /compra e /vendedor); PRICES com ,00; tabela compacta separada p/ prompt da IA. Deploy OK (/health v1.14.9; /preco ao vivo 200). Suite 21 OK. Pendentes: limpeza pedidos teste (22/32/33/35/36), publish Google OAuth, 1a venda (Fase C vetada).
Dia 10 (fechamento 4, v1.14.10, 12/09): confirmacao do pedido no formato padrao (CONFIRMACAO DO PEDIDO com Valor/Preco/Pix/Char + QR) via novo helper; QR gerado IMEDIATAMENTE ao confirmar (removido passo de pedir e-mail; pix usa ADMIN_EMAILS como e-mail padrao); 'trade in-game' removido dos textos ao cliente (preco, DELIVERY_NOTE, pagamento confirmado). Validado ao vivo: pedido 47 -> confirmacao -> SIM -> cobranca MP pending R (QR enviado). Suite v170 22 OK. Pendentes: limpeza pedidos teste (22/32/33/34/35/36/37/38/47), publish Google OAuth, 1a venda (Fase C vetada).
Dia 10 (fechamento 6, v1.14.13, 12/09): PARSER TOLERANTE a formato compacto corrige o loop ao vivo (dono digitou 'inmortals - 1250 - pix' e o bot nao reconhecia - caia na IA, e 'sim' respondia com a saudacao fixa). parse_amount com fallback de numero pelado, char com fallback (remove numeros/stop-words/intencao), looks_like_order com dicas (pix/pagamento/rc/tc/coins), bloqueio de pedido incompleto (pede qtd ou char em vez de salvar lixo - pedido 48 era esse lixo). Validado ao vivo: 'inmortals - 1250 - pix' -> CONFIRMACAO DO PEDIDO; 'sim' -> pedido 49 (inmortals, 1250, R,50) + QR MP pending 112,50. Deploy OK (/health v1.14.13). Suite v170: 28 OK; test_rubinot_v112 alinhado (bloqueio sem char + CONFIRMACAO DO PEDIDO). Pendentes: limpeza pedidos teste (22/32/33/34/35/36/37/38/47/48/49), publish Google OAuth, 1a venda (Fase C vetada); dono repetir o fluxo no celular.
Dia 10 (fechamento 7, v1.14.14, 12/09): API DO RUBINOT REMOVIDA a pedido do dono ('vai ser muito empenho entrar em contato com os caras'; fluxo rodou perfeito). Removidos: constantes RUBINOT_*, rubinot_char_info, ramos de validacao no pedido, override de char/mundo por dados oficiais; curl_cffi fora do requirements. Confirmacao agora usa o CHAR DIGITADO pelo cliente (botoes SIM/NAO) e o QR sai na hora ao confirmar, sem consulta externa. Validado ao vivo: 'inmortals - 1250 - pix' -> CONFIRMACAO DO PEDIDO; 'sim' -> pedido 51 (inmortals, 1250, R,50) + QR MP pending. Deploy OK (/health v1.14.14). Suites verdes: v170 27 OK, rubinot reescrita (12 checagens, agora sem API), parse_rc, auth, planilha. Pendentes: limpeza pedidos teste (22/32/33/34/35/36/37/38/47/48/49/50/51), publish Google OAuth, 1a venda (Fase C vetada).
Dia 10 (fechamento 8, v1.14.15, 12/09): corrigido ERRO 500 em /webhook reportado pelo dono (teste real). Causa: duplo toque/reenvio do botao SIM com AWAITING_CHAR vazio -> KeyError em notify_owner (reproduzido local: 'KeyError: chat_id'). Guarda 'if not pending: return' no topo de _finalizar_confirmacao_char. Validado ao vivo: 2 callbacks char_sim -> 200, sem novo pedido. Deploy OK (/health v1.14.15). Suites verdes: v170 27 OK, rubinot 6 cenarios + duplo callback. Tambem: site bapzx-portfolio ja e responsivo (viewport + @media) - ok no celular. Pendentes: limpeza pedidos teste (22/32/33/34/35/36/37/38/47/48/49/50/51), publish Google OAuth, 1a venda (Fase C vetada).
Dia 10 (fechamento 5, v1.14.11+1.14.12, 12/09): confirmacao sem tracos e sem linha extra (v1.14.11); persona sem pedir mundo/e-mail/trade; MENSAGEM DE ABERTURA da IA fixada no formato do dono (v1.14.12, bloco no persona). IA que pedia o Mundo era efeito de mensagem nao reconhecida como pedido + persona antiga. Suite 22 OK. Deploy OK (/health v1.14.12). Pendentes: limpeza pedidos teste (22/32/33/34/35/36/37/38/47), publish Google OAuth, 1a venda (Fase C vetada).
Dia 5 (11/09): v1.6.0 â€” Pix automÃ¡tico com Mercado Pago. Conta pessoal do
                dono conectada (token de produÃ§Ã£o APP_USR validado), pedido
                agora pede e-mail do cliente, gera QR Code (imagem + copia
                e cola) e o webhook /webhook/mp confirma o pagamento
                sozinho. Testado local (fluxo pedido->email->QR; webhook
                mock: pedido->pago). Tabela pedidos limpa (dados de teste).
                v1.7.0 â€” revisÃ£o de seguranÃ§a e preparaÃ§Ã£o: landing pÃ¡gina
                pÃºblica no / (preÃ§os + como comprar + QR do bot), /health,
                /dashboard e /pedidos protegidos por DASHBOARD_KEY, rate
                limit anti-spam, extraÃ§Ã£o de char corrigida. Suite de
                testes passou. Pendente: configurar DASHBOARD_KEY no Render
                e validar/suportar primeiro cliente real.
Dia 13 (13/09, ambiente): 5 servidores MCP instalados/configurados no opencode
                (opencode.jsonc global): filesystem (npx, aponta p/ MEUS
                PROJETOS), github (remoto oficial api.githubcopilot.com via
                env GITHUB_TOKEN), context7 (npx @upstash/context7-mcp),
                playwright (npx @playwright/mcp, BROWSER=chromium), sqlite
                (venv mcp-sqlite-venv com mcp==1.28.1; e necessario esse pin
                por incompatibilidade com SDK mcp 2.x). mcp_timeout 120s.
                Todos validados (filesystem/context7/playwright resolveram
                via npx; sqlite respondeu initialize+tools; github remoto
                aguarda token). Pendente dono: setar GITHUB_TOKEN (setx),
                rodar 'npx playwright install chromium' e REINICIAR o opencode
                (config nÃ£o faz hot-reload). gh mcp nÃ£o existe no gh 2.100.
Dia 13 (13/09, ambiente, sessao 2): 5 MCPs validados e config global otimizada
                (~/.config/opencode/opencode.jsonc). GITHUB_TOKEN criado, setx
                persistido e validado (login bapzxdev; MCP github remote
                api.githubcopilot.com autenticando). Chromium do Playwright
                instalado (chrome 153). Config: compaction auto tail 15,
                tool_output cap 200/16KB, 3 references (POKEMON, POKE IDLE,
                DIVULGADOR), permission git allow / webfetch-websearch ask,
                sqlite MCP agora em DB persistente (nao mais temp).
                Pendentes: REINICIAR opencode p/ MCP github valer; 2 tokens
                vazaram em chat 13/09 (1 classic ghp_..., 1 fine-grained
                github_pat_...) -> dono orientado a REVOGAR; continuar fluxo
                do bot (celular, limpeza testes, Google OAuth, 1a venda).
Dia 6 (__/__): -
Dia 6 (__/__): -
Dia 7 (__/__): -
Dia 8 (__/__): -
Dia 9 (__/__): -
Dia 10 (__/__): -
Dia 11 (__/__): -
Dia 12 (__/__): -
Dia 13 (__/__): -
Dia 14 (__/__): -
Dia 15 (15/09, v1.16.2): BACKUP criado (bapzx-bot-tibia-v1.16.2-backup.zip,
                backups/ â€” cÃ³digo+docs+SQL, SEM .env/segredos, conforme
                RESTAURAR.txt). Plano aprovado pelo dono para v2.0.0:
                (1) RBAC BAPZX ACCESS substituindo ADMIN_EMAILS (cargos
                MASTER/ADMIN/MANAGER/FINANCEIRO/OPERADOR/MODERADOR/SUPORTE/
                CLIENTE, nÃ­veis 100..10, permissÃµes individuais por usuÃ¡rio,
                MASTER sÃ³ por MASTER_EMAILS fixo, audit completo);
                (2) PolÃ­tica de Privacidade (LGPD) + Termos + Reembolso com
                PDF baixÃ¡vel + links no footer da landing e do portfÃ³lio;
                (3) Produto "IntermediaÃ§Ã£o BAPZX R$5" no portfÃ³lio (item,
                sem tocar bot Telegram); (4) WhatsApp nos novos locais;
                (5) Grupos do WhatsApp (Coroa/Rubinot/Pokepixel/PokeIdle) na
                landing com botÃµes, gerenciados em /admin/grupos + /api/grupos.
                PendÃªncia dono: aplicar supabase_migracao_v118.sql quando
                pronta.
Dia 15 (15/09, v2.0.0, RBAC + legal + grupos) â€” DEPLOYADO. Implementado e
                testado: RBAC "BAPZX ACCESS" (rbac.py: cargos MASTER 100..
                CLIENTE 10, permissÃµes padrÃ£o por cargo + individuais jsonb,
                MASTER por MASTER_EMAILS c/ fallback ADMIN_EMAILS), painel
                com /admin/usuarios (CRUD cargos+perms), /admin/audit,
                /admin/grupos (CRUD) e /api/grupos (pÃºblico), sidebar
                filtrada por permissÃ£o; bot.py OAuth resolvendo cargo/perms
                da tabela users; pÃ¡ginas legais LGPD em legais.py
                (/privacidade /termos /reembolso + /privacidade/pdf com
                reportlab); portfÃ³lio v3.3 com seÃ§Ã£o "Nossos Grupos" (via
                /api/grupos, "em breve" sem link) + links legais/WhatsApp no
                footer das 7 pÃ¡ginas; seed de IntermediaÃ§Ã£o R$5 em itens.
                Migration supabase_migracao_v118.sql criada â€” PENDENTE do
                dono no SQL Editor (rotas novas jÃ¡ retornam lista vazia sem
                erro via _fetch_soft). Testes: RBAC 6 checagens, rotas MASTER
                200 / CLIENTE bloqueado, /privacidade*/PDF 200, /api/grupos
                200 vazio, py_compile OK. Deploys: bot 2c82756â†’Render,
                portfÃ³lio cf990b8â†’GitHub Pages.
Dia 13 (13/09, sessao 4, v1.14.16, SEGURANCA): PRIMEIRO SCAN do bot com OWASP ZAP via MCP (skill security-testing): spider + passive + active em bapzx-bot-tibia.onrender.com. Achado real UNICO: rotas inexistentes e post errado davam 500 "erro" em vez de 404/405 (errorhandler(Exception) capturava NotFound/MethodNotAllowed) e CADA probe avisava o dono no Telegram (spam/ruido). Correcao: handlers @app.errorhandler(404) e @app.errorhandler(HTTPException) â€” 404/405 limpos sem alerta; 500 real continua avisando dono. VERSION 1.14.16. Testado local: /xyz->404, /robots->404, /webhook GET->405, /health->200, /->302, /boom->500 c/ aviso (1 chamada ao dono), 404/405 sem aviso (0). Alertas Medium do ZAP (clickjacking/CSP/CORS*/SRI) sao do PORTFOLIO GitHub Pages (ZAP seguiu 302 da /), nao do bot â€” sem acao; info de HSTS/cache idem. ZAP daemon gerido por launcher. Pendente: deploy v1.14.16 no Render + verificar 404/405 ao vivo; fluxo celular; limpeza pedidos teste; publish OAuth; 1a venda (Fase C vetada).
Dia 13 (13/09, sessao 3, ambiente): github MCP confirmado conectado (get_me=bapzxdev);
                tokens revogados confirmados pelo dono. 5 skills instaladas em
                ~/.config/opencode/skills/ (debugging, testing, code-review,
                git-github, documentation - formato SKILL.md). STACK DE SEGURANCA:
                OWASP ZAP 2.17.0 via winget (JRE Temurin 17), add-on MCP Integration
                v0.4.0, MCP server em localhost:8282 (chave 64 chars rotacionada em
                config.xml + env ZAP_API_KEY, secureOnly=false p/ HTTP local),
                MCP "zap" remoto no opencode.jsonc, skill security-testing (recon ->
                analise -> testes -> validacao -> relatorio), launchers ZAP-MCP.bat
                (GUI) e ZAP-MCP-daemon.bat. Testado: initialize 200 c/ chave, 401 sem.
                ZAP daemon parado ao fim da sessao (rodar launcher antes de usar).
                Dia 14 (14/09, v1.16.0, painel/cliente expandido): itens 1-4 da evoluÃ§Ã£o aprovada
                pelo dono implementados em sequÃªncia: (1) aba Clientes no admin
                (lista, detalhe c/ histÃ³rico, editar personagem/mundo/role,
                bloquear/desbloquear) + /cliente/perfil; (2) aba Pagamentos
                (pendentes/aprovados/entregues/cancelados/faturado); (3)
                Tickets/Suporte â€” tabela nova `tickets`, admin responde/
                encerra/exclui (com prioridade), cliente abre em /cliente/suporte;
                (4) ConfiguraÃ§Ãµes â€” preÃ§os globais editÃ¡veis (tabela `config`,
                chave precos) lidos pelo bot via calc_price (cache 2 min, fallback
                PRICES) + notificar_pedido. CSRF reutilizado nos formulÃ¡rios do
                cliente. SQL supabase_migracao_v116.sql criado (pende dono). 34
                rotas registradas, py_compile + GET admin/cliente 200, CSRF
                302/403. Ainda nesta sessÃ£o: /login 403 (Origem invÃ¡lida)
                corrigido (ALLOWED_HOSTS + bapzx-bot-tibia.onrender.com, d5b2a5b);
                causa do 500 de /api/itens era credencial SUPABASE_URL/KEY errada
                no Render (corrigida pelo dono, produÃ§Ã£o 200). Pendentes: aplicar
                migraÃ§Ã£o v1.16 no SQL Editor, validar deploy v1.16.0 + /login ao
                vivo, testes da nova Ã¡rea ao vivo, fluxo celular, limpeza pedidos
                de teste, publish Google OAuth, Fase C vetada.
                Dia 14 (2Âº, 14/09, v1.16.1 -> v1.16.2): v1.16.1 adicionou a rota
                /acesso (pÃ¡gina de escolha CLIENTE/ADMINISTRAÃ‡ÃƒO apÃ³s o login â€”
                admin vÃª 2 portas, cliente sÃ³ Cliente; callback do OAuth agora
                vai para /acesso; link "Trocar Ã¡rea" no admin e na Ã¡rea do
                cliente). v1.16.2 fez o RESTRUCTURE VISUAL completo da Ã¡rea
                ADMIN (pedido do dono): carcaÃ§a profissional em painel.py â€”
                sidebar fixa agrupada com Ã­cones/hover/ativo (PRINCIPAL:
                Dashboard; VENDAS: Pedidos/Itens/Pagamentos; CLIENTES:
                Clientes/Tickets; SISTEMA: ConfiguraÃ§Ãµes; ATALHOS: Ver site/
                Trocar Ã¡rea/Sair), topbar com tÃ­tulo+breadcrumb, busca real
                (filtra as tabelas da pÃ¡gina via JS), sino com badge real
                (pedidos pendentes + tickets abertos via _count) e menu do
                usuÃ¡rio; dashboard recriado: 4 KPIs (Faturamento/Pagamentos/
                Pedidos/Clientes) com dados reais de _metrics, grÃ¡fico de
                barras vertical "Pedidos nos Ãºltimos 14 dias" (perÃ­odo, valores,
                tooltip) e "PÃ¡ginas mais visitadas" com chips de visitas
                (7d/hoje/total). Responsivo: drawer no <1024px (hambÃºrguer +
                scrim) e scroll interno nas tabelas no mobile (corrigido
                overflow-x de 879px que estourava o layout). CAUSA RAIZ
                corrigida: o CSS do painel estava INATIVO porque LAYOUT_HEAD
                usava chaves duplicadas ({{/}}) preparadas para um .format() que
                nunca rodava â€” sÃ³ existia .replace("{title}"); novo CSS (chaves
                simples) finalmente aplica. Testes: py_compile OK, GET nas 7
                rotas admin 200 com shell, CSS sem chaves duplas e balanceado,
                Playwright validou desktop 2048/1440 e mobile 390 (drawer
                abre/fecha, dropdowns, busca filtra 12 linhas, sem overflow-x,
                charts/KPIs 1 coluna). Deploy verificado: /health â†’ v1.16.2.
Dia 15 (15/09, v2.0.1, acentos + mesma aba) â€” DEPLOYADO. Bug de encoding:
                `_page("Entrar", "Escolha a &aacute;rea", ...)` â€” o parÃ¢metro
                `brand` do `_page` Ã© escapado com `html.escape`, entÃ£o
                `&aacute;` virava `&amp;aacute;` literal na tela. Corrigido p/
                "Escolha a Ã¡rea". Script `fix_entities.py` substituiu TODAS as
                entidades HTML (`&aacute;`/`&ccedil;`/`&atilde;`/`&middot;`/
                `&copy;` etc.) por caracteres reais em bot.py/painel.py/
                legais.py. Removidos TODOS os `target="_blank"` do portfÃ³lio
                (7 pÃ¡ginas) e de bot.py (2)/painel.py (3): padrÃ£o agora Ã© abrir
                na MESMA aba. VERSION 2.0.1. Deploys: bot db0f135â†’Render,
                portfÃ³lio a027139â†’GitHub Pages (v2.0.1 confirmado no /health).
Dia 15 (15/09, v2.0.2, pentest ZAP) â€” DEPLOYADO. Pentest da nova atualizaÃ§Ã£o
                a pedido do dono: ZAP (spider+passive+active) + script manual
                `pentest_v202.py` (35/35 checagens OK: RBAC bypass, CSRF, XSS,
                info disclosure, rotas legais, APIs, error handlers). Achados
                de header corrigidos em `security_headers` (bot.py:~727):
                HSTS (`max-age=31536000`, sÃ³ sob HTTPS via x-forwarded-proto)
                e CSP (`default-src 'self'; ... frame-ancestors 'none';
                base-uri 'self'; form-action 'self'`). Confirmado em produÃ§Ã£o:
                6/6 headers em 7 rotas (/health, /privacidade, /termos,
                /reembolso, /api/grupos, /api/itens, /robots.txt). Alertas ZAP
                remanescentes (CORS `*`, anti-clickjacking, SRI,
                X-Content-Type-Options aparente) sÃ£o do PORTFÃ“LIO GitHub Pages
                (o ZAP segue o 302 da `/`); o scan direto de `/privacidade` em
                v2.0.2 NÃƒO gerou alerta. `Application Error Disclosure` era o
                500 transitÃ³rio do cold start em `/robots.txt` (hoje 404
                limpo). VERSION 2.0.2. Deploy bot 886eac8â†’Render.
Dia 15 (15/09, v2.1.0, serviÃ§os Ã— itens) â€” DEPLOYADO. A pedido do dono: a
                IntermediaÃ§Ã£o nÃ£o podia ficar misturada com a venda de itens
                do jogo. `supabase_migracao_v119.sql`: cria tabela `servicos`
                (espelha `itens`), move a IntermediaÃ§Ã£o BAPZX R$5 de `itens`
                para `servicos` (bucket + policy pÃºblicas de imagens). Novo
                endpoint pÃºblico `/api/servicos` no painel.py (espelho de
                `/api/itens`, =rate limit, CORS condicionado). PortfÃ³lio
                `itens.html` com 2 seÃ§Ãµes separadas: "Itens do jogo âš’ï¸"
                (`/api/itens`) e "ServiÃ§os ðŸ›¡ï¸" (`/api/servicos`, CTA
                "Quero contratar"). VERSION 2.1.0. Migrations v118 e v119
                APLICADAS pelo dono. Validado em produÃ§Ã£o: `/api/servicos` â†’
                IntermediaÃ§Ã£o; `/api/itens` â†’ vazio. Testes: py_compile OK,
                /api/servicos 200. Deploys: bot 97c9d3câ†’Render,
                portfÃ³lio v3.5 f171800â†’GitHub Pages.
Dia 16 (16/09, v2.1.2, Ã¡rea do cliente padronizada) â€” DEPLOYADO. A pedido do
                dono, a pÃ¡gina "Escolha a Ã¡rea" (/acesso) ficou igual ao inÃ­cio
                do site: tÃ­tulo da aba "BAPZX Â· Escolha a Ã¡rea" (AUTH_LAYOUT
                agora usa `<title>BAPZX Â· {title}</title>`), link "Voltar ao
                site" no topo (PORTFOLIO_URL) e marca BAPZX com fonte Sora 800
                + gradiente verdeâ†’azul (`.brand` com `BAP<span>ZX</span>`),
                replicando o portfÃ³lio por toda a Ã¡rea do cliente. VERSION
                2.1.2. Validado: tÃ­tulo, link e gradiente presentes. Deploy
                7887fc5 â†’ Render.
Dia 16 (16/09, portfÃ³lio v3.6, aba Grupos) â€” DEPLOYADO. A pedido do dono
                ("aba Grupos no topo da primeira pÃ¡gina, antes de Minha Ã¡rea"),
                criada pÃ¡gina dedicada `grupos.html` no portfÃ³lio (consome
                `/api/grupos`, botÃµes "Entrar no grupo", fallback "em breve")
                e adicionada a aba **Grupos** no menu de TODAS as 8 pÃ¡ginas
                (posiÃ§Ã£o: Itens â†’ Grupos â†’ FAQ â†’ Contato â†’ Minha Ã¡rea). O site
                jÃ¡ mostra os 3 grupos reais cadastrados pelo dono no
                /admin/grupos (RUBINOT AURORIA, RUBINOT BELARIA-VESPERIA,
                RUBINOT BELLUM, com links chat.whatsapp.com). index.html: seÃ§Ã£o
                "Nossos Grupos" mantida + versÃ£o v3.3â†’v3.6. Validado local
                (Playwright) e em produÃ§Ã£o: grupos.html 200. Commit 65abe5a â†’
                GitHub Pages.
Dia 16 (16/09, v2.2.0 + portfÃ³lio v3.7, grupos completos) â€” DEPLOYADO. TrÃªs
                pedidos do dono: (1) EXCLUIR grupo no /admin/grupos (rota POST
                `/admin/grupos/<gid>/excluir`, CSRF, botÃ£o vermelho com
                confirm); (2) ALINHAR TEXTO da pÃ¡gina de Grupos (cards com tag
                "ðŸ’¬ WhatsApp", nome centralizado, botÃ£o uniforme em grupos.html
                e na seÃ§Ã£o Nossos Grupos do index); (3) REORDENAR ao mudar a
                ordem â€” botÃµes â†‘/â†“ (POST `/admin/grupos/<gid>/mover`) trocam a
                posiÃ§Ã£o e reescrevem ordem=1..n (dashboard e /api/grupos jÃ¡
                ordenavam por ordem.asc). VERSION 2.2.0. Validado via test
                client: GET 200 com botÃµes, mover cima/baixo 302 (3 patches),
                excluir 302, CSRF 403, bordas nÃ£o erram. Deploys: bot 03908f9â†’
                Render (v2.2.0 no /health; API grupos ordem 1/2/3), portfÃ³lio
                a01ece1â†’GitHub Pages v3.7 (grupos.html 200).
Dia 16 (16/09, v2.4.0, ConfiguraÃ§Ãµes no dashboard â€” item 11) â€” DEPLOYADO. A
                pedido do dono ("11. ConfiguraÃ§Ãµes: Site (Logo, Nome, Banner,
                Textos, Links, Redes sociais); Conta (Nome, E-mail, Senha, 2FA);
                Pagamentos (Pix, Gateway, Dados financeiros); NotificaÃ§Ãµes (E-
                mail, WhatsApp, Alertas)"), a aba ConfiguraÃ§Ãµes de /admin/config
                foi reescrita com 4 abas via `?aba=site|conta|pagamentos|
                notificacoes` na tabela `config` jÃ¡ existente (v116, sem
                migration nova). painel.py (VERSION 2.4.0): helpers
                `_CONFIG_CAMPOS/_CONFIG_SECOES/_CONFIG_PUBLICAS/_config_field/
                _config_textarea/_config_bool/_config_tabs/_config_grupo_html`;
                salvar valida por seÃ§Ã£o (URL http(s), bool 1/0, limites) e grava
                SÃ“ campos presentes no form (nÃ£o apaga os outros); rotas novas
                POST /admin/config/salvar, POST /admin/config/conta (nome do
                usuÃ¡rio + session + auditoria) e GET /api/site pÃºblico (CORS +
                rate-limit, sÃ³ _CONFIG_PUBLICAS, nunca token/segredo); antigo
                secao=precos mantido. Conta: e-mail read-only e card explicando
                senha/2FA via login Google. Pagamentos: pix_chave (fallback env
                PIX_KEY) + beneficiÃ¡rio, Gateway MP read-only (status depende
                da env MP_ACCESS_TOKEN no Render). bot.py (VERSION 2.4.0):
                `_config_map()` com cache 120 s (falhaâ†’{}), payment_text usa
                pix_chave, notify_owner e notify_owner_pix com gates
                (notificar_pedido/notificar_pix), _error500 sÃ³ avisa dono se
                notificar_erro != "0". Validado: py_compile + test_config.py
                (4 abas 200, salvar site/notif/precos 302, URL invÃ¡lida 400,
                conta 302 PATCH com params email=eq., CSRF 403, /api/site 200
                sem chaves privadas, sem permissÃ£o 302/403) + test_bot_config.py
                (gates OFF/ON, override/fallback pix, _config_map falhaâ†’{}) â€”
                TODOS PASSARAM. Deploy bot `07a8467` â†’ Render: /health "bot ok
                v2.4.0", /api/site {"ok":true,"site":{...pÃºblicas vazias}},
                /admin/config sem login 302â†’/login. Pendente dono: preencher
                /admin/config (ajustar depois, ex.: banner), conferir /api/site
                e depois ligar no portfÃ³lio (itens 8/9/14); v120 do cupom segue
                pendente.
Dia 16 (16/09, v2.3.0, cupons no dashboard â€” item 10) â€” DEPLOYADO. A pedido
                do dono ("no dashboard vamos implementaÃ§Ã£o: 10. Cupons"),
                implementado o CRUD completo de cupons de desconto no painel.
                `supabase_migracao_v120.sql` (PENDENTE do dono no SQL Editor):
                tabela `cupons` â€” codigo unique, tipo percentual|fixo,
                valor numeric, validade date, limite_usos (0=ilimitado),
                usos (contador), produto_id/servico_id/grupo_id opcionais,
                ativo + Ã­ndices. `rbac.py`: permissÃµes `ver_cupons` e
                `gerenciar_cupons` (padrÃ£o ADMIN + MANAGER). `painel.py`:
                item "Cupons" na sidebar (Vendas, Ã­cone ticket), rotas GET
                /admin/cupons (lista + form), POST /novo, GET/POST /<id>
                (editar), POST /<id>/ativar (toggle), POST /<id>/excluir;
                validaÃ§Ã£o (codigo MAIÃšSCULAS obrigatÃ³rio, valor > 0, %
                limitada a 100, validade, limite â‰¥ 0) e "JÃ¡ existe um cupom
                com o cÃ³digo X" em conflito unique. VERSION 2.3.0. Validado:
                py_compile + test client (lista 200, novo 302, duplicado 400,
                editar 302, toggle 302, excluir 302, CSRF 403, valor 0 400).
                Deploy bot `e303372` â†’ Render (/health "bot ok v2.3.0").
                Pendente dono: aplicar v120 no Supabase e criar o cupom de
                exemplo BAPZVESPERIA (10% grupo Belaria-Vesperia).
Dia 16 (16/09, v2.5.0, Auditoria completa â€” item 14 do roadmap, ANTECIPADO)
                â€” DEPLOYADO. A pedido do dono ("saber quem fez o quÃª e quando"),
                auditoria de ponta a ponta: (1) evento do BOT â†’ `audit_log`
                (funÃ§Ã£o `audit_log` em bot.py, email `sistema@bapzx`/ip
                `sistema`, hook em `pedido_criado`, `pix_gerado` â€” sempre loga,
                `pedido_pago`/`pedido_entregue` via apply_status cobrindo /pago,
                /entregue e webhook MP, e `feedback_recebido`); (2) pÃ¡gina
                `/admin/audit` reescrita com busca `q`, dropdown de aÃ§Ã£o
                (`_ACOES_AUDIT` = labels + badges coloridos), filtro por
                e-mail `quem`, paginaÃ§Ã£o 50/pÃ¡g (`Range` + `Prefer:
                count=exact`) e **Exportar CSV** (2000 filtrados); `_fetch_soft`
                na listagem. VERSION 2.5.0. Validado: test_audit.py +
                test_audit_bot.py + regressÃ£o config â€” TODOS PASSARAM;
                py_compile OK. Deploy bot `97565a2` â†’ Render (/health "bot ok
                v2.5.0"; /admin/audit sem login 302â†’/login). Auditoria de admin
                (21 rotas POST) jÃ¡ existia desde v2.0.0. Pendente dono: validar
                a pÃ¡gina ao vivo (busca/filtros/CSV) e fazer pedidos para ver os
                eventos do bot no log.
Dia 15 (15/09, v2.1.1, resiliÃªncia APIs) â€” DEPLOYADO. O dono perguntou se os
                avisos "ERRO 500 em /api/itens (raise ConnectionError)" eram
                testes â€” NÃƒO eram: o Supabase teve uma queda momentÃ¢nea e
                `/api/itens` usava `_fetch` estrito (500). Criado
                `_fetch_public` em painel.py: endpoints pÃºblicos degradam para
                lista vazia em conexÃ£o/timeout/5xx do Supabase (sem 500, sem
                aviso no Telegram); 401/403/PGRST30x continuam subindo.
                Aplicado em /api/itens, /api/grupos, /api/servicos. VERSION
                2.1.1. Validado: /health "bot ok v2.1.1"; APIs 200 (itens 0,
                grupos 0, servicos 1). Deploy 2405e90 â†’ Render.
Dia 16 (16/09, v2.6.0, itens 13 Administradores + 9 NotificaÃ§Ãµes) â€”
                rbac.py com cargos novos (ADMINISTRADOR total, MODERADOR,
                ATENDENTE, FINANCEIRO) e normalizacao de cargos antigos;
                /admin/notificacoes + sino com feed por permissao e Alertas
                administrativos; hooks erro_pagamento no bot. Migration v120 de
                cupons APLICADA pelo dono. Prazo do bloco estendido +2 meses
                (meta 16/11/2026) a pedido do dono. Testes verdes.
                FASE A/B seguem encerradas; FASE C (divulgacao) segue VETADA
                pelo dono ate tudo ajustado.
Dia 16 (16/09, v2.7.0, Ã¡rea Service + Ã¡rea SeguranÃ§a) â€” a pedido do dono:
                (1) "Service" = diÃ¡rio pessoal de serviÃ§os manuais do dono â€”
                `/admin/services` com KPIs (ServiÃ§os/ConcluÃ­dos/Total Pix/
                Total Coins/Horas) no topo, CRUD completo (novo, editar,
                concluir/reabrir, excluir) e form novo serviÃ§o (data, hora,
                serviÃ§o, nome, WhatsApp, valor, forma pix|coins, horas,
                observaÃ§Ã£o); (2) "SeguranÃ§a" = `/admin/seguranca` com
                histÃ³rico de login (IP/dispositivo/Ãºltimo acesso), sessÃµes
                ativas, botÃ£o de ENCERRAR sessÃ£o e dica dos links Google de
                seguranÃ§a. bot.py: `_registrar_sessao` no OAuth (tabela nova
                `sessoes`), `_encerrar_sessao` no logout, audit login/logout.
                Guardas do painel validam sessÃ£o ativa (`_sessao_ativa` cache
                60s) e forÃ§am logout se encerrada. WhatsApp adicionado ao form
                de ediÃ§Ã£o de cliente. rbac: 4 permissÃµes novas
                (ver/gerenciar_servicos_manuais, ver_seguranca,
                gerenciar_seguranca). Migration `supabase_migracao_v121.sql`
                (PENDENTE do dono no SQL Editor): servicos_manuais + sessoes +
                profiles.whatsapp. VERSION 2.7.0 (bot.py e painel.py).
                Validado: py_compile OK; test_services_seguranca.py +
                test_bot_sessoes.py NOVOS + regressÃ£o completa (rbac,
                notificacoes, config, cupons, audit, audit_bot, v200,
                bot_config) â€” TODOS PASSARAM.
Dia 17 (17/09, v2.7.1, Service com valor cobrado automÃ¡tico) â€” dono testou
                Service e pediu: valor cobrado = valor/hora Ã— horas (1h â†’ R$ 20,
                1,5h â†’ R$ 30) com campo Desconto (R$) abaixo do valor. Ao
                investigar o "valor absurdo" nos totais, descoberto bug no
                `_parse_brl`: string decimal do Supabase ("150.00") virava
                15000 (ponto tratado como milhar); corrigido â€” nÃºmero sem
                vÃ­rgula vira float direto, e sÃ³ o formato BR "1.500,50" usa
                vÃ­rgula como decimal. painel.py/bot.py: forms novo/editar de
                serviÃ§o ganharam Valor por hora (R$) (padrÃ£o 20), Horas e
                Desconto (R$) com prÃ©-cÃ¡lculo ao vivo via JS (`sv_total`);
                POST calcula valor = max(0, valor_horaÃ—horas âˆ’ desconto) e
                persiste valor_hora/desconto. Migration `supabase_migracao_
                v122.sql` (PENDENTE do dono no SQL Editor): colunas
                valor_hora/desconto em servicos_manuais + backfill. v121
                APLICADA pelo dono (Service testado ao vivo). VERSION 2.7.1
                (bot.py e painel.py). Validado: py_compile OK; teste
                test_services_seguranca.py atualizado para o cÃ¡lculo +
                regressÃ£o (cupons, sessoes, notificacoes, rbac, audit_bot) â€”
                TODOS PASSARAM. Commit 5fc92f7 pushado (96e7cb2..5fc92f7).
                Deploy: re-deploy no Render pendente (dono).
Dia 19 (19/09, v2.7.4, Service form fix) â€” corrigido bug pedido no check-in: horas com
                vÃ­rgula ("2,5") viravam 0 ao salvar/editar (float() quebrava com
                ValueError e o except zerava). Helper `_sv_num` aceita "2,5"/
                "2.5"/"1.500,50" e Ã© usado nos 2 POSTs (valor_hora/horas/desconto).
                Removida a lÃ³gica `svRecalc` e suas chamadas dos 2 forms; `svCoinToggle`
                mantida como funÃ§Ã£o independente. VERSION painel.py 2.7.4. Pendente dono: deploy no Render.
Dia 22 (22/09, v2.7.12, autocomplete Service) â€” pedido do dono: no dashboard
                Service, os campos Nome do cliente e WhatsApp do cliente passam a
                auto-completar com os clientes jÃ¡ cadastrados (ex.: digitar "Dout"
                â†’ "Doutor Odeioretro"). `_sv_sugestoes()` junta servicos_manuais +
                profiles; `_sv_autocomplete_html()` monta 2 datalists + JS `svPair`
                que preenche o WhatsApp (ou o nome) do parceiro ao escolher um
                conhecido, se o campo estiver vazio. Aplicado nos forms novo e
                editar de serviÃ§o. VERSION painel.py 2.7.12 (bot.py 2.7.3 sem
                mudanÃ§a). Validado: py_compile OK + test client real (200 nos dois
                forms com datalists+SV_PAIRS) + sugestÃµes reais no Supabase.
                Pendente dono: re-deploy no Render e validar ao vivo o autocomplete.
Dia 22 (22/09, v2.8.0, mÃ³dulo COINS administrativo + preÃ§o dinÃ¢mico) â€” pedido
                do dono: controlar Tibia Coins no dashboard manualmente com
                histÃ³rico. `supabase_migracao_v123.sql` (PENDENTE do dono no SQL
                Editor): coins_config (linha Ãºnica id=1: estoque 100000, preco_mil
                90, min_compra 100, max_compra 50000, status ativo|pausado,
                atualizado_em/por) + coins_historico (admin, qtd_anterior/nova,
                preco_anterior/novo, alteracao, criado_em) + Ã­ndices. rbac:
                ver_coins/gerenciar_coins (sÃ³ ADMINISTRADOR/MASTER por padrÃ£o).
                painel.py: item COINS na sidebar (Vendas), GET /admin/coins (4
                cards + form ediÃ§Ã£o + calculadora JS + histÃ³rico â‰¤100), POST
                /admin/coins/salvar (validaÃ§Ãµes, diffâ†’histÃ³rico, upsert id=1,
                audit coins_salvar). bot.py: preÃ§o vira dinÃ¢mico (coins_config.
                preco_mil, fallback R$ 90) em calc_price/price_table_text/
                price_table_compact/ask_ai/persona (load_persona); _coins_check
                bloqueia venda pausada ou fora de [min,max] apÃ³s build_order;
                fail-soft sem a tabela; preÃ§o congelado na criaÃ§Ã£o do pedido.
                Mojibake do nome no profiles CORRIGIDO (PATCH 204 â†’ "Lucas
                \"bapstyl3x\" Cristianini Marca"). VERSION 2.8.0 (bot.py +
                painel.py). Validado: py_compile OK; test_coins.py NOVO (23
                testes â€” TODOS OK); regressÃ£o test_qtd_coins intacta.
                Pendente dono: aplicar v123; re-deploy no Render; validar ao vivo
                /admin/coins.
Dia 22 (22/09, organizaÃ§Ã£o Supabase) â€” a pedido do dono, TODOS os arquivos
                .sql do Supabase foram movidos para a pasta canÃ´nica
                `C:\DEV\Supabase` (fora do repo): supabase_migracao_v111..v123,
                criar_tabela_supabase.sql e migracao_status.sql foram removidos
                do git bapzx; sÃ³ ficou `scripts/migrar_pedidos.py` (script
                Python do projeto) e `scripts/criar_tabela_supabase.sql`/
                `migracao_status.sql` agora vivem sÃ³ em C:\DEV\Supabase. Criada
                `MEMORIA_MIGRATION.md` registrando a regra (novos .sql SEMPRE em
                C:\DEV\Supabase). Mensagem do /admin/coins e teste atualizados
                para citar o caminho. Commit 6af2e70 ja continha v123; novo
                commit do repo com a remoÃ§Ã£o dos .sql + gitignore.
Dia 22 (22/09, v2.9.0, redesign Ã¡rea do cliente) â€” a pedido do dono, a Ã¡rea
                do cliente (`/cliente`, `/cliente/perfil`, `/cliente/suporte`,
                `/cliente/suporte/<id>`) foi redesenhada como dashboard
                profissional SaaS dark (UI/UX); backend/rotas/auth/CSRF
                intactos. AUTH_LAYOUT reescrito (tokens @@TITLE@@/@@BRAND@@/
                @@TOP@@/@@BODY@@/@@WHATSAPP@@ via `.replace()` na nova
                `_render_layout()`), helpers `_title_initials`/`_cliente_header`/
                `_status_badge`/`_fmt_brl`/`_cliente_profile`/`_cliente_tickets`;
                `/cliente` com boas-vindas + 4 KPIs reais + pedidos recentes +
                Ãºltimo pedido + empty state (CTA â†’ portfÃ³lio) + ajuda + perfil.
                Bug corrigido no `_fmt_brl` ("22.50," â†’ "R$ 22,50"; milhar ok).
                VERSION bot.py 2.9.0 (painel.py segue 2.8.1). Validado:
                py_compile + test_coins.py 26 OK + test client + Playwright
                (dark theme, responsivo 4â†’2 cols, header colapsa <480px).
                Pendente dono: deploy no Render e validaÃ§Ã£o ao vivo do /cliente.
Dia 23 (23/09, v2.10.1, MARKTRADE â€” ajustes pedidos pelo dono): (1) **Mundo
                vira `<select>`** com os 16 mundos (`_MK_MUNDOS`: Auroria,
                Belaria, Bellum, Drakaria, Eldrian, Elysian, Infernum I/II/III,
                Lunarian, Malveria, Mystian, Obsidian, Solarian, Tenebrium,
                Vesperia); POST valida (`world not in _MK_MUNDOS` â†’ flash
                "Selecione um mundo vÃ¡lido" + redirect) e habilita o select por
                categoria (jogos Tibia 12 mundos, PokÃ©mon 3). (2) **"Tipo de
                PvP" removido** do form e do payload (`/api/troca` sem `pvp`;
                troca.html sem dot/CSS `.pvp`, SERVER_COLORS para 16 mundos);
                coluna da v124 fica no banco sem migration nova. (3) **Sprite
                automÃ¡tico do Wiki Tibia**: `_mk_itemsprite(item_name)` â€”
                mediawiki API (`prop=images` + `imageinfo iiurlwidth=96`),
                User-Agent BAPZX-MARKTRADE, timeout 8s, cache `_SPRITE_CACHE`
                cap 800, falha/inexistente â†’ ""; chamado no POST quando
                `sprite` vazio; hint no form "Deixe em branco para buscar a
                imagem automaticamente no Wiki Tibia". Validado ao vivo: "War
                Hammer" â†’ tibiawiki.com.br/images/2/25/War_Hammer.gif,
                "Guardian Axe" â†’ images/6/67/Guardian_Axe.gif, item
                inexistente â†’ "". **Migration v124 APLICADA pelo dono**
                (23/09). CorreÃ§Ã£o: linha 1 do bot.py corrompida (`ja
                subimport base64`) â†’ `import base64`. VERSION bot+painel
                **2.10.1**. Validado: py_compile OK; **test_marketplace.py 37
                OK** (novos: _MK_MUNDOS; _mk_itemsprite sucesso/cache/
                falha_e_vazio; publicar_mundo_invalido_rejeita 302;
                publicar_mundo_ok_nao_valida_mundo â€” payload sem tipo_pvp;
                publicar_sprite_vazio_busca_auto); regressÃ£o test_coins.py 26
                OK. Pendente dono: re-deploy no Render (v2.10.1), re-deploy do
                portfÃ³lio (troca.html) e validar ao vivo o fluxo completo
                (publicar c/ mundo do select â†’ sprite automÃ¡tico â†’ PIX â†’
                webhook ativa â†’ selo VIP â†’ /admin/marketplace â†’ vitrine).
Dia 23 (23/09, v2.10.4, MARKTRADE â€” publicar padronizado, categoria, contato obrigatÃ³rio e sprite fixo) â€” pedido do dono (5 itens): (1) **nome do item em title case** ao publicar (`_mk_title_case`: conectivos de/do/da/the/of/a/em em minÃºsculo; "WAR HAMMER"â†’"War Hammer"); (2) **select de Categoria** no publicar com padrÃ£o "AutomÃ¡tico (Wiki Tibia)" â†’ `_mk_itemcategory` consulta o Wiki Tibia (`prop=categories`, cllimit 500) e mapeia termos (soul core, make believe, rare, primal ordeal/wrath, fansite, soul war, rotten blood, house/guildhall/apartment/flat) â†’ nunca estoura, falhaâ†’""; (3) **Contato obrigatÃ³rio** (`required` + validaÃ§Ã£o no POST com flash+redirect; label "Contato * (discord/telegram/whypixels)"); (4) **sprite fixo**: `_mk_itemsprite` tenta novamente com `_mk_title_case(nome)` quando a 1Âª busca falha (anÃºncios "WAR AXE"/"war hammer" voltam a ter foto; validado ao vivo: "WAR HAMMER"â†’images/2/25/War_Hammer.gif); (5) POST reordenado (mundo validado antes de rede de categoria). painel.py `/api/troca` devolve `categoria`+`contato`; troca.html usa `a.categoria` no filtro icat (antes `a[k]` errado) e renderiza chip de categoria + contato (âœ‰). VERSION bot+painel **2.10.4** (bump real de cÃ³digo apÃ³s rÃ³tulo v2.10.4 anterior ser sÃ³ dados/UI). Validado: py_compile OK; test_marketplace **45 OK** (+5: title case, categoria wiki, contato obrigatÃ³rio, normaliza+cat manual, sprite auto c/ categoria); test_coins **26 OK**; JS check troca.html OK; navegador mock (2 anÃºncios com categoria/contato/sprite + filtro icat "soul core" â†’ 1). Commits pushados: bot `45620d1`, portfolio `1c70f88`. **PrÃ³ximo passo (dono): re-deploy no Render (v2.10.4) e testar ao vivo: publicar "WAR HAMMER" (nome "War Hammer" + foto + categoria) e sem contato (deve rejeitar).**

Dia 23 (23/09, v2.10.5, MARKTRADE â€” pÃ¡gina de detalhes do anÃºncio + info do item via Wiki) â€” pedido do dono: clicar num anÃºncio da listagem deve abrir uma **pÃ¡gina de detalhes dinÃ¢mica**, que busca as informaÃ§Ãµes (tier/atributos/requisitos/peso/preÃ§o de referÃªncia/histÃ³rico) sozinha do **Tibia Wiki**. Implementado: painel.py ganhou **GET `/api/troca/<id>`** (anÃºncio individual com `status`; 404 + CORS se nÃ£o achar) e **GET `/api/item?nome=`** (cache 2min; consulta a `{{Infobox_Item` do Wiki server-side via `action=parse&redirects=1`, limpa wikilinks, retry com UA neutro em 403/429; `referencia` = min/max/mÃ©dia/quantidade calculados dos anÃºncios ativos do MESMO item no prÃ³prio marketplace â€” sem preÃ§o inventado). portfolio: `anuncio.html` (nova pÃ¡gina, visual dark igual troca.html, "â† Voltar para os anÃºncios" padrÃ£o do site; mostra preÃ§o/ofertas/mundo/anunciante/contato/descriÃ§Ã£o/"Sobre o item" (ficha Wiki)/"PreÃ§o de referÃªncia"; loading/id invÃ¡lido/404 tratados; tÃ­tulo da aba dinÃ¢mico) + `troca.html` (cards viram `<a href="anuncio.html?id=...">` e **filtros persistidos em `sessionStorage`** para voltar com a lista preservada). VERSION painel.py **2.10.5** (bot.py segue 2.10.4). Validado: py_compile OK; test_marketplace **56 OK** (+10: api_troca detalhe encontrado/nÃ£o encontrado/rate-limit/CORS, api_item sem nome/com info, iteminfo parseia infobox/sem tier/falha+vazio, ref_de_preco mÃ©dia/vazio); test_coins **26 OK**; JS check troca.html + anuncio.html OK; navegador mock fim-a-fim (listagem â†’ filtro "Soul Core" â†’ clique â†’ detalhe c/ Tier 3/atributos/preÃ§o referÃªncia â†’ Voltar â†’ filtro restaurado; id invÃ¡lido e 404 tratados). Commits pushados: bot `6e3fc96`, portfolio `d3bd64d`. **PrÃ³ximo passo (dono): re-deploy no Render (v2.10.5 no /health) e validar ao vivo: clicar num anÃºncio real (foto/atributos/referÃªncia) e o "Voltar" com filtros preservados.**

Dia 23 (23/09, v2.10.0, MARKTRADE â€” marketplace de anÃºncios) â€” pedido do
                dono: os grupos de trade pediam um espaÃ§o de anÃºncios. bot.py
                (VERSION 2.10.0): Ã¡rea do cliente `/cliente/troca` (publicar
                anÃºncio: jogo, categoria, tÃ­tulo, descriÃ§Ã£o, preÃ§o GP por
                vidro flexÃ­vel, imagens) + `/cliente/troca/<aid>` (detail com
                selo VERIFICADO/SELLER# + botÃ£o PIX) + listagem com filtros;
                `_mk_gp` (formata GP; None/vazio â†’ "Aceita ofertas"). PIX
                Mercado Pago com `external_reference` prefixado `PUB-<listing>`
                / `DES-<listing>` (publicaÃ§Ã£o+destaque num PIX sÃ³) /
                `VIP-<email>` â€” selo VIP e ativaÃ§Ã£o de anÃºncio SÃ“ via
                webhook/query real no MP; `_marketplace_confirm` cobre
                PUB/DES/VIP e o branch fica antes do gate `isdigit()`.
                painel.py (VERSION 2.10.0): mÃ³dulo ADM `/admin/marketplace`
                (config preÃ§os/limites/duraÃ§Ãµes + lista de anÃºncios com
                ativar/bloquear/desbloquear/encerrar/verificar + teste VIP),
                sidebar MARKTRADE, auditoria marketplace_config/acao/vip.
                rbac.py: ver_marketplace/gerenciar_marketplace.
                Migration `supabase_migracao_v124.sql` (PENDENTE do dono no
                SQL Editor; arquivo em C:\DEV\Supabase): marketplace_config +
                marketplace_listings + marketplace_pagamentos +
                profiles.vip_until. Validado: py_compile OK; test_marketplace.py
                NOVO 30 OK; test_coins.py 26 OK. Pendente dono: aplicar v124,
                re-deploy no Render e validar ao vivo (publicar, PIX, webhook,
                selo VIP, /admin/marketplace).
Dia 23 (23/09, v2.10.5, MARKTRADE - ajuste do detalhe/card do anÃºncio) - pedido do dono (com referÃªncia impressa do card ideal): "a imagem ta muito grande", deixar "mais ou menos igual" ao card de referÃªncia e "nÃ£o usar os dados (sÃ£o fictÃ­cios)" (o print tinha Sanguine Legs T3 etc - era sÃ³ modelo de layout). Implementado: anuncio.html (detalhe): sprite 190px -> 88px (.d-sprite img) + chip de tier sobreposto (.d-tier-chip, via /api/troca/<id>.tier com fallback do Wiki); troca.html (card): chip de tier (.mk-tier-chip) sobre o sprite usando a.tier; painel.py: /api/troca (lista) e /api/troca/<aid> (detalhe) agora devolvem tier por anÃºncio via _iteminfo (cache 2min, nunca derruba). Tudo com os dados reais do marketplace (nada fictÃ­cio). Validado: py_compile painel.py OK; git diff conferido. Commits pushados: bapzx-portfolio 5ed7fe4, bapzx-bot-tibia 9bf8454 (inclui v2.10.5 + limite ilimitado p/ masters no publicar/dashboard). PrÃ³ximo passo (dono): re-deploy no Render (v2.10.5 no /health) e conferir o detalhe do anÃºncio (sprite pequeno + tier chip) e os cards da listagem com o chip de tier.

Dia 23 (23/09, v2.10.6, MARKTRADE - ficha do item (Wiki) voltou a aparecer) - bug do dono: "nÃ£o tÃ¡ aparecendo as informaÃ§Ãµes do item" no detalhe do anÃºncio (anuncio.html). Causa raiz: _iteminfo_wiki consultava o TibiaWiki com action=parse&prop=wikitext, que era bloqueado (403) no servidor Render - o sprite usa action=query e por isso os cards tinham imagem mas a ficha do item vinha vazia (testado ao vivo: /api/item retornava info {} mas referencia OK; action=parse dava 403 mesmo com UA neutro; action=query+revisions retorna o wikitext normal). CorreÃ§Ã£o: painel.py _iteminfo_wiki agora usa action=query&prop=revisions&rvprop=content&rvslots=main e lÃª query.pages[].revisions[].slots.main.content (mesmo mecanismo do sprite que funciona em produÃ§Ã£o). Tests: test_iteminfo_wiki_parsea_infobox e sem_tier_deixa_vazio mockados no formato novo (query.pages[].revisions[].content); test_marketplace 58 OK (56 anteriores + master limite + nÃ£o-master bloqueia, de mudanÃ§a pendente da v2.10.5); py_compile painel.py+bot.py OK. VERSION painel.py+bot.py **2.10.6**. Commit pushado: bapzx-bot-tibia d8a8758. **PrÃ³ximo passo (dono): re-deploy no Render (v2.10.6 no /health) e conferir a ficha do item ("Sobre o item") + tier no detalhe e nos cards ao vivo.**

Dia 24 (24/09, v2.10.8, MARKTRADE - autocomplete de itens no Publicar anÃºncio + ficha local no detalhe) - pedido do dono: o autocomplete de itens deve aparecer SÃ“ na pÃ¡gina Publicar anÃºncio (Ã¡rea do cliente /cliente/troca), nÃ£o na vitrine. Implementado no bot.py: novo mÃ³dulo mk_itens.py com _MK_ITENS_DB (54 itens: 14 Rods + 40 Wands; nome/nivel/vocacao/elemento/bonus/resistencia/atk/def/slots/peso/drop), _MK_ITENS_JSON injetado num JS inline (_MK_AC_SCRIPT) com dropdown filtrado (setas/Enter/Escape) + ficha do item (NÃ­vel/VocaÃ§Ã£o/Elemento/BÃ´nus/ResistÃªncia/Ataque/Defesa/Slots/Peso/Obtido de) e CSS _MK_AC_CSS (.mk-pub-ac/.mk-pub-ac-drop/.mk-pub-ficha). Campo item_name ganhou id + autocomplete=off. Corrigido bug do Ã­ndice filtrado vs array completo (data-i). troca.html do portfolio REVERTIDO ao estado anterior (sem autocomplete). FICHA LOCAL NO DETALHE DO ANÃšNCIO: painel.py ganhou _ficha_local() (busca em mk_itens por nome normalizado sem acentos) + ficha_local em /api/item e /api/troca/<id>; anuncio.html renderiza "Ficha do item - Dados da nossa base de itens" antes da ficha do Wiki. VERSION bot.py e painel.py 2.10.8. Validado: py_compile OK; test_marketplace 61 OK; test_coins 26 OK; navegador mock (detalhe id=99 com ficha local completa). SUBIDO: commits pushados bapzx (fd8e412: bot.py+painel.py+mk_itens.py novo; .gitignore ignora _mk_*.py) e bapzx-portfolio (fa61927); Render jÃ¡ re-deployado (v2.10.8 no /health); GitHub Pages atualizado. CRIADOS 8 anÃºncios de teste (4 VIP + 4 recentes, todos da base local): Sanguine Coil id 14 (95M, VIP), Falcon Wand id 15 (89M, VIP), Cobra Wand id 16 (70M, VIP), Lion Wand id 17 (Troca ofertas, VIP), Hailstorm Rod id 18 (4M), Moonlight Rod id 19 (3,5M), Rod of Destruction id 20 (60M), Wand of Destruction id 21 (50M); sprite real do TibiaWiki (bot._mk_itemsprite). VALIDADO AO VIVO: /api/troca/14 traz ficha_local (600/Sorcerers/114 atk); anuncio.html?id=14 renderiza a ficha local completa em produÃ§Ã£o; troca.html mostra 4 VIP no topo + 4 recentes na lista. PRÃ“XIMO (dono): validar ao vivo digitar 'sangui' no campo Item de /cliente/troca (publicar anÃºncio)


Dia 24 (24/09, v2.10.9, MARKTRADE - capacetes + schema unificado de itens no banco local) - pedido do dono: o banco local mk_itens.py alinhou para o schema que ele vai usar em tudo ('nome level voc tipo de dano bonus protecao dano medio slots tier peso dropa de'). Banco agora com 205 itens (54 armas Rods/Wands + 151 CAPACETES colados pelo dono). Schema novo por item: [nome, nivel, vocacao, tipo_dano, bonus, protecao, dano_medio, slots, tier, peso, drop] - def sai, tier entra, elemento->tipo_dano, resistencia->protecao, atk->dano_medio. Capacetes: tipo_dano='' e dano_medio guarda o Arm (botao rotulo dinamico 'Armadura'; armas 'Dano Medio'). Sem coluna de sprite (decisao do dono). Gerado por _mk_gera_capacetes.py (gitignored; le as 54 armas do HEAD do git + TSV temp do envio do dono; idempotente). Correcoes de transcricao: 'Nigem.'->'Ninguem.', Demon Helmet lvl 3->0. Codigo atualizado: painel._ficha_local (campos novos), bot.py _MK_AC_SCRIPT (labels Tipo de dano/Protecao/Dano Medio ou Armadura/Tier, sem Defesa), anuncio.html do portfolio (etiquetas dinamicas). VERSION bot+painel 2.10.9. Validado: py_compile OK; test_marketplace 62 OK (+1 test_ficha_local_capacete); test_coins 26 OK. Pendente dono: re-deploy no Render (v2.10.9 no /health) + GitHub Pages e validar ao vivo o autocomplete de capacete (digitar 'amazon' -> Amazon Helmet Armadura 7) e o schema novo no detalhe do anuncio.

Dia 24 (24/09, v2.10.10, MARKTRADE - armaduras no banco local do autocomplete) - pedido do dono: adicionar a lista de armaduras colada por ele ao banco local mk_itens.py (mesmo schema da v2.10.9). Banco agora com 370 itens (54 armas Rods/Wands + 151 capacetes + 165 ARMADURAS). Armaduras: tipo_dano='' e dano_medio guarda o Arm (Botao rotulo dinamico 'Armadura' ja existente desde v2.10.9 cobre; nenhuma mudanca de codigo/UI foi necessaria). Sem coluna de sprite (decisao mantida). Dados transcritos em _mk_armas_dados.py (gitignored); gerador _mk_gera_capacetes.py passou a ler as 54 armas do HEAD como itens com tier vazio (capacetes e armaduras tem tier preenchido - filtro idempotente) + 151 capacetes do TSV + 165 armaduras do modulo de dados. Caso especial: Spectral Dress com arm vazio (ficha mostra campo vazio). VERSION bot+painel 2.10.10 (bump). Validado: py_compile OK; test_marketplace 64 OK (+2: test_ficha_local_armadura Amazon Armor = Armadura 13, test_ficha_local_armadura_sem_arm); test_coins 26 OK (90 total). Commit pushado: bapzx ffcd0ea. Pendente dono: re-deploy no Render (v2.10.10 no /health) + GitHub Pages e validar ao vivo o autocomplete de armadura (digitar 'amazon armor' -> Amazon Armor Armadura 13) e ficha local no detalhe.

Dia 24 (24/09, v2.10.11, MARKTRADE - escudos + schema de 12 campos com categoria) - pedido do dono: adicionar a lista de escudos colada por ele ao banco local mk_itens.py; no meio do caminho o dono optou por seguir SÓ com os escudos por enquanto (pernas/spellbooks/botas/aljavas/fetiches ficam aguardando os dados). Banco agora com 455 itens (54 armas + 151 capacetes + 165 armaduras + 85 ESCUDOS). SCHEMA NOVO DE 12 CAMPOS: [nome, nivel, vocacao, tipo_dano, bonus, protecao, dano_medio, slots, tier, peso, drop, CATEGORIA] - cada categoria tem a coluna categoria ('Armas', 'Capacetes', 'Armaduras', 'Escudos'). Rotulo do dano_medio decidido por categoria: Armas->'Dano Médio', Escudos/Spellbooks->'Defesa', Aljavas->'Volume', demais->'Armadura'. Escudos: tipo_dano='', dano_medio=Def (rotulo 'Defesa'), tier=''. As 8 aljavas listadas na secao de escudos ficaram de fora (entram pela secao de aljavas com Volume). Codigo: painel._ficha_local campos +'categoria'; bot.py _MK_AC_SCRIPT rotuloDano(it) c/ fallback legado por tipo_dano; anuncio.html (portfolio) rotuloDano(ficha). Gerador _mk_gera_capacetes.py atualizado (categoria no dict, armas do HEAD c/ 11 ou 12 campos, filtro por categoria). VERSION bot+painel 2.10.11. Validado: py_compile OK; node --check no JS (bot + anuncio); test_marketplace 67 OK (+3: escudo Demon Shield 'Defesa' 46, escudo sem def, schema 12 campos sem duplicados); test_coins 26 OK (93 total); rotulos conferidos fim-a-fim via node (Demon Shield->Defesa 46, Amazon Armor->Armadura 13, Hailstorm Rod->Dano Médio 65, Adamant Shield->Defesa vazio). Commits pushados: bapzx 7365ce5, portfolio 07d741d. Pendente dono: re-deploy no Render (ainda v2.10.8, 3 versoes atras) + GitHub Pages e validar ao vivo o autocomplete de escudo (digitar 'demon shield' -> Demon Shield 'Defesa' 46); colar as demais secoes do envio para as proximas categorias.

Dia 24 (24/09, v2.10.12, MARKTRADE - banco local completo: pernas, spellbooks, botas, aljavas e fetiches) - pedido do dono: colou as 4 secoes restantes do envio (Pernas 66, Spellbooks 30, Botas 66, Aljavas 8, Fetiches/Extra Slot 76). Transcrito nos modulos gitignored (_mk_pernas_dados.py ja existia da sessao anterior; criados _mk_spellbooks_dados.py, _mk_botas_dados.py, _mk_aljavas_dados.py e _mk_fetiches_dados.py). Banco agora com 701 itens (54 armas + 151 capacetes + 165 armaduras + 85 escudos + 66 pernas + 30 spellbooks + 66 botas + 8 aljavas + 76 fetiches). Gerador _mk_gera_capacetes.py com as 5 categorias novas + merge de fetiches (_fk_bonus: Bônus vence; se "Nenhum."/"Nenhum"/"" usa Atributos; se ambos none, vazio = caso Cursed Coin). Layout por categoria: pernas/botas dano_medio=Arm (rotulo Armadura) + tier; spellbooks dano_medio=Def (rotulo Defesa) sem tier; aljavas dano_medio=Volume (rotulo Volume) sem slots/tier; fetiches nivel '0', vocacao 'Todas', sem dano_medio/slots/tier. Rotulo dinamico do bot.py e anuncio.html ja cobria tudo (sem mudanca de JS). Casos especiais mantidos: Boots of Waterwalking/Pair of Soft Boots/Worn Soft Boots arm vazio; Cursed Coin bonus vazio; Torch 'Pirate Gunner' duplicado no drop; Pumpkinhead peso '(apagada) 9.50 oz - (acesa) 12.50'; 'Speed + 15'/'Speed + 10' com espaco. VERSION bot+painel 2.10.12. Validado: py_compile OK; node --check no JS (bot + anuncio); rotulos fim-a-fim via node (6 casos OK); test_marketplace 74 OK (+7: total 701, perna, botas, botas sem arm, spellbook, aljava, fetiche bonus Atributos, fetiche sem bonus); test_coins 26 OK (100 total). AO VIVO: sem deploy. Pendente dono: re-deploy no Render (agora 4 versoes atras: v2.10.9..v2.10.12) + GitHub Pages; validar ao vivo novas categorias (ex.: 'spellbook' -> Defesa 23, 'quiver' -> Volume 6, 'fabulous' -> Fabulous Legs Armadura 9); conferir 8 anuncios de teste (ids 14-21); aplicar migracao v123 (COINS) se pendente.

Dia 24 (24/09, v2.10.13, MARKTRADE - pagina "Publicar anuncio" reformulada) - pedido do dono: reformular a pagina de publicacao. Implementado no bot.py: (1) removida busca automatica de sprite no Tibia Wiki no POST (campo sprite virou "URL da imagem (opcional)" manual; helper _mk_itemsprite mantido para scripts _mk_*); (2) campo descricao removido do form e do payload; (3) contato agora e WhatsApp com DDD obrigatorio: mascara (99) 9XXXX-XXXX via JS (mk_contato) + validacao backend novo helper _mk_whatsapp() (10/11 digitos, normaliza "(19) 98765-4321"; invalido rejeita com flash); label antigo discord/telegram/whypixels removido; (4) "Aceito ofertas" virou cards segmentados "Preco fixo / Aceito ofertas" (mk-seg, campo hidden modo_preco; preco fixo exige preco); (5) "Destacar meu anuncio" virou card estilizado (mk-destaque-box) com preco; (6) portfolio anuncio.html: bloco "Quer negociar este item?" agora e link real wa.me/55<digitos> (target _blank) quando ha numero (mini-contact continua chip dentro de <a>, sem link aninhado). VERSION bot+painel 2.10.13. Validado: py_compile OK; test_marketplace 75 OK (74 antigos -1 sprite auto +2 novos contato invalido/normaliza; posts de publish atualizados p/ "(19) 98765-4321"); test_coins 26 OK; GET da pagina conferido (mk-seg, mk_contato, sem textarea de descricao, sem nota de busca automatica). Pendente dono: re-deploy no Render (v2.10.8 -> 2.10.13) + GitHub Pages e validar ao vivo mascara de WhatsApp, cards preco/destaque e link wa.me no anuncio; conferir 8 anuncios de teste (ids 14-21).

Dia 25 (25/09, v2.10.14, MARKTRADE - distancia + punhos no banco local, publicar sem ficha e vitrine sem teste) - 3 pedidos do dono concluidos: (1) armas de distancia (18 Arremesso + 28 Bestas + 36 Arcos) e punhos (36) transcritos das tabelas coladas -> mk_itens.py agora com 1169 itens (522 armas); categorias novas "Armas de Arremesso"/"Bestas"/"Arcos" com rotulo "Ataque" e extras maos/alcance/hit (ficha local + autocomplete), punhos na categoria "Armas" c/ extras maos/def/mod_def; linha() sempre grava os 3 extras; zero divergencias nas 4 secoes. (2) removido o card de detalhes (mk-pub-ficha) do form Publicar anuncio (autocomplete de nomes mantido; aplicar so preenche item_name). (3) removidos os 8 anuncios de teste do Supabase (ids 14-21) e criados 8 novos (ids 22-29) com itens da base via _mk_renova_8.py (NÃO versionar); removidos os 4 cards hardcoded da vitrine (VIP_TESTE em troca.html do portfolio) - vitrine agora so mostra a API (8 anuncios, 3 destacados: id 23/26/27). VERSION bot+painel 2.10.14. Validado: py_compile OK; test_marketplace + test_coins 101 OK; _mk_renova_8.py removeu 14-21 (204) e criou 22-29; JS troca.html OK; pagina ao vivo confirmada sem VIP_TESTE (cache CDN atualizado). Commits pushados: bapzx 04c27e8, portfolio 9798b56. Pendente dono: re-deploy no Render (ainda v2.10.8, agora 6 versoes atras) + GitHub Pages e validar ao vivo autocomplete sem ficha, ficha local dos 8 anuncios novos e vitrine sem os hardcodes.

Dia 25 (25/09, v2.10.20, MARKTRADE - sprinte/cascata + 3 bugs do publicar + vitrine Sanguine) - (1) MK_SPRITE_HOST aceita lista (cloudinary,supabase); _mk_sprite_host com fallback; bucket publico mk-sprites; _mk_sprite_cdn neutralizado; 6 testes cascata. (2) v2.10.20 corrige 3 bugs do Publicar anuncio: hidden mk_modo_preco (modo.value = v), input preco so-numeros 9 digitos, e WhatsApp removido do card (troca.html) - fica so no detalhe (anuncio.html). (3) Vitrine BAPZX populada: doacoes ids 32-34 deletadas, criados 35 (War Hammer destaque verificado) + 36-45 (os 10 Sanguine, 1 de cada, com sprite Supabase + contatos 90000-0006..). 85 OK marketplace + 26 coins. Commits: bapzx b38f0e0 (v2.10.20), portfolio caa9253 (card sem contato). Render online v2.10.20 (dono fez deploy). Screenshot vitrine-sanguine.png.
Dia 25 (25/09, MARKTRADE - identidade visual no site inteiro + fix ficha Sanguine Crossbow) - (1) styles.css reescrito com os tokens/identidade do MARKTRADE (bg #0b0f1a, --border-2 #2c3d5e, --purple/--amber, radial-gradients roxo/verde, cards com borda+borda+sombra, hover elevacao, focus roxo) valendo para todo o portfolio (index, rubini, itens, service, faq, contato, grupos, como-comprar); troca.html/anuncio.html mantidos (root proprio prevalece). Rodape v3.8 em index/grupos. Commits portfolio 871d0a5 (styles.css), ef9ba10 (v3.8). (2) Fix ficha de Bestas/Arcos/Arremesso: o Sanguine Crossbow (id 41) mostrava "Armadura +10" e omitia Range/Hit% - rotuloDano agora retorna "Ataque" para Bestas/Arcos/Arremesso e a ficha ganhou linhas Range (alcance) e Hit% (hit). Commit portfolio e8407a9; 85 OK. (3) SE O: criada MEMORIA_1.md (raiz) com as 9 acoes SEO do dono (Search Console, Google Meu Negocio, llms.txt, robots.txt, velocidade, auditoria tecnica/titulos, Analytics, sitemap.xml, keyword) priorizadas + diagnostico do site (titulos ok, 6 paginas sem description, sem robots/sitemap/canonical/OG/schema); AGENTS.md agora manda le-la por primeiro. Google Meu Negocio = ADIADO (sem endereco fisico).

Dia 26 (26/09, MARKTRADE - SEO: apos item 1 verificado, fechados os itens 5/7/3 - restam so 8 bloq. dono) - (1) item 5 velocidade: lazy-load + width/height nos sprites de troca.html/anuncio.html/itens.html (commit ac9ca57) - preconnect + display=swap ja existiam; PageSpeed API sem chave (quota 429), CLS e lazy validados ao vivo via Playwright (22 imgs lazy, 0 overflow, 11 cards). (2) item 7 analytics: descoberto bug silencioso - track.js usava navigator.sendBeacon que envia credentials:include e era BLOQUEADO por CORS (ultima visita registrada 24/09); trocado por fetch keepalive com credentials:omit (commit d0c98c1); visitas 30-33 registradas em 26/09 (troca.html 200 no console limpo). (3) item 3 llms.txt: criado na raiz do portfolio (visao do site + 10 paginas + anuncios ativos + diretrizes p/ agentes de IA + WhatsApp real 5519991813598) e referenciado no robots.txt (commit 11c8b2f). (4) versao exibida v3.8 -> v3.9 (commit 7044aa8). SEO agora: 8/9 itens FEITOS e no ar (1-verificado, 3,4,5,6,7,8,9); so falta dono enviar sitemap.xml + indexacao no painel do Search Console. Memoria: MEMORIA_1.md atualizada, commit c3f8221.

Dia 26 (26/09, SEGURANCA - auditoria AppSec estatica de sexta, documental, sem alteracao de codigo) - revisado bot.py/painel.py/rbac.py/storage.py/legais.py/mk_itens.py + track.js e paginas do portfolio; pip-audit na venv: sem CVE. Relatorio completo salvo em BAPZX_SECURITY_AUDIT_2026-09-26.md (formato das 4 entregas do dono: checklist 15 corretos, imprecisos reformulados, +10 categorias, checklist final por area). Resultado: Criticos 0 / Altos 0 / Medios 2 / Baixos 5 / Info 5 / PASS 14 de 15. Destaques: M1 CSP script-src 'unsafe-inline' (JS inline do admin, sem XSS conhecido - pode aguardar); M2 SSRF latente no _mk_sprite_host (GET em URL arbitraria do usuario quando MK_SPRITE_HOST lista supabase/cloudinary; env nao setada -> inerte hoje; fix sugerido: allowlist de host + MIME image/* + limite de tamanho); B1 requirements.txt sem pin de versoes; B2 webhook MP sem validacao de assinatura (mitigado por reconsulta no MP + rate limit 60/min, impacto baixo); B3 rate limit em memoria do processo (pode ser contornado a cada restart/replica); B4 /api/track aceita body ~11MB (rate limit 20/min mitiga); B5 /health e x-render-origin-server divulgam versoes (fingerprint leve). Info: I1 /api/grupos reflete Origin sem _cors_ok (dado publico); I2 /api/item?debug=1 expoe diagnostico do Wiki; I3 DASHBOARD_KEY comparada com == (timing); I4 fallback storage em pedidos.json (resiliencia, sem resync); I5 confirmar presenca de 'state' no OAuth. VERSION sem bump (nenhuma mudanca de codigo). Proximo passo proposto: aplicar fixes M2 + B1/B2/B4 na ordem aprovada pelo dono.

Dia 26 (26/09, v2.10.21, MARKTRADE - filtros da vitrine CONSERTADOS, pendencia desde v2.10.4-dados) - dono pediu "arrume os filtros": causa raiz era o payload da /api/troca SEM o campo `voc` (qualquer chip de Vocacao zerava a vitrine). Fix: helper novo `_mk_vocs(item_name)` no painel.py normalizando para ["knight",...] (fonte 1 ficha local mk_itens "Knights"/"Sorcerers", fonte 2 fallback Wiki `vocrequired`; sem fonte -> []), campo `voc` no payload da /api/troca, e applyFilters do troca.html casando por inclusao na lista. De quebra: botao "Limpar filtros" do estado vazio nao funcionava (listener preso em <template> destacado; agora anexa no botao inserido) e `hideOffers` saiu do restoreState (sem switch na UI; estado legado travava ofertas ocultas). VERSION painel.py 2.10.21 (bot.py segue 2.10.20). Validado: py_compile OK; test_marketplace 89 OK (4 novos) + test_coins OK; node --check JS inline OK; simulacao node OK (voc=sorcerer -> Sanguine Coil; voc=knight -> War Hammer). Pendente dono: re-deploy no Render (painel 2.10.21) + GitHub Pages (troca.html) e validar ao vivo os chips de Vocacao.

Dia 26 (26/09, v2.10.22, MARKTRADE - categoria do anuncio DELETADA, sem uso, a pedido do dono) - removida a `category` do anuncio (Soul Core/Rares/... + auto-detect Wiki): deletados `_MK_ITEM_CATEGORIAS`, `_MK_CAT_WIKI`, `_mk_itemcategory()` e a leitura/validacao/gravacao no POST publicar (bot.py; publicar fica 1 chamada Wiki mais leve); campo `categoria` fora dos payloads /api/troca e /api/troca/<id> (painel.py); chip de categoria fora do card (troca.html) e do detalhe (anuncio.html) + CSS orfao; JSON-LD do detalhe com "category": "Item de Tibia" fixo. MANTIDO (tem uso): categoria da ficha local (rotulos Dano Medio/Ataque/Defesa/Volume) e categoria do catalogo itens/servicos. Coluna `category` segue no banco (sem migration). VERSION bot+painel 2.10.22. Validado: py_compile OK; test_marketplace 87 OK (2 testes do _mk_itemcategory deletados; normaliza_item_sem_categoria recriado; assertNotIn category no payload) + test_coins 26 OK; node --check troca.html + anuncio.html OK. Pendente dono: re-deploy no Render (v2.10.22) + GitHub Pages e validar ao vivo (publicar sem categoria, cards/detalhe sem chip).

Dia 27 (03/10, v2.10.27, ITENS - /admin/itens sem categoria e sem upload, a pedido do dono) - form novo e editar: Categoria e upload de imagem removidos; Nome com autocomplete do banco local mk_itens.py (reuso de _MK_AC_CSS/_MK_AC_SCRIPT/_MK_SPRITE_JS do bot.py via import tardio, vars CSS .itens-ac); sprite via navegador (preview + hidden) com fallback servidor _mk_itemsprite+_mk_sprite_host (fail-soft); editar mantem imagem se nome igual; card sem categoria; /api/itens sem categoria (portfolio tolera). Coluna categoria segue no banco default geral, SEM migration. VERSION painel.py 2.10.27 (bot 2.10.26). Validado: test_itens_admin.py NOVO 13 OK + regressao 105 marketplace + 26 coins; py_compile OK. Pendente: commit+push e re-deploy Render.

Dia 27 (03/10, v2.10.28, PERFIL - /cliente/perfil expandido, pedido do dono com mock) - 3 secoes (pessoais: apelido + email read-only c/ chip Google + WhatsApp + avatar upload bucket avatares c/ preview; jogo: personagem* + mundo select 16 _MK_MUNDOS + vocacao + Discord; prefs: 2 toggles + tema + idioma) + toast ok/erro + botao Salvando + dirty badge. POST valida e upsert c/ fallback legado sem migration. Migration v126 PENDENTE (8 colunas profiles + bucket avatares). /cliente ganhou cards Apelido/Vocacao. VERSION bot 2.10.28. Validado: test_perfil.py NOVO 13 OK + regressao 105 + 26 + 13 OK. Pendente: commit+push, aplicar v126, re-deploy Render.

Dia 27 (03/10, v2.10.29, ITENS PRO - preco sem letras + descricao auto + visual MARKTRADE, pedido do dono c/ print) - (1) preco: JS so numeros/R$ + servidor 400 se letra; (2) descricao readonly do banco local via /admin/item-desc + recompute no POST (_itens_desc_auto: categoria/Nv/vocacao/stat rotulado/bonus/peso); (3) form mk-form (labels bold, b dourado, glow, mk-publish-btn). VERSION painel 2.10.29. Validado: test_itens_admin 17 OK + regressao 105 + 26 + 13 OK. Pendente: commit+push e re-deploy Render.

Dia 27 (03/10, v2.10.30, DASH CLIENTE - area do cliente padrao admin, pedido do dono) - sidebar+topbar (grupos Principal/Negociacao/Ajuda, drawer mobile, user-menu c/ VIP) em /cliente, /perfil, /suporte e detalhe; _cliente_dash_page por replace do AUTH_LAYOUT (CSS reusado, fallback seguro); _cliente_header mantido so p/ troca (MK intacto); backend intacto. VERSION bot 2.10.30. Validado: test_cliente_dash.py NOVO 5 OK + regressao 105+26+17+13 OK. Pendente: commit+push e re-deploy Render.

Dia 27 (03/10, v2.10.31, CLIENTE 10 ITENS - lista do dono) - mantidos Dashboard/Pedidos/Suporte/Perfil; novos Pagamentos, Automacoes (toggles no profiles), Meu Bot (gated VIP c/ upsell), Meus Servicos (match WhatsApp + catalogo), Meu Plano (Basico vs VIP Pro + historico), Notificacoes (feed). Sidebar 10 itens/5 grupos. Sem migration. VERSION bot 2.10.31. Validado: test_cliente_dash 13 OK + regressao 105+26+17+13 OK. Push autorizado.

Dia 27 (03/10, v2.10.32, DASH ENXUTO - 7 blocos + pagina Pedidos, referencia do dono) - /cliente: saudacao/conta, resumo 4 cards, atividade 3+2, acesso rapido, plano c/ barras reais, avisos top4, status c/ check STORE/MP; tabela full em /cliente/pedidos; feed em helper reusado. Sem migration. VERSION bot 2.10.32. Validado: test_cliente_dash 14 OK + regressao 105+26+17+13 OK. Pendente: commit+push e re-deploy Render.
