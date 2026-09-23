#!/usr/bin/env python3
"""Cliente mínimo e seguro da API do Agendor para a prospecção.

Uso:
  python agendor.py quem-sou-eu
  python agendor.py funis
  python agendor.py duplicados <lote.json>
  python agendor.py criar <lote.json>               # simulação: só mostra o que faria
  python agendor.py criar <lote.json> --confirmar   # grava de verdade

Regras embutidas (valem para qualquer usuário):
  - Só faz leitura e criação. Não existe caminho no código para editar ou apagar
    registro que já estava no CRM.
  - `criar` sem --confirmar nunca grava.
  - Empresa que já existe no CRM (mesmo CNPJ ou nome parecido) bloqueia o lote
    inteiro. Com --pular-duplicados, ela é ignorada e o resto segue.
  - Respeita o `limite_diario` que o usuário definiu no onboarding, contando os
    negócios que ele já criou hoje no funil.
  - Se a API responder 5xx, confere se o registro foi criado antes de tentar de novo.

Token: variável de ambiente AGENDOR_TOKEN ou arquivo ~/.secrets/agendor.txt.
Configuração: ~/.prospeccao/config.json, criado no onboarding (ver config.py).
"""
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import requests

import config as conf
from util import normal

BASE = "https://api.agendor.com.br/v3"


def token():
    t = os.environ.get("AGENDOR_TOKEN")
    if t:
        return t.strip()
    arq = Path.home() / ".secrets" / "agendor.txt"
    if arq.exists():
        return arq.read_text(encoding="utf-8").strip()
    sys.exit("Token não encontrado. Defina AGENDOR_TOKEN ou salve em ~/.secrets/agendor.txt")


H = {"Authorization": f"Token {token()}", "Content-Type": "application/json"}


def _pedido(metodo, caminho, **kw):
    for tentativa in range(4):
        r = requests.request(metodo, BASE + caminho, headers=H, timeout=40, **kw)
        if r.status_code < 500 or metodo != "GET":
            return r
        time.sleep(15 * (tentativa + 1))
    return r


def get(caminho, **params):
    r = _pedido("GET", caminho, params=params)
    r.raise_for_status()
    return r.json()


def paginar(caminho, **params):
    pagina, itens = 1, []
    while True:
        dados = get(caminho, page=pagina, per_page=100, **params).get("data", [])
        itens += dados
        if len(dados) < 100:
            return itens
        pagina += 1


def limpar(x):
    """A API recusa campo vazio ("contact[mobile] is empty"): remove None e ""."""
    if isinstance(x, dict):
        return {k: limpar(v) for k, v in x.items() if v not in (None, "", [], {})}
    return x


# ---------- leitura ----------

def quem_sou_eu():
    me = get("/users/me")["data"]
    usuarios = get("/users")["data"]
    print(json.dumps({"eu": {"id": me["id"], "nome": me["name"]},
                      "usuarios": [{"id": u["id"], "nome": u["name"]} for u in usuarios]},
                     ensure_ascii=False, indent=1))


def funis():
    for f in get("/funnels")["data"]:
        print(f'{f["id"]}  {f["name"]}')
        for e in f.get("dealStages", []):
            print(f'    etapa {e["id"]}  {e["name"]}')


def carregar_lote(caminho):
    lote = json.loads(Path(caminho).read_text(encoding="utf-8"))
    empresas = lote["empresas"] if isinstance(lote, dict) else lote
    for e in empresas:
        if "receita" not in e or "erro" in e["receita"]:
            sys.exit(f'{e.get("nome")}: falta o bloco "receita" (rode cnpj_tools.py receita).')
    return empresas


def achar_duplicados(empresas, orgs=None):
    orgs = orgs if orgs is not None else paginar("/organizations")
    achados = {}
    for e in empresas:
        cnpj = e["receita"]["cnpj"]
        chaves = {normal(e["nome"]), normal(e["receita"]["razao_social"])} - {""}
        hits = []
        for o in orgs:
            nomes = {normal(o.get("name")), normal(o.get("legalName"))} - {""}
            mesmo_cnpj = (o.get("cnpj") or "") == cnpj
            mesmo_nome = any(len(c) >= 4 and len(n) >= 4 and (c == n or c in n or n in c)
                             for c in chaves for n in nomes)
            if mesmo_cnpj or mesmo_nome:
                hits.append({"id": o["id"], "nome": o["name"], "cnpj": o.get("cnpj"),
                             "responsavel": (o.get("ownerUser") or {}).get("name"),
                             "motivo": "CNPJ igual" if mesmo_cnpj else "nome parecido",
                             "link": o.get("_webUrl")})
        if hits:
            achados[e["nome"]] = hits
    return achados, orgs


def duplicados(caminho):
    achados, orgs = achar_duplicados(carregar_lote(caminho))
    print(f"{len(orgs)} empresas lidas no CRM.")
    print(json.dumps(achados or "nenhum duplicado", ensure_ascii=False, indent=1))


def criados_hoje(cfg):
    # /funnels/{id}/deals responde 404 e os filtros de /deals são ignorados:
    # pagina tudo e filtra aqui.
    hoje = dt.date.today().isoformat()
    return sum(1 for d in paginar("/deals")
               if d["dealStage"]["funnel"]["id"] == cfg["crm"]["agendor"]["funil_id"]
               and (d.get("author") or {}).get("id") == cfg["crm"]["agendor"]["responsavel_id"]
               and d.get("createdAt", "").startswith(hoje))


# ---------- escrita (só criação) ----------

def descricao_empresa(r):
    socios = "<br />".join(f'{s["nome"].upper()} - ' for s in r["socios"]) or f'{r["razao_social"].upper()} - '
    return (f'DATA DE ABERTURA DA EMPRESA: {r["abertura"]}<br /><br />'
            f'PORTE DA EMPRESA: {r["porte"]}<br /><br />'
            f'SITUAÇÃO CADASTRAL: {r["situacao"]}<br /><br />'
            f'DATA DA SITUAÇÃO CADASTRAL: {r.get("data_situacao") or ""}<br /><br />'
            f'QUADRO DE SÓCIOS E ADMINISTRADORES:<br />{socios}<br /><br />'
            f'CÓDIGO E DESCRIÇÃO DA ATIVIDADE ECONÔMICA PRINCIPAL:<br />{r["cnae_codigo"]} - {r["cnae_descricao"]}')


def titulo_caso(nome):
    minusc = {"de", "da", "do", "dos", "das", "e"}
    return " ".join(p if p.lower() in minusc else p.capitalize() for p in nome.lower().split())


def corpo_empresa(e, cfg):
    r, a = e["receita"], e["receita"]["endereco"]
    numero = str(a.get("numero") or "")
    return limpar({
        "name": e["nome"],
        "legalName": r["razao_social"],
        "cnpj": r["cnpj"],
        "description": descricao_empresa(r),
        "website": e.get("site"),
        "ownerUser": cfg["crm"]["agendor"]["responsavel_id"],
        "leadOrigin": cfg["crm"]["agendor"].get("origem_lead"),
        "contact": {"email": e.get("email"), "work": r.get("telefone"),
                    "mobile": e.get("celular"), "whatsapp": e.get("celular")},
        # No POST/PUT o endereço vai em snake_case; em camelCase a API ignora calada.
        "address": {"country": "Brasil", "state": a.get("uf"), "city": a.get("cidade"),
                    "district": a.get("bairro"), "street_name": (a.get("logradouro") or "").upper(),
                    "street_number": int(numero) if numero.isdigit() else None,
                    "additional_info": a.get("complemento"), "postal_code": a.get("cep")},
    })


def corpo_negocio(e, cfg):
    return limpar({
        "title": conf.titulo(cfg, e),
        "description": e.get("descricao_negocio"),
        "value": cfg["negocio"].get("valor"),
        "funnel": cfg["crm"]["agendor"]["funil_id"],
        "dealStage": cfg["crm"]["agendor"]["etapa_id"],
        "ownerUser": cfg["crm"]["agendor"]["responsavel_id"],
    })


def post(caminho, corpo, conferir_cnpj=None):
    r = _pedido("POST", caminho, json=corpo)
    if r.status_code >= 500 and conferir_cnpj:
        # A gravação pode ter acontecido mesmo com erro: confere antes de repetir.
        time.sleep(20)
        existente = [o for o in paginar("/organizations") if o.get("cnpj") == conferir_cnpj]
        if existente:
            return existente[0]
        r = _pedido("POST", caminho, json=corpo)
    if r.status_code >= 300:
        raise RuntimeError(f"{caminho} -> {r.status_code}: {r.text[:400]}")
    return r.json()["data"]


def criar(caminho, confirmar=False, pular_duplicados=False):
    cfg = conf.carregar()
    if cfg["crm"]["tipo"] != "agendor":
        sys.exit("O CRM configurado não é o Agendor. Use exportar_csv.py.")
    empresas = carregar_lote(caminho)

    achados, _ = achar_duplicados(empresas)
    if achados and not pular_duplicados:
        print("PAROU: estas empresas já existem no CRM. Decida com o usuário antes de seguir.")
        print(json.dumps(achados, ensure_ascii=False, indent=1))
        return 2
    empresas = [e for e in empresas if e["nome"] not in achados]

    ja_hoje = criados_hoje(cfg)
    vagas = max(cfg["limite_diario"] - ja_hoje, 0)
    if len(empresas) > vagas:
        print(f"Limite diário: {ja_hoje} já criados hoje, cabem mais {vagas}. "
              f"{len(empresas) - vagas} ficam para amanhã.")
        empresas = empresas[:vagas]

    if not confirmar:
        print("SIMULAÇÃO (nada foi gravado). Rode de novo com --confirmar depois do ok do usuário.\n")
        for e in empresas:
            socios = [titulo_caso(s["nome"]) for s in e["receita"]["socios_pessoa_fisica"]] if cfg.get("pessoas", {}).get("criar_socios") else []
            print(json.dumps({"empresa": corpo_empresa(e, cfg), "negocio": corpo_negocio(e, cfg),
                              "pessoas": socios}, ensure_ascii=False, indent=1))
        return 0

    log = []
    for e in empresas:
        org = post("/organizations", corpo_empresa(e, cfg), conferir_cnpj=e["receita"]["cnpj"])
        neg = post(f'/organizations/{org["id"]}/deals', corpo_negocio(e, cfg))
        pessoas = []
        if cfg.get("pessoas", {}).get("criar_socios"):
            for s in e["receita"]["socios_pessoa_fisica"]:
                p = post("/people", limpar({"name": titulo_caso(s["nome"]), "organization": org["id"],
                                             "role": s["cargo"], "ownerUser": cfg["crm"]["agendor"]["responsavel_id"]}))
                pessoas.append({"id": p["id"], "nome": p["name"]})
        item = {"empresa": e["nome"], "org_id": org["id"], "negocio_id": neg["id"],
                "titulo": neg["title"], "pessoas": pessoas, "link": neg.get("_webUrl")}
        log.append(item)
        print("OK", json.dumps(item, ensure_ascii=False))

    arq_log = Path(caminho).with_name(f"criados_{dt.date.today():%Y%m%d}.json")
    anteriores = json.loads(arq_log.read_text(encoding="utf-8")) if arq_log.exists() else []
    arq_log.write_text(json.dumps(anteriores + log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(log)} negócios criados. Registro em {arq_log}")
    return 0


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "quem-sou-eu":
        quem_sou_eu()
    elif cmd == "funis":
        funis()
    elif cmd == "duplicados" and len(argv) > 1:
        duplicados(argv[1])
    elif cmd == "criar" and len(argv) > 1:
        return criar(argv[1], "--confirmar" in argv, "--pular-duplicados" in argv)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
