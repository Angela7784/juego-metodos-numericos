import re

_SUP = {
    '0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹',
    '-':'⁻','+':'⁺',
    'a':'ᵃ','b':'ᵇ','c':'ᶜ','d':'ᵈ','e':'ᵉ','f':'ᶠ','g':'ᵍ','h':'ʰ','i':'ⁱ',
    'j':'ʲ','k':'ᵏ','l':'ˡ','m':'ᵐ','n':'ⁿ','o':'ᵒ','p':'ᵖ','r':'ʳ','s':'ˢ',
    't':'ᵗ','u':'ᵘ','v':'ᵛ','w':'ʷ','x':'ˣ','y':'ʸ','z':'ᶻ',
}


def fmt_math(text: str) -> str:
    """Convierte notación de computadora a símbolos matemáticos Unicode."""
    # pow(base, exp) → base^exp  (antes de procesar ^)
    def _pow(m):
        base, exp = m.group(1).strip(), m.group(2).strip()
        return base + '^' + exp
    text = re.sub(r'\bpow\(([^,]+),\s*([^)]+)\)', _pow, text)
    # Multiplicación
    text = text.replace('*', '·')
    # Potencias: ^n → superíndice (dígitos y signo)
    def _sup(m):
        return ''.join(_SUP.get(c, c) for c in m.group(1))
    text = re.sub(r'\^([-+]?\d+|[a-zA-Z])', _sup, text)
    # Raíz cuadrada
    text = re.sub(r'\bsqrt\b', '√', text)
    # Pi
    text = re.sub(r'\bpi\b', 'π', text)
    return text
