# Formato do lote (`lote.json`)

O lote é o arquivo que `agendor.py criar` e `exportar_csv.py` recebem. Monte o lote só com as empresas que o usuário
aprovou na tabela.

```json
{
  "cidade": "Ribeirão Preto/SP",
  "nicho": "empresas de energia",
  "empresas": [
    {
      "nome": "Solaris Engenharia",
      "site": "https://solarisengenharia.com.br",
      "email": "contato@solarisengenharia.com.br",
      "celular": "(34) 99999-0000",
      "descricao_negocio": "Distribuidora e integradora de energia solar, com holding no quadro societário.",
      "receita": { "...": "saída de cnpj_tools.py receita, sem alterar" }
    }
  ]
}
```

| Campo | Origem | Regra |
|---|---|---|
| `nome` | Maps ou site | O nome pelo qual a empresa é conhecida, sem o SEO do Maps ("Energia Solar em Ribeirão Preto \| Painel..."). Entra no título como `{nome}`. |
| `site` | Maps | URL que abriu na checagem |
| `email` | Site | Só e-mail do domínio da empresa. Omita se não houver. |
| `celular` | Maps ou site | Número que começa com 9. Entra como celular e WhatsApp. Omita se só houver fixo (o fixo vem da Receita). |
| `descricao_negocio` | Site | No estilo definido em `negocio.estilo_descricao` do config. Sem adjetivo de marketing. |
| `receita` | `cnpj_tools.py receita` | Cole o objeto inteiro. O script usa razão social, CNPJ, endereço, telefone fixo, sócios e CNAE. |

Campos vazios devem ser **omitidos**. A API do Agendor recusa `null` e string vazia.

## O que o script grava

**Empresa (Agendor):** nome, razão social, CNPJ, site, e-mail, telefone fixo (Receita), celular/WhatsApp,
endereço da Receita, origem do lead (`crm.agendor.origem_lead`), responsável (`crm.agendor.responsavel_id`) e uma
descrição no mesmo formato que o Agendor gera quando o CNPJ é digitado na tela (abertura, porte,
situação, sócios, CNAE).

**Negócio:** origem do lead (campo personalizado de `crm.agendor.origem_negocio`, conferida depois de criar), título (modelo `negocio.titulo`, com as variáveis `{nome}`, `{razao_social}`,
`{cidade}` e `{socio}`), valor (`negocio.valor`, opcional), funil, etapa, responsável e `descricao_negocio`.

**Pessoas** (se `pessoas.criar_socios`): cada sócio pessoa física, ligado à empresa, com o cargo da Receita. O tipo
do sócio vem da própria Receita (pessoa física ou jurídica). Holding e outras empresas sócias não viram Pessoa.

A tarefa de primeiro contato **não** é criada pelo script. Se a conta tiver automação por etapa,
ela cria sozinha, e o card fica vermelho até a página ser recarregada.

**CSV (outros CRMs):** `exportar_csv.py` gera uma linha por empresa com título, valor, dados da
Receita, contatos, sócios e descrição, separado por `;` e em UTF-8 com BOM (abre direto no Excel).
