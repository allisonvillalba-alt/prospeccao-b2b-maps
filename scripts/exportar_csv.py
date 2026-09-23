#!/usr/bin/env python3
"""Exporta o lote aprovado em CSV, para importar em qualquer CRM ou planilha.

Uso:
  python exportar_csv.py <lote.json> [--base export_do_crm.csv]

Para quem não usa o Agendor. O CSV sai na pasta `crm.csv.pasta` do config, com uma
linha por empresa e colunas que a maioria dos CRMs aceita na importação (HubSpot,
Pipedrive, RD Station, Piperun, Moskit, planilha).

--base: exportação atual do CRM do usuário, em CSV. Empresas com o mesmo CNPJ ou
nome parecido saem do arquivo e são listadas, igual à deduplicação do Agendor.

O limite diário é controlado por ~/.prospeccao/historico.json, porque aqui não há
CRM para consultar.
"""
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import config as conf
from util import normal

COLUNAS = [
    "Título do negócio", "Valor", "Empresa", "Razão social", "CNPJ", "Site", "E-mail",
    "Telefone", "Celular", "Endereço", "Bairro", "Cidade", "UF", "CEP", "Porte", "Simples",
    "CNAE principal", "Sócios", "Descrição do negócio",
]


def linha(cfg, e):
    r, a = e["receita"], e["receita"]["endereco"]
    endereco = " ".join(str(x) for x in (a.get("logradouro"), a.get("numero"), a.get("complemento")) if x)
    return {
        "Título do negócio": conf.titulo(cfg, e),
        "Valor": cfg["negocio"].get("valor") or "",
        "Empresa": e["nome"],
        "Razão social": r["razao_social"],
        "CNPJ": r["cnpj"],
        "Site": e.get("site", ""),
        "E-mail": e.get("email", ""),
        "Telefone": r.get("telefone") or "",
        "Celular": e.get("celular", ""),
        "Endereço": endereco,
        "Bairro": a.get("bairro") or "",
        "Cidade": a.get("cidade") or "",
        "UF": a.get("uf") or "",
        "CEP": a.get("cep") or "",
        "Porte": r.get("porte") or "",
        "Simples": {True: "Sim", False: "Não"}.get(r.get("simples"), ""),
        "CNAE principal": f'{r["cnae_codigo"]} - {r["cnae_descricao"]}',
        "Sócios": "; ".join(s["nome"].title() for s in r.get("socios_pessoa_fisica", [])),
        "Descrição do negócio": e.get("descricao_negocio", ""),
    }


def ler_base(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        amostra = f.read(4096)
        f.seek(0)
        dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t")
        registros = list(csv.DictReader(f, dialect=dialeto))
    cnpjs, nomes = set(), set()
    for reg in registros:
        for k, v in reg.items():
            if not v:
                continue
            chave = (k or "").lower()
            if "cnpj" in chave:
                cnpjs.add("".join(c for c in v if c.isdigit()))
            elif any(p in chave for p in ("empresa", "organiza", "company", "nome", "razão", "razao")):
                n = normal(v)
                if len(n) >= 4:
                    nomes.add(n)
    return cnpjs, nomes


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv:
        print(__doc__)
        return 1
    cfg = conf.carregar()
    lote = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    empresas = lote["empresas"] if isinstance(lote, dict) else lote

    if "--base" in argv:
        cnpjs, nomes = ler_base(argv[argv.index("--base") + 1])
        dup = [e["nome"] for e in empresas
               if e["receita"]["cnpj"] in cnpjs
               or any(n in nomes or any(n in x or x in n for x in nomes)
                      for n in {normal(e["nome"]), normal(e["receita"]["razao_social"])} if len(n) >= 4)]
        if dup:
            print("Já existem no CRM (fora do arquivo):", ", ".join(dup))
        empresas = [e for e in empresas if e["nome"] not in dup]

    hist_arq = conf.CAMINHO.with_name("historico.json")
    hist = json.loads(hist_arq.read_text(encoding="utf-8")) if hist_arq.exists() else {}
    hoje = dt.date.today().isoformat()
    vagas = max(cfg["limite_diario"] - hist.get(hoje, 0), 0)
    if len(empresas) > vagas:
        print(f"Limite diário: cabem mais {vagas} hoje. {len(empresas) - vagas} ficam para amanhã.")
        empresas = empresas[:vagas]

    pasta = Path(cfg["crm"]["csv"]["pasta"]).expanduser()
    pasta.mkdir(parents=True, exist_ok=True)
    saida = pasta / f"prospeccao_{dt.datetime.now():%Y%m%d_%H%M}.csv"
    with open(saida, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
        w.writeheader()
        for e in empresas:
            w.writerow(linha(cfg, e))

    hist[hoje] = hist.get(hoje, 0) + len(empresas)
    hist_arq.write_text(json.dumps(hist, indent=1), encoding="utf-8")
    print(f"{len(empresas)} empresas exportadas para {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
