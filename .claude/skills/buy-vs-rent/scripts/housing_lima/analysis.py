"""Sensibilidad, alquiler de equilibrio y escenarios."""
from .model import Perfil, simular

VARIABLES_CLAVE = {
    "apreciacion_anual": 0.02,
    "rentabilidad_alternativa": 0.02,
    "tea_hipoteca": 0.015,
    "crecimiento_alquiler": 0.02,
    "alquiler_mensual": None,  # ±15 %
    "precio_vivienda": None,   # ±10 %
}


def _delta(p, var, d):
    if d is not None:
        return d
    return getattr(p, var) * (0.15 if var == "alquiler_mensual" else 0.10)


def sensibilidad(p: Perfil):
    """Tornado: ventaja de comprar al bajar/subir cada variable clave."""
    base = simular(p)["ventaja_comprar"]
    filas = []
    for var, d in VARIABLES_CLAVE.items():
        delta = _delta(p, var, d)
        valor = getattr(p, var)
        baja = simular(p.con(**{var: valor - delta}))["ventaja_comprar"]
        sube = simular(p.con(**{var: valor + delta}))["ventaja_comprar"]
        filas.append({
            "variable": var,
            "valor_base": valor,
            "delta": delta,
            "ventaja_si_baja": baja,
            "ventaja_si_sube": sube,
            "rango": abs(sube - baja),
        })
    filas.sort(key=lambda f: f["rango"], reverse=True)
    return {"ventaja_base": base, "tornado": filas}


def alquiler_equilibrio(p: Perfil, tol=1.0):
    """Alquiler mensual al que comprar y alquilar empatan (bisección)."""
    lo, hi = 1.0, p.precio_vivienda * 0.05
    f = lambda a: simular(p.con(alquiler_mensual=a))["ventaja_comprar"]
    if f(lo) > 0 or f(hi) < 0:
        return None
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def escenarios(p: Perfil, apreciaciones=(0.0, 0.02, 0.04, 0.06), rentabilidades=(0.03, 0.05, 0.07, 0.09)):
    """Matriz de ventaja de comprar: filas = apreciación, columnas = rentabilidad alternativa."""
    return {
        "apreciaciones": list(apreciaciones),
        "rentabilidades": list(rentabilidades),
        "ventaja": [
            [simular(p.con(apreciacion_anual=a, rentabilidad_alternativa=r))["ventaja_comprar"] for r in rentabilidades]
            for a in apreciaciones
        ],
    }
