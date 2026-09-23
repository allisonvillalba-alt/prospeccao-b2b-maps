#!/usr/bin/env python3
"""Ferramentas de CNPJ para a prospecção: whois de domínio .br e consulta à Receita.

Uso:
  python cnpj_tools.py whois <dominio> [<dominio> ...]
  python cnpj_tools.py receita <cnpj> [<cnpj> ...] [--out pasta]

`whois` consulta o RDAP do registro.br e devolve o CNPJ do titular do domínio.
Quando o titular é pessoa física, o registro.br mascara o CPF (***.123.456-**)
e o CNPJ precisa ser procurado em outras fontes.

`receita` consulta a CNPJá (dados completos, 5 consultas por minuto) e, se ela
falhar, a BrasilAPI. A saída é um JSON normalizado por empresa, que entra no
campo "receita" do lote do Agendor (ver references/formato-lote.md).
"""
import json
import os
import re
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

CNPJA_INTERVALO = 13  # segundos entre consultas, limite gratuito da CNPJá

PORTE = {
    "Microempresa": "MICRO EMPRESA",
    "Empresa de Pequeno Porte": "EMPRESA DE PEQUENO PORTE",
    "Demais": "DEMAIS",
}
PJ_SOCIO = re.compile(r"\b(LTDA|S/?A|EIRELI|HOLDING|PARTICIPACOES)\b")


def so_digitos(s):
    return re.sub(r"\D", "", s or "")


def whois(dominio):
    dominio = dominio.lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").strip("/")
    if not dominio.endswith(".br"):
        return {"dominio": dominio, "titular": None, "obs": "domínio fora do .br, whois não traz CNPJ"}
    r = requests.get(f"https://rdap.registro.br/domain/{dominio}", timeout=20)
    if r.status_code != 200:
        return {"dominio": dominio, "titular": None, "obs": f"RDAP {r.status_code}"}
    # Só o titular (registrant). O contato técnico costuma ser a agência que fez o
    # site, e o CNPJ dela não é o da empresa.
    ids = [p.get("identifier") for e in r.json().get("entities", [])
           if "registrant" in (e.get("roles") or []) for p in e.get("publicIds", [])]
    cnpjs = [so_digitos(i) for i in ids if "*" not in i and len(so_digitos(i)) == 14]
    return {
        "dominio": dominio,
        "titular": ids[0] if ids else None,
        "cnpj": cnpjs[0] if cnpjs else None,
        "obs": None if cnpjs else "titular é pessoa física (CPF mascarado)",
    }


def _telefone(area, numero):
    return f"({area}) {numero[:-4]}-{numero[-4:]}" if area and numero else None


def _cnpja(cnpj):
    r = requests.get(f"https://open.cnpja.com/office/{cnpj}", timeout=30)
    if r.status_code != 200:
        return None
    j = r.json()
    co, a = j["company"], j["address"]
    socios = [
        {"nome": m["person"]["name"], "cargo": m["role"]["text"],
         "pessoa_fisica": m["person"].get("type") == "NATURAL" if m["person"].get("type") else None}
        for m in co.get("members", [])
    ]
    fones = j.get("phones") or []
    return {
        "cnpj": cnpj,
        "razao_social": co["name"],
        "nome_fantasia": j.get("alias"),
        "situacao": j["status"]["text"],
        "data_situacao": j.get("statusDate"),
        "abertura": j["founded"],
        "matriz": j.get("head"),
        "porte": PORTE.get(co["size"]["text"], co["size"]["text"].upper()),
        "capital_social": co.get("equity"),
        "simples": (co.get("simples") or {}).get("optant"),
        "cnae_codigo": j["mainActivity"]["id"],
        "cnae_descricao": j["mainActivity"]["text"],
        "natureza_juridica": co["nature"]["text"],
        "endereco": {
            "logradouro": a["street"],
            "numero": a["number"],
            "complemento": a.get("details"),
            "bairro": a["district"],
            "cidade": a["city"],
            "uf": a["state"],
            "cep": a["zip"],
        },
        "telefone": _telefone(fones[0]["area"], fones[0]["number"]) if fones else None,
        "email_receita": (j.get("emails") or [{}])[0].get("address"),
        "socios": socios,
        "fonte": "cnpja",
    }


def _brasilapi(cnpj):
    r = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}", timeout=30)
    if r.status_code != 200:
        return None
    j = r.json()
    tel = so_digitos(j.get("ddd_telefone_1"))
    return {
        "cnpj": cnpj,
        "razao_social": j["razao_social"],
        "nome_fantasia": j.get("nome_fantasia") or None,
        "situacao": j["descricao_situacao_cadastral"].capitalize(),
        "data_situacao": j.get("data_situacao_cadastral"),
        "abertura": j["data_inicio_atividade"],
        "matriz": j.get("descricao_identificador_matriz_filial") == "MATRIZ",
        "porte": j.get("porte"),
        "capital_social": j.get("capital_social"),
        "simples": j.get("opcao_pelo_simples"),
        "cnae_codigo": j["cnae_fiscal"],
        "cnae_descricao": j["cnae_fiscal_descricao"],
        "natureza_juridica": j.get("natureza_juridica"),
        "endereco": {
            "logradouro": f'{j.get("descricao_tipo_de_logradouro", "")} {j.get("logradouro", "")}'.strip(),
            "numero": j.get("numero"),
            "complemento": j.get("complemento") or None,
            "bairro": j.get("bairro"),
            "cidade": j.get("municipio"),
            "uf": j.get("uf"),
            "cep": j.get("cep"),
        },
        "telefone": _telefone(tel[:2], tel[2:]) if len(tel) >= 10 else None,
        "email_receita": j.get("email") or None,
        # identificador_de_socio: 1 = pessoa jurídica, 2 = pessoa física, 3 = estrangeiro
        "socios": [{"nome": s["nome_socio"], "cargo": s["qualificacao_socio"],
                    "pessoa_fisica": {1: False, 2: True}.get(s.get("identificador_de_socio"))}
                   for s in j.get("qsa", [])],
        "fonte": "brasilapi",
    }


def receita(cnpj):
    cnpj = so_digitos(cnpj)
    dados = _cnpja(cnpj) or _brasilapi(cnpj)
    if dados is None:
        return {"cnpj": cnpj, "erro": "CNPJ não encontrado na CNPJá nem na BrasilAPI"}
    # A fonte informa o tipo do sócio. O regex só decide quando ela não informa.
    dados["socios_pessoa_fisica"] = [
        s for s in dados["socios"]
        if s["pessoa_fisica"] or (s["pessoa_fisica"] is None and not PJ_SOCIO.search(s["nome"].upper()))
    ]
    return dados


def main(argv):
    if len(argv) < 2 or argv[0] not in ("whois", "receita"):
        print(__doc__)
        return 1
    cmd, args = argv[0], argv[1:]
    out = None
    if "--out" in args:
        i = args.index("--out")
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
        os.makedirs(out, exist_ok=True)
    resultado = []
    for n, alvo in enumerate(args):
        if cmd == "whois":
            resultado.append(whois(alvo))
        else:
            if n:
                time.sleep(CNPJA_INTERVALO)
            dados = receita(alvo)
            resultado.append(dados)
            if out and "erro" not in dados:
                with open(os.path.join(out, f'{dados["cnpj"]}.json'), "w", encoding="utf-8") as f:
                    json.dump(dados, f, ensure_ascii=False, indent=1)
    print(json.dumps(resultado, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
