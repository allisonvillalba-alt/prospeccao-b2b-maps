# Critérios de qualificação

Critérios padrão da skill, na ordem em que são aplicados. Uma empresa só vai para o CRM se
passar por todas as etapas. O que for específico de cada vendedor (perfil de cliente, portes,
regimes, exclusões) vem do `perfil_cliente` do config, respondido no onboarding.

## 1. Site (primeiro filtro)

Vale quando `qualificacao.exige_site` é `true`. A empresa é **descartada** se:

1. O Maps não mostra site. Link só de WhatsApp (`wa.me`), Instagram ou Facebook não conta como site.
2. O site está fora do ar: erro de DNS, erro de SSL, "site suspenso" ou página de hospedagem padrão.
3. A atividade descrita no site é diferente do nicho pesquisado. Exemplo: numa busca por "energia",
   uma loja de material elétrico ou uma imobiliária é descartada.

Se passar, leia o site inteiro (home, sobre, serviços, rodapé) e anote:
- o que a empresa faz de verdade, para a descrição do negócio
- números que ela divulga (MW instalados, projetos, anos de mercado), marcando como "segundo o site"
- e-mail do próprio domínio (`contato@`, `comercial@`); e-mail pessoal (gmail, hotmail) não entra
- mais de uma unidade, cidade ou estado: é gancho tributário
- linhas de negócio com tributação mais complexa (locação de usinas, energia por assinatura,
  mercado livre, venda de equipamento com instalação)

Sinais de site abandonado (template com texto repetido, copyright de anos atrás) não eliminam,
mas entram como observação.

## 2. CNPJ e triangulação

Ordem de busca do CNPJ:
1. Rodapé do site
2. Whois do domínio `.br` (`cnpj_tools.py whois`). Se o titular for CPF, o registro.br mascara o número.
3. Busca na web por `"<nome> <cidade> CNPJ <endereço do Maps>"` (Econodata, cnpj.biz, Casa dos Dados, Serasa)

Depois, `cnpj_tools.py receita <cnpj>` traz os dados oficiais. **Triangulação:** o endereço da
Receita precisa bater com o endereço do Maps.

| Situação | Decisão |
|---|---|
| Mesma rua e número | Aprovada |
| Mesma rua e número, sala ou complemento diferente | Aprovada |
| Telefone diferente | Aprovada (é comum) |
| Rua ou número diferente, mesma cidade | **Pergunte ao usuário.** Pode ser mudança de endereço. |
| Outra cidade, ou CNAE sem relação com o nicho | Descartada |
| CNPJ não encontrado | Descartada |
| Situação diferente de Ativa | Descartada |

Mesmo nome não prova que é a mesma empresa. Busca na web costuma misturar CNPJs parecidos.
Só a triangulação de endereço confirma.

## 3. Perfil

Compare os dados da Receita com o `perfil_cliente` do config:
- porte fora de `portes_aceitos`: descartada
- optante do Simples com `aceita_simples: false`: descartada
- MEI com `aceita_mei: false`: descartada
- empresário individual (razão social = nome + CPF) com `aceita_empresario_individual: false`: descartada
- qualquer item de `excluir` (ex.: multinacional, estatal, concorrente): descartada
- `observacoes`: regras em texto livre do usuário, aplique com bom senso e pergunte na dúvida

Além disso, anote no resumo o que ajuda a priorizar: porte, capital social, regime, número de sócios,
  CNAE que não combina com a atividade real (sinal de enquadramento errado) e empresário
  individual (conversa natural sobre virar Ltda).
- O e-mail que aparece na Receita muitas vezes é do escritório contábil que cuida da empresa,
  e não da própria empresa. Não use como contato. (Para quem vende contabilidade, ele mostra quem é o concorrente.)

## 4. Deduplicação no CRM

Antes de propor o cadastro, rode `agendor.py duplicados` (ou `exportar_csv.py --base` com a
exportação do CRM do usuário). Se a empresa já existe:
- com outro responsável: **não cadastre**. Ela pode ser cliente ou negociação de um colega.
  Conte ao usuário onde está (funil, etapa, dono).
- com o próprio usuário como responsável: pergunte se quer um negócio novo.
