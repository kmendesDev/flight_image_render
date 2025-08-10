# image_renderer.py
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Dict, Any
import unicodedata
import datetime
import uuid
from io import BytesIO

ASSETS_DIR = Path(__file__).parent / "assets"
TEMPLATE_PATH = ASSETS_DIR / "template.png"
# Mantemos a referência caso no futuro você decida colocar uma fonte aqui.
FONT_PATH = ASSETS_DIR / "DejaVuSans.ttf"

# Ajuste as coordenadas conforme seu template
COORDS = {
    "companhia": (550, 250),
    "classe_passagem": (1100, 250),
    "procedencia": (310, 390),
    "destino": (320, 530),
    "data": (250, 670),
    "janela_horarios": (1100, 670),
    "tempo_voo": (330, 810),
    "tipo_voo": (1100, 900),
}

def _try_truetype(path_like: Path | str, size: int):
    try:
        return ImageFont.truetype(str(path_like), size=size)
    except Exception:
        return None

def _load_font(size: int = 24):
    """
    Sem se preocupar com fontes.
    1) Se existir uma .ttf em assets (ex.: DejaVuSans.ttf), usa.
    2) Tenta algumas fontes comuns do macOS.
    3) Cai no ImageFont.load_default() (funciona, mas pode ter limitações com acentos).
    """
    # 1) fonte no projeto
    if FONT_PATH.exists():
        f = _try_truetype(FONT_PATH, size)
        if f:
            return f

    # 2) tentativas comuns no macOS
    mac_candidates = [
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ]
    for p in mac_candidates:
        f = _try_truetype(p, size)
        if f:
            return f

    # 3) fallback absoluto
    return ImageFont.load_default()

def _normalize_key(k: str) -> str:
    """
    Normaliza chaves: remove acento, trim, lower, e mapeia nomes comuns.
    Ex.: 'classe de passagem ' -> 'classe_passagem'
    """
    s = unicodedata.normalize("NFKD", k).encode("ASCII", "ignore").decode("ASCII")
    s = s.strip().lower()
    mappings = {
        "classe de passagem": "classe_passagem",
        "tempo do voo": "tempo_voo",
        "tipo de voo": "tipo_voo",
        "horario da decolagem da procedencia": "hora_decolagem",
        "horario do pouso": "hora_pouso",
    }
    return mappings.get(s, s)

def normalize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    nd: Dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(k, str):
            nd[_normalize_key(k)] = v
    return nd

def render_image(payload: Dict[str, Any], template_path: Path = TEMPLATE_PATH) -> Image.Image:
    data = normalize_payload(payload)

    if not template_path.exists():
        raise FileNotFoundError(f"Template não encontrado: {template_path}")

    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    font = _load_font(36)
    color = (0, 0, 0)  # preto

    # Campos principais
    draw.text(COORDS["companhia"], str(data.get("companhia", "N/A")), fill=color, font=font)
    draw.text(COORDS["classe_passagem"], str(data.get("classe_passagem", "N/A")), fill=color, font=font)
    draw.text(COORDS["procedencia"], str(data.get("procedencia", "N/A")), fill=color, font=font)
    draw.text(COORDS["destino"], str(data.get("destino", "N/A")), fill=color, font=font)
    draw.text(COORDS["data"], str(data.get("data", "N/A")), fill=color, font=font)

    janela = f"{data.get('hora_decolagem', 'N/A')} - {data.get('hora_pouso', 'N/A')}"
    draw.text(COORDS["janela_horarios"], janela, fill=color, font=font)

    draw.text(COORDS["tempo_voo"], str(data.get("tempo_voo", "N/A")), fill=color, font=font)
    draw.text(COORDS["tipo_voo"], str(data.get("tipo_voo", "N/A")), fill=color, font=font)

    return img

def save_and_bytes(img: Image.Image):
    out_dir = ASSETS_DIR / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"flight_quote_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}.png"
    out_path = out_dir / fname

    img.save(out_path, format="PNG")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return out_path, buf
