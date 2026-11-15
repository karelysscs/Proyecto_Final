"""Datos en vivo del API del BCRP (estadisticas.bcrp.gob.pe).

Series usadas:
- PD04640PD  Tipo de cambio venta, sistema bancario SBS (S/ por US$), diario.
- PN07848NM  Tasa activa promedio de la banca, MN, Hipotecario (TEA %), mensual.
- PN07815NM  Tasa pasiva promedio de la banca, MN, depósitos a plazo de 360 días a más (TEA %), mensual.

Si el API no responde, se usan los valores de config/defaults.json.
"""
import json
from datetime import date, timedelta
from urllib.request import Request, urlopen

API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{ini}/{fin}"
WEB = "https://estadisticas.bcrp.gob.pe/estadisticas/series/{tipo}/resultados/{codigo}/html"

SERIES = {
    "tipo_cambio": {"codigo": "PD04640PD", "tipo": "diarias", "escala": 1.0,
                    "nombre": "Tipo de cambio venta (S/ por US$)"},
    "tea_hipoteca": {"codigo": "PN07848NM", "tipo": "mensuales", "escala": 0.01,
                     "nombre": "TEA hipotecaria promedio, banca, MN"},
    "rentabilidad_alternativa": {"codigo": "PN07815NM", "tipo": "mensuales", "escala": 0.01,
                                 "nombre": "Depósito a plazo 360 días a más, banca, MN"},
}


def _ultimo_valor(codigo, dias_atras):
    fin = date.today()
    ini = fin - timedelta(days=dias_atras)
    if codigo.endswith("M"):  # series mensuales: AAAA-MM
        ini_s, fin_s = ini.strftime("%Y-%m"), fin.strftime("%Y-%m")
    else:
        ini_s, fin_s = ini.isoformat(), fin.isoformat()
    req = Request(API.format(codigo=codigo, ini=ini_s, fin=fin_s), headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as resp:
        datos = json.loads(resp.read().decode("utf-8"))
    for periodo in reversed(datos.get("periods", [])):
        valor = periodo["values"][0]
        try:
            return float(valor), periodo["name"]
        except ValueError:  # "n.d."
            continue
    raise ValueError(f"sin datos para {codigo}")


def indicadores(respaldo):
    """Devuelve {clave: {valor, periodo, fuente, url, en_vivo}} para cada serie.

    `respaldo` es un dict con los valores por defecto (mismas claves) por si el API falla.
    """
    salida = {}
    for clave, s in SERIES.items():
        url = WEB.format(tipo=s["tipo"], codigo=s["codigo"])
        try:
            valor, periodo = _ultimo_valor(s["codigo"], 30 if s["tipo"] == "diarias" else 200)
            salida[clave] = {"valor": valor * s["escala"], "periodo": periodo, "nombre": s["nombre"],
                             "url": url, "en_vivo": True}
        except Exception:  # noqa: BLE001 - cualquier fallo de red usa el respaldo
            salida[clave] = {"valor": respaldo[clave], "periodo": "valor por defecto", "nombre": s["nombre"],
                             "url": url, "en_vivo": False}
    return salida


if __name__ == "__main__":
    for k, v in indicadores({"tipo_cambio": 3.75, "tea_hipoteca": 0.088, "rentabilidad_alternativa": 0.05}).items():
        print(k, v)
