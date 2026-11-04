"""Carga y validación del perfil del usuario."""
import json
from pathlib import Path

from .model import Perfil

AQUI = Path(__file__).resolve().parent
CONFIG = AQUI / "config" / "defaults.json"
SCHEMA = AQUI / "schemas" / "perfil.schema.json"

TIPOS = {"number": (int, float), "integer": (int,), "string": (str,), "boolean": (bool,)}


def config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def plantilla():
    return dict(config()["perfil"])


def validar(datos):
    """Valida contra el schema (subconjunto: required, type, minimum, maximum). Devuelve lista de errores."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errores = [f"falta '{k}'" for k in schema.get("required", []) if k not in datos]
    for k, v in datos.items():
        regla = schema["properties"].get(k)
        if regla is None:
            errores.append(f"campo desconocido '{k}'")
            continue
        tipos = TIPOS[regla["type"]]
        if isinstance(v, bool) and regla["type"] != "boolean" or not isinstance(v, tipos):
            errores.append(f"'{k}' debe ser {regla['type']}")
            continue
        if "minimum" in regla and v < regla["minimum"]:
            errores.append(f"'{k}'={v} es menor que {regla['minimum']}")
        if "maximum" in regla and v > regla["maximum"]:
            errores.append(f"'{k}'={v} es mayor que {regla['maximum']}")
    return errores


def cargar_perfil(ruta=None):
    """Combina defaults + JSON del usuario, valida y devuelve un Perfil."""
    cfg = config()
    datos = dict(cfg["perfil"])
    if ruta:
        datos.update(json.loads(Path(ruta).read_text(encoding="utf-8")))
    errores = validar(datos)
    if errores:
        raise ValueError("Perfil inválido: " + "; ".join(errores))
    return Perfil.desde_dict({**datos, "uit": cfg["uit"]})
