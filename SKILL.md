---
name: prospeccao-b2b-maps
description: Prospecção B2B ativa para empresas brasileiras a partir do Google Maps e de dados abertos de CNPJ. Encontra empresas de um nicho numa cidade, qualifica pelo site, confirma o CNPJ cruzando o endereço com a Receita Federal, confere duplicados no CRM e cadastra os leads aprovados (Agendor pela API, ou CSV para qualquer outro CRM). Esta skill deve ser usada quando o usuário pedir para prospectar, pesquisar ou levantar empresas de um nicho numa cidade, qualificar ou enriquecer uma lista de leads com CNPJ, ou subir leads no CRM ("pega 10 empresas de engenharia em Campinas", "qualifica esses sites", "sobe no CRM").
---

# Prospecção B2B pelo Maps

Faz o trabalho de um SDR na prospecção ativa: busca empresas de um nicho no Google Maps, abre
cada site para ver se a empresa existe e atua no nicho, acha o CNPJ, cruza o endereço com a
Receita Federal, confere se a empresa já está no CRM e só então cadastra, com aprovação do
usuário.

A skill não traz nada fixo de nenhuma empresa. Nicho, perfil de cliente, título do negócio,
valor, funil e limite diário são perguntados a quem for usar, no primeiro uso, e ficam salvos
em `~/.prospeccao/config.json`, fora da pasta da skill.

## When to Use This Skill

- Montar a lista diária de prospecção de um nicho numa cidade
- Qualificar uma lista de sites ou empresas (site no ar, atividade coerente, CNPJ confirmado)
- Descobrir o CNPJ e os sócios de uma empresa a partir do site ou do domínio
- Conferir se as empresas já estão no CRM antes de abordar
- Cadastrar os leads aprovados no CRM, ou gerar a planilha de importação

## What This Skill Does

1. **Onboarding**: pergunta o que o usuário vende, o perfil de cliente, as regras do CRM e o limite diário, e salva a configuração
2. **Busca no Maps**: lê os resultados de um termo numa cidade (nome, categoria, endereço, telefone, site)
3. **Qualifica pelo site**: descarta quem não tem site, tem site fora do ar ou atua fora do nicho, e extrai ganchos para a abordagem
4. **Confirma o CNPJ**: pelo rodapé do site, pelo whois do registro.br ou pela web, e cruza o endereço da Receita com o do Maps
5. **Aplica o perfil**: porte, regime tributário, MEI e exclusões definidas pelo usuário
6. **Deduplica**: compara CNPJ e nome com o CRM e mostra quem é o dono de cada empresa que já existe
7. **Cadastra com aprovação**: empresa, negócio e sócios no funil e na etapa que o usuário escolheu no Agendor, ou um CSV pronto para importar em outro CRM, sempre dentro do limite diário

## How to Use

### Basic Usage

```
Pega 10 empresas de engenharia elétrica em Campinas e me mostra por que funcionariam.
```

```
Pode subir as aprovadas.
```

### Advanced Usage

```
Prospecta clínicas odontológicas em Curitiba, até 15. Só fora do Simples.
Me mostra também as reprovadas e o motivo.
```

```
Tenho estes sites: [lista]. Confere se estão no ar, acha o CNPJ, triangula
e me diz quais já estão no meu CRM (exportação anexa).
```

## Onboarding (primeiro uso)

Rode `python scripts/agendor.py` ou qualquer script. Se aparecer `CONFIG_AUSENTE` ou
`CONFIG_INCOMPLETA`, faça as perguntas abaixo **antes de prospectar**. Pergunte, não suponha:
nenhum destes valores tem padrão. Use o formato de múltipla escolha quando houver, em blocos
de no máximo 4 perguntas.

**Bloco 1: o que você vende e para quem**
1. Qual é a sua empresa e o que ela vende? (entra no raciocínio de "por que funcionaria")
2. Quais nichos você prospecta? (termos de busca no Maps)
3. Quais portes de empresa entram? (Micro, Pequeno Porte, Demais)
4. Empresa do Simples entra? E MEI? E empresário individual?
5. Quem nunca deve entrar? (ex.: concorrentes, multinacionais, estatais, um segmento específico)

**Bloco 2: qualificação**
6. Empresa sem site pode entrar, ou site é obrigatório?
7. O endereço do CNPJ precisa bater com o do Maps? (recomendado: sim)

**Bloco 3: CRM**
8. Qual CRM você usa? Agendor (integração pela API) ou outro (a skill gera CSV para importar)?
9. Se for **Agendor**: salve o token (Menu → Integrações → API) em `~/.secrets/agendor.txt` e rode `python scripts/agendor.py quem-sou-eu` e `python scripts/agendor.py funis`.
10. **Em qual funil do Agendor os leads prospectados vão entrar?** Mostre a lista de funis da conta pelo nome e deixe o usuário escolher. Não escolha por ele, mesmo que exista um funil chamado "Prospecção": em conta com equipe, cada vendedor pode ter o seu.
11. **Em qual etapa desse funil?** Mostre só as etapas do funil escolhido. Normalmente é a primeira, mas confirme.
12. Quem fica como responsável (normalmente ele mesmo), qual origem do lead usar, se a conta usar (escrita exatamente como está no Agendor), e se a conta é compartilhada com uma equipe.
13. Se for **outro CRM**: em que pasta salvar o CSV, e em qual funil ou lista os leads vão entrar quando ele importar (vai no nome do arquivo e na explicação de importação). Se puder, peça uma exportação atual do CRM, para deduplicar.

**Bloco 4: como o negócio é criado**
14. Qual é o padrão do título do negócio? Ofereça as variáveis `{nome}`, `{razao_social}`, `{cidade}` e `{socio}` (ex.: `Reunião | {nome}`).
15. O negócio tem valor padrão? Qual? (pode ficar sem valor)
16. Como deve ser a descrição do negócio? Peça um exemplo real que ele já escreveu.
17. Os sócios devem ser cadastrados como Pessoas ligadas à empresa?
18. **Quantos negócios novos por dia, no máximo?** Não sugira um número antes de ele responder.

Mostre o resumo das respostas, peça confirmação e salve em `~/.prospeccao/config.json`,
seguindo `config.example.json`. Para mudar alguma coisa depois, é só o usuário pedir, e você
edita o mesmo arquivo.

## Instructions

Os critérios completos estão em `references/qualificacao.md`.

### 1. Definir o alvo
Nicho (um dos `perfil_cliente.nichos`, ou o que o usuário pedir), cidade e quantidade. Sem
cidade, escolha uma com potencial para o nicho e explique em uma frase. A quantidade nunca passa
de `limite_diario`.

### 2. Buscar no Maps
Use o navegador (Claude in Chrome), numa aba própria: `google.com/maps/search/<termo>+<cidade>`.
Extraia nome, categoria, endereço, telefone e domínio do site, rolando a lista até ter por volta
do dobro da quantidade pedida. Metade costuma cair na qualificação.

### 3. Qualificar pelo site
Abra cada site no navegador. Muitos bloqueiam requisição feita sem navegador (erro 406), e parte
do texto só aparece depois de renderizar. Aplique os critérios e anote os ganchos para a abordagem.

### 4. CNPJ, triangulação e perfil
```
python scripts/cnpj_tools.py whois dominio1.com.br dominio2.com.br
python scripts/cnpj_tools.py receita 12345678000190 98765432000110 --out receita/
```
Quando o whois devolve CPF mascarado, busque na web `"<nome> <cidade> CNPJ <endereço>"`.
Resultado da web é só pista: a confirmação é o endereço da Receita bater com o do Maps. Depois,
aplique o `perfil_cliente`.

### 5. Deduplicar
Monte o `lote.json` (formato em `references/formato-lote.md`) e rode:
```
python scripts/agendor.py duplicados lote.json                  # Agendor
python scripts/exportar_csv.py lote.json --base export_crm.csv  # outro CRM
```
Empresa que já existe com outro responsável sai da lista, e o usuário fica sabendo onde ela está.

### 6. Apresentar para aprovação
Tabela com: empresa, CNPJ, porte e regime, sócios e **por que funcionaria para o que o usuário
vende**, com um gancho concreto tirado do site ou da Receita. Depois, uma lista curta das
reprovadas com o motivo de cada uma, e as duplicadas com o dono. Pergunte sobre qualquer caso
fora da regra. Nada é cadastrado nesta etapa.

### 7. Cadastrar
Só depois do ok explícito do usuário.

**Agendor:** a primeira linha da simulação mostra o destino (`DESTINO: funil "X" → etapa "Y"`).
Pergunte ao usuário, **a cada lote**, se os leads devem entrar nesse funil. Se ele quiser outro
só para este lote, rode `funis`, deixe ele escolher e use `--funil` e `--etapa`. Se quiser trocar
de vez, atualize o config.
```
python scripts/agendor.py criar lote.json                                  # simulação: confira destino e dados
python scripts/agendor.py criar lote.json --confirmar                      # grava no funil do config
python scripts/agendor.py criar lote.json --funil ID --etapa ID --confirmar  # outro funil só neste lote
```
Se aparecer `FUNIL_INVALIDO` ou `ETAPA_INVALIDA`, o funil foi apagado ou renomeado na conta:
pergunte de novo ao usuário e atualize o config.
Na primeira vez numa conta, grave **uma** empresa e peça para o usuário conferir na tela (campos,
etapa e automações da conta) antes de gravar o resto.

**Outro CRM:**
```
python scripts/exportar_csv.py lote.json
```
Entregue o caminho do CSV e explique como importar no CRM do usuário.

### 8. Conferir
No Agendor, recarregue o funil no navegador e confira se os cards estão na etapa certa. Relate o
que foi criado, com base no registro `criados_AAAAMMDD.json`.

## Regras de segurança (valem para todo usuário)

- **Ler é livre. Gravar exige ok explícito**, lote por lote.
- **Só criar.** Os scripts não editam, movem, reatribuem nem apagam registro que já existia. A única exceção é corrigir um registro que a própria skill criou na mesma sessão, e o usuário precisa ficar sabendo.
- **Nunca** criar ou alterar funil, etapa, origem, campo personalizado, automação ou usuário do CRM.
- Empresa que já existe com outro responsável **não é prospectada**. Pode ser cliente ou negociação de um colega.
- O token não entra em arquivo da skill, em log nem em mensagem. Se o usuário colar o token no chat, salve no arquivo e sugira gerar um novo depois.
- O limite diário é do usuário. A skill não decide nem aumenta sozinha.

## Example

**User**: "Pega 10 empresas de energia solar em Ribeirão Preto e me manda em tabela por que funcionariam"

**Output**:
```
| # | Empresa         | CNPJ               | Porte / regime          | Sócios              | Por que funciona                                      |
|---|-----------------|--------------------|-------------------------|---------------------|-------------------------------------------------------|
| 1 | Solaris Engenharia | 00.000.000/0001-00 | Demais, fora do Simples | Ana Souza, Rui Lima | Holding no quadro societário e unidades em SP e MG     |
| 2 | Agro Sol        | 11.111.111/0001-11 | Micro, fora do Simples  | Pedro Alves         | Usina + bateria para pivô: venda de equipamento e obra juntas |
| 3 | Luz Norte       | 22.222.222/0001-22 | Micro, Simples          | Carla Dias          | CNAE principal é informática, não energia             |
...
Reprovadas: Sol Mais (SSL quebrado), Energia Já (site não existe), Brilho Solar (endereço do CNPJ diferente do Maps)
Duplicada: Voltaica já está no CRM com outro vendedor (funil Contratos). Fora da lista.
```

Depois do ok, os negócios aparecem na etapa escolhida no onboarding, com o título no padrão do usuário.

(Nomes e CNPJs do exemplo são fictícios.)

## Tips

- Peça o dobro da quantidade no Maps. Na prática, metade cai no site ou na triangulação.
- Busca por nome na web mistura empresas parecidas. Só confie no CNPJ depois que o endereço bater.
- CNAE principal que não combina com o que o site mostra é um bom gancho: pode indicar enquadramento errado.
- Mais de uma unidade, cidade ou estado costuma indicar operação mais complexa, o que é bom sinal para serviços B2B.
- A CNPJá aceita 5 consultas por minuto. O script já espera entre elas.

## Common Use Cases

- Rotina diária de SDR: lote de novos negócios no funil de prospecção
- Abrir uma praça nova: testar uma cidade e ver quantas empresas passam no filtro
- Limpar uma lista comprada ou herdada antes de subir no CRM
- Confirmar CNPJ e sócios de uma empresa antes de uma abordagem

**Inspired by:** o fluxo manual de prospecção ativa de um SDR de contabilidade B2B (Maps → site → whois/Serasa → CRM), mapeado acompanhando um cadastro real.
