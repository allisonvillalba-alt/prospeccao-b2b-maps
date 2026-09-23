# API do Agendor: o que foi aprendido na prática

Base: `https://api.agendor.com.br/v3`. Autenticação: cabeçalho `Authorization: Token <token>`.
O token é gerado em Menu → Integrações → API e tem as mesmas permissões do usuário.

## Comportamentos que não estão óbvios na documentação

| Situação | Comportamento |
|---|---|
| Campo com `null` ou `""` no POST | Erro 400 (`contact[mobile] is empty`). Omita o campo. |
| Endereço em camelCase (`streetName`) no POST/PUT | Aceito com 200, mas **ignorado em silêncio**. Use snake_case: `street_name`, `street_number`, `additional_info`, `postal_code`. A leitura (GET) devolve em camelCase. |
| `GET /organizations?text=...` ou `?cnpj=...` | O filtro é ignorado e a API devolve a primeira página de tudo. Para deduplicar, pagine todas as empresas (`per_page=100`) e compare localmente. |
| `GET /funnels/{id}/deals` | 404. Use `GET /deals` paginado e filtre por `dealStage.funnel.id` localmente: os parâmetros `funnel` e `createdDateGt` também são ignorados. |
| `leadOrigin` | Aceita o nome da origem em texto (`"prospecção ativa"`) e liga à origem existente. |
| DELETE com token de vendedor | 401. O token comum não apaga, e isso é uma proteção útil. Registro criado por engano precisa ser apagado na tela. |
| 503 esporádico | Acontece. A gravação pode ou não ter sido feita. Confira pelo CNPJ antes de repetir o POST. |
| Tarefas do negócio (`/deals/{id}/tasks`) | Exige filtro de data (`createdDateGt` e similares). |
| Campos personalizados do negócio | Só aparecem com `?withCustomFields=true` no GET. Vêm em `customFields`, pela chave do campo (ex.: `origem_do_lead`). Campo de lista devolve `[{"id": 76460, "value": "Prospecção Ativa"}]`. |
| Gravar campo personalizado | `{"customFields": {"origem_do_lead": [76460]}}`, com os ids das opções. Funciona no PUT; o script também manda no POST e confere depois, completando com PUT se não tiver gravado. |
| Lista de campos e opções | Não há endpoint (`/custom_fields` dá 404). As opções saem dos negócios já existentes: `agendor.py campos-negocio`. |
| Duas "origens" | A empresa tem `leadOrigin` (origem da empresa). O negócio pode ter um campo personalizado próprio de origem. São campos diferentes e os dois aparecem na tela. |

## Endpoints usados

| Método | Caminho | Para quê |
|---|---|---|
| GET | `/users/me`, `/users` | id do responsável |
| GET | `/funnels` | funis e etapas (ids) |
| GET | `/deals` | todos os negócios, filtrados localmente (conta do limite diário) |
| GET | `/organizations` | deduplicação |
| POST | `/organizations` | criar empresa |
| POST | `/organizations/{id}/deals` | criar negócio ligado à empresa (`funnel`, `dealStage`, `ownerUser`) |
| POST | `/people` | criar sócio ligado à empresa (`organization`) |

## Conta compartilhada

Funil, etapa, origem, campo personalizado e automação são da equipe. A skill nunca cria nem altera
nenhum deles. Se o config apontar para um funil que não existe, pare e pergunte.
