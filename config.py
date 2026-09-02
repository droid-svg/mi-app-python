# -*- coding: utf-8 -*-
"""Configuración de OCUPAMOR Mobile (Kivy)."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# Directorio de datos (funciona en escritorio y Android)
try:
    from kivy.utils import platform
    if platform == "android":
        from android.storage import app_storage_path  # type: ignore
        APP_DIR = app_storage_path()
    else:
        APP_DIR = os.path.join(os.path.expanduser("~"), ".ocupamor")
except Exception:
    APP_DIR = os.path.join(os.path.expanduser("~"), ".ocupamor")

os.makedirs(APP_DIR, exist_ok=True)
LOCAL_USERS_FILE = os.path.join(APP_DIR, "users.json")
PROGRESS_FILE = os.path.join(APP_DIR, "progress.json")
SETTINGS_FILE = os.path.join(APP_DIR, "learning_settings.json")
MISSIONS_FILE = os.path.join(APP_DIR, "missions.json")

APP_TITLE = "OCUPAMOR: Aprendiendo con calma"

# Paletas de color (hex -> rgba float para Kivy)
def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    return [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)] + [a]

THEMES = {
    "escolar": {
        "name": "Modo Escolar",
        "bg": hex_rgba("#FFFFFF"),
        "card": hex_rgba("#F2F4F8"),
        "primary": hex_rgba("#1565C0"),
        "primary_dark": hex_rgba("#0D47A1"),
        "secondary": hex_rgba("#2E7D32"),
        "accent": hex_rgba("#F9A825"),
        "text": hex_rgba("#10131A"),
        "text_soft": hex_rgba("#3A4051"),
        "calm": hex_rgba("#5C7C8A"),
        "white": hex_rgba("#FFFFFF"),
        # Tonos suaves derivados (misma familia escolar, sin estridencias)
        "soft": hex_rgba("#E3ECF7"),
        "soft_2": hex_rgba("#E6F1E8"),
        "soft_3": hex_rgba("#FBF0DA"),
        "success": hex_rgba("#2E7D32"),
        "line": hex_rgba("#D5DCE7"),
    },
}

# Categorías configurables (Módulo 5)
LEARNING_CATEGORIES = [
    ("vocales", "Vocales y fonemas"),
    ("silabas", "Construcción silábica"),
    ("vocabulario", "Vocabulario básico"),
    ("comprension", "Comprensión lectora"),
    ("trabalenguas", "Trabalenguas y articulación"),
    ("oraciones", "Construcción de oraciones"),
    ("sinonimos", "Sinónimos y antónimos"),
    ("cognitivo", "Retos cognitivos"),
    ("senas", "Lenguaje de señas"),
    ("emociones", "Expresión emocional"),
    ("matematicas", "Matemáticas (números y figuras)"),
]
