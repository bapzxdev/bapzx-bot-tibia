# AGENTS.md — BAPZX
## Regras Gerais da Área de Trabalho
### Versão 1.0

---

# 1. REGRAS GERAIS DA ÁREA DE TRABALHO

Antes de alterar o código de qualquer projeto:

- Verifique se o projeto possui documentação, memória, decisões técnicas ou
  instruções próprias.
- Leia os arquivos relevantes antes de modificar o código.
- Identifique corretamente qual projeto e qual pasta estão relacionados à tarefa.
- Verifique o estado atual do Git antes de realizar alterações.
- Faça somente as alterações necessárias para cumprir a tarefa solicitada.

Após uma alteração importante:

- Atualize a documentação daquele projeto, quando ela existir.
- Registre decisões importantes.
- Registre testes realizados.
- Registre pendências ou limitações encontradas.

Sempre que houver uma alteração funcional no código:

- Incremente a versão exibida do programa correspondente.
- Respeite o padrão de versionamento já utilizado pelo projeto.
- Não invente um novo sistema de versionamento.

Nunca coloque:

- Senhas.
- Tokens.
- Chaves de API.
- Cookies.
- Credenciais.
- Chaves privadas.
- Outros segredos.

no código, documentação, logs, commits ou backups.

---

# 2. LEITURA OBRIGATÓRIA EM TODA SESSÃO — SEO PRIMEIRO

LEIA SEMPRE POR PRIMEIRO o arquivo:

`MEMORIA_1.md`

Localização:

```text
raiz da área de trabalho
```

---

# 3. PERMISSÃO DE EXECUÇÃO (MEMÓRIA ATIVA)

Leia `MEMORIA_MUSE_SPARK_1_3.md` (em `docs/memoria/`): o dono concedeu PERMISSÃO PERMANENTE
(ALWAYS ALLOW) para editar/criar/excluir arquivos do projeto, rodar comandos,
instalar dependências, rodar testes e corrigir erros — sem pedir confirmação
repetida por arquivo ou comando. Vale somente para tarefas do projeto, dentro
desta área de trabalho.

---

# 4. PROTOCOLO DE CONTINUIDADE (OBRIGATÓRIO EM TODA SESSÃO)

No início de cada sessão (CHECK-IN), leia `PROTOCOLO.md`, `ROADMAP-15DIAS.md`,
`CONTEXTO-SESSAO.md` e `LEMBRETE.md` (este último é o lembrete ativo da sessão
anterior; não repetir tarefas já marcadas como feitas) e o bloco
"PROTOCOLO DE REENTRADA" das memórias dos projetos,
e responda em até 5 linhas onde paramos. No fim de toda sessão (CHECK-OUT),
atualize o bloco de reentrada daquele projeto, registre o dia no log do
`ROADMAP-15DIAS.md`, faça commit + push das alterações e encerre com
"FIM DE SESSÃO". Detalhes no `PROTOCOLO.md`.
