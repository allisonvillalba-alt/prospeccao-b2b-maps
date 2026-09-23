"""Funções pequenas compartilhadas entre os scripts."""
import re
import unicodedata

# Palavras que aparecem em quase todo nome do nicho e atrapalham a comparação.
GENERICAS = r"\b(ltda|me|epp|eireli|s/?a|cia|comercio|servicos|solucoes|grupo|do|da|de|e)\b"


def normal(s):
    """Nome reduzido para comparar empresas: sem acento, sufixo societário ou pontuação."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(GENERICAS, "", s)
    return re.sub(r"[^a-z0-9]", "", s)
