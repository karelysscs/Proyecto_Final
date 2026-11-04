"""Lectura de avisos (listings.csv), resumen por distrito y control de fuentes."""
import csv
from collections import defaultdict
from statistics import median
from urllib.parse import urlparse

from .intake import config

COLUMNAS = ["id", "fuente", "url", "fecha_consulta", "distrito", "operacion", "precio",
            "moneda", "area_m2", "dormitorios", "banos", "estacionamiento", "notas"]


def leer(ruta):
    cfg = config()
    tc = cfg["tipo_cambio"]
    filas, errores = [], []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            try:
                precio = float(row["precio"])
                area = float(row["area_m2"])
                if row["operacion"] not in ("venta", "alquiler"):
                    raise ValueError("operacion debe ser venta o alquiler")
                if row["moneda"] == "USD":
                    precio *= tc
                elif row["moneda"] != "PEN":
                    raise ValueError("moneda debe ser PEN o USD")
                filas.append({**row, "precio_pen": precio, "area_m2": area, "precio_m2": precio / area})
            except (KeyError, ValueError) as e:
                errores.append(f"fila {i}: {e}")
    return filas, errores


def control_fuentes(filas):
    """Cuenta URLs distintas y las compara con el máximo configurado."""
    maximo = config()["busqueda"]["max_fuentes"]
    urls = sorted({r["url"].strip() for r in filas if r.get("url")})
    dominios = sorted({urlparse(u).netloc for u in urls})
    return {"max_fuentes": maximo, "fuentes_usadas": len(urls), "dentro_del_limite": len(urls) <= maximo,
            "urls": urls, "dominios": dominios}


def resumen_por_distrito(filas):
    grupos = defaultdict(lambda: {"venta": [], "alquiler": []})
    for r in filas:
        grupos[r["distrito"]][r["operacion"]].append(r["precio_m2"])
    salida = []
    for distrito, g in sorted(grupos.items()):
        venta_m2 = median(g["venta"]) if g["venta"] else None
        alquiler_m2 = median(g["alquiler"]) if g["alquiler"] else None
        rend = alquiler_m2 * 12 / venta_m2 if venta_m2 and alquiler_m2 else None
        salida.append({
            "distrito": distrito,
            "n_venta": len(g["venta"]),
            "n_alquiler": len(g["alquiler"]),
            "venta_m2_mediana": venta_m2,
            "alquiler_m2_mediana": alquiler_m2,
            "rendimiento_bruto": rend,
            "per": 1 / rend if rend else None,
        })
    return salida
