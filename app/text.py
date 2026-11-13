import re
import unicodedata

NEGATION = re.compile(r"\b(nao|ainda nao|inexiste|inexistencia de|ausencia de|sem|pendente de|aguardando)\b")

PII_PATTERNS = [
    ("[CPF]", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    ("[CNPJ]", re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")),
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("[PHONE]", re.compile(r"\(?\b\d{2}\)?\s?9?\d{4}-?\d{4}\b")),
]

MONEY = re.compile(r"r\$\s*([\d.]+,\d{2})")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


# Mesmo efeito de normalize(), mas mantendo cada posição alinhada com o texto original,
# para recortar a evidência do documento como ele foi escrito.
def normalize_aligned(text: str) -> str:
    out = []
    for c in text or "":
        base = unicodedata.normalize("NFKD", c)[0] if c.strip() else " "
        out.append(base.lower())
    return "".join(out)


def mask_pii(text: str) -> str:
    for token, pattern in PII_PATTERNS:
        text = pattern.sub(token, text)
    return text


def format_brl(value: float) -> str:
    us = f"{value:,.2f}"
    return "R$ " + us.replace(",", "_").replace(".", ",").replace("_", ".")


def parse_brl(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))


def is_negated(text: str, start: int, window: int = 30) -> bool:
    return bool(NEGATION.search(text[max(0, start - window):start]))


def find_affirmed(pattern: re.Pattern, text: str) -> re.Match | None:
    for match in pattern.finditer(text):
        if not is_negated(text, match.start()):
            return match
    return None


def excerpt(text: str, start: int, end: int, margin: int = 60) -> str:
    left = max(0, start - margin)
    right = min(len(text), end + margin)
    prefix = "..." if left > 0 else ""
    suffix = "..." if right < len(text) else ""
    return f"{prefix}{text[left:right].strip()}{suffix}"
