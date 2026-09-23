"""Configuração do usuário da skill.

Fica fora da pasta da skill, para a skill poder ser compartilhada sem levar dados
de ninguém: ~/.prospeccao/config.json (ou o caminho em PROSPECCAO_CONFIG).
Quem cria o arquivo é o onboarding descrito no SKILL.md, a partir das respostas
do usuário. Nenhum valor tem padrão: o que faltar interrompe o script.
"""
import json
import os
import sys
from pathlib import Path

CAMINHO = Path(os.environ.get("PROSPECCAO_CONFIG", Path.home() / ".prospeccao" / "config.json"))

OBRIGATORIOS = {
    "todos": ["limite_diario", "negocio.titulo", "crm.tipo"],
    "agendor": ["crm.agendor.funil_id", "crm.agendor.etapa_id", "crm.agendor.responsavel_id"],
    "csv": ["crm.csv.pasta"],
}


def _pegar(cfg, chave):
    valor = cfg
    for parte in chave.split("."):
        if not isinstance(valor, dict):
            return None
        valor = valor.get(parte)
    return valor


def carregar():
    if not CAMINHO.exists():
        sys.exit(f"CONFIG_AUSENTE: {CAMINHO} não existe. Faça o onboarding do SKILL.md com o usuário antes de continuar.")
    cfg = json.loads(CAMINHO.read_text(encoding="utf-8"))
    tipo = _pegar(cfg, "crm.tipo")
    faltando = [c for c in OBRIGATORIOS["todos"] + OBRIGATORIOS.get(tipo, [])
                if _pegar(cfg, c) in (None, "", [])]
    if faltando:
        sys.exit(f"CONFIG_INCOMPLETA: pergunte ao usuário e preencha {', '.join(faltando)} em {CAMINHO}.")
    return cfg


def titulo(cfg, empresa):
    """Aplica o modelo de título do usuário. Variáveis: {nome} {razao_social} {cidade} {socio}."""
    r = empresa["receita"]
    socios = r.get("socios_pessoa_fisica") or []
    return cfg["negocio"]["titulo"].format(
        nome=empresa["nome"],
        razao_social=r["razao_social"],
        cidade=(r.get("endereco") or {}).get("cidade", ""),
        socio=socios[0]["nome"].title() if socios else "",
    ).replace(" |  | ", " | ").strip(" |")


if __name__ == "__main__":
    # `python config.py`: diz se o onboarding já foi feito, sem precisar de token.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    cfg = carregar()
    print(f"CONFIG_OK: {CAMINHO}")
    print(json.dumps(cfg, ensure_ascii=False, indent=1))
