# Prospecção B2B pelo Maps (Claude Skill)

Skill para o Claude que faz a prospecção ativa de um SDR: busca empresas de um nicho numa
cidade no Google Maps, abre o site de cada uma para ver se a empresa existe e atua no nicho, acha
o CNPJ, confirma cruzando o endereço com a Receita Federal, confere se a empresa já está no seu
CRM e cadastra os leads aprovados. Tudo com a sua aprovação antes de gravar.

Funciona com o **Agendor** (integração direta pela API) e com **qualquer outro CRM** (gera um CSV
pronto para importar no HubSpot, Pipedrive, RD Station, Piperun, Moskit ou numa planilha).

## O que você precisa

- [Claude Code](https://claude.com/claude-code) (terminal, app desktop ou extensão de IDE)
- Extensão **Claude in Chrome** conectada (a skill usa o navegador para ler o Maps e os sites)
- Python 3.9 ou mais novo, com a biblioteca `requests`
- Opcional: conta no Agendor com acesso à API

## Instalação

1. Baixe a skill (botão **Code → Download ZIP** no GitHub, ou `git clone https://github.com/allisonvillalba-alt/prospeccao-b2b-maps.git`)
   e coloque a pasta `prospeccao-b2b-maps` dentro da pasta de skills do Claude:
   - Windows: `C:\Users\<seu-usuario>\.claude\skills\`
   - macOS / Linux: `~/.claude/skills/`
2. Instale a dependência:
   ```
   pip install -r ~/.claude/skills/prospeccao-b2b-maps/requirements.txt
   ```
3. Abra uma sessão nova do Claude Code. A skill aparece na lista e é ativada sozinha sempre que o
   assunto for prospecção ou vendas: buscar leads, pesquisar uma empresa antes de abordar, descobrir
   CNPJ e sócios, conferir se a empresa já está no CRM ou subir negócios no funil.

## Primeiro uso

Na primeira vez, o Claude faz algumas perguntas antes de prospectar. Nada vem pronto: cada um
responde do seu jeito.

- O que você vende e para quem
- Nichos, portes aceitos, se empresa do Simples, MEI ou empresário individual entram, e quem nunca deve entrar
- Se o site é obrigatório e se o endereço do CNPJ precisa bater com o do Maps
- Qual CRM você usa
- **Em qual funil e em qual etapa do Agendor os leads prospectados vão entrar.** O Claude lista os funis da sua conta pelo nome para você escolher, e confirma o destino de novo a cada lote antes de gravar.
- Padrão do título do negócio, valor, estilo da descrição e se os sócios viram contatos
- **Quantos negócios novos por dia, no máximo**

As respostas ficam em `~/.prospeccao/config.json`. Para mudar depois, é só pedir ao Claude
("muda meu limite diário para 15").

### Se você usa o Agendor

Gere o token em **Menu → Integrações → API** e salve num arquivo, fora da pasta da skill:

- Windows (PowerShell):
  ```
  New-Item -ItemType Directory -Force "$env:USERPROFILE\.secrets" | Out-Null
  Set-Content -NoNewline "$env:USERPROFILE\.secrets\agendor.txt" "SEU_TOKEN"
  ```
- macOS / Linux:
  ```
  mkdir -p ~/.secrets && printf '%s' 'SEU_TOKEN' > ~/.secrets/agendor.txt
  ```

Prefira não colar o token no chat.

Se o menu de Integrações não mostrar a opção de token, é provável que o seu plano do Agendor não
inclua a API. Nesse caso, escolha a opção de CSV no primeiro uso e importe pela tela do Agendor.

## Como usar

```
Pega 10 empresas de engenharia elétrica em Campinas e me mostra por que funcionariam.
```

O Claude devolve uma tabela com empresa, CNPJ, porte, regime, sócios e o motivo de cada uma ser
um bom lead, mais a lista das reprovadas e das que já estão no seu CRM. Depois:

```
Pode subir as aprovadas.
```

Outros exemplos:

```
Prospecta clínicas odontológicas em Curitiba, até 15. Só fora do Simples.
```

```
Tenho estes sites: [lista]. Confere se estão no ar, acha o CNPJ e me diz quais já estão no meu CRM.
```

## Como a skill qualifica

1. **Site:** sem site, com site fora do ar ou com atividade fora do nicho, a empresa sai.
2. **CNPJ:** vem do rodapé do site, do whois do registro.br ou da web, e só é aceito se o endereço da Receita bater com o do Maps.
3. **Perfil:** porte, regime e exclusões que você definiu no primeiro uso.
4. **Duplicados:** empresa que já está no CRM com outro vendedor não é prospectada.

Os critérios completos estão em `references/qualificacao.md`.

## Segurança

- Nada é gravado sem o seu ok. O cadastro sempre roda primeiro em simulação.
- Os scripts só **criam** registros. Não existe código para editar ou apagar o que já está no CRM.
- A skill nunca mexe em funil, etapa, campo personalizado, automação ou usuário.
- O limite diário é seu. O que passar dele fica para o dia seguinte.
- O token fica em `~/.secrets/`, nunca dentro da skill.

## Estrutura

```
prospeccao-b2b-maps/
├── SKILL.md               instruções que o Claude segue
├── README.md              este arquivo
├── config.example.json    modelo da configuração criada no primeiro uso
├── requirements.txt
├── scripts/
│   ├── cnpj_tools.py      whois do registro.br e dados da Receita (CNPJá / BrasilAPI)
│   ├── agendor.py         leitura, deduplicação e criação no Agendor
│   ├── exportar_csv.py    CSV de importação para outros CRMs
│   ├── config.py          leitura e validação da configuração
│   └── util.py
└── references/
    ├── qualificacao.md    critérios de qualificação
    ├── formato-lote.md    formato do lote e o que vai em cada campo
    └── agendor-api.md     comportamentos da API do Agendor descobertos na prática
```

## Fontes de dados

- Google Maps (lido pelo navegador)
- [RDAP do registro.br](https://rdap.registro.br) para o titular de domínios `.br`
- [CNPJá](https://cnpja.com) (API aberta, 5 consultas por minuto) e [BrasilAPI](https://brasilapi.com.br) para os dados da Receita Federal

Os dados vêm de cadastros públicos. Se usar os contatos para abordagem, respeite a LGPD: prefira
contatos funcionais da empresa e atenda os pedidos de descadastro.

## Licença

MIT. Pode usar, adaptar e redistribuir. Veja `LICENSE`.
