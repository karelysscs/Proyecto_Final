"""Informe en español a partir de los resultados."""
from .analysis import sensibilidad, alquiler_equilibrio
from .model import Perfil, simular

NOMBRES = {
    "apreciacion_anual": "apreciación anual de la vivienda",
    "rentabilidad_alternativa": "rentabilidad de la inversión alternativa",
    "tea_hipoteca": "TEA del crédito hipotecario",
    "crecimiento_alquiler": "crecimiento anual del alquiler",
    "alquiler_mensual": "alquiler mensual",
    "precio_vivienda": "precio de la vivienda",
}


def soles(x):
    return f"S/ {x:,.0f}"


def pct(x):
    return f"{x * 100:.1f} %"


def explicar(p: Perfil, fuentes=None):
    r = simular(p)
    s = sensibilidad(p)
    eq = alquiler_equilibrio(p)
    decision = "**COMPRAR**" if r["recomendacion"] == "comprar" else "**ALQUILAR e invertir la diferencia**"
    lineas = [
        f"# ¿Comprar o alquilar? — {p.distrito or 'Lima'}",
        "",
        f"Con un horizonte de **{p.horizonte_anios} años**, conviene {decision}.",
        f"La diferencia de patrimonio al final es {soles(abs(r['ventaja_comprar']))} "
        f"({soles(abs(r['ventaja_comprar_real']))} en soles de hoy).",
        "",
        "## Números clave",
        "",
        "| Concepto | Valor |",
        "|---|---|",
        f"| Precio de la vivienda | {soles(p.precio_vivienda)} |",
        f"| Cuota inicial ({pct(p.cuota_inicial_pct)}) | {soles(r['cuota_inicial'])} |",
        f"| Préstamo | {soles(r['prestamo'])} a {p.plazo_anios} años, TEA {pct(p.tea_hipoteca)} |",
        f"| Cuota mensual del crédito | {soles(r['cuota_mensual'])} |",
        f"| Alquiler mensual actual | {soles(p.alquiler_mensual)} |",
        f"| Gastos de cierre (incl. alcabala {soles(r['alcabala'])}) | {soles(r['gastos_cierre'])} |",
        f"| PER (precio / alquiler anual) | {r['per']:.1f} años |",
        f"| Rendimiento bruto del alquiler | {pct(r['rendimiento_bruto_alquiler'])} |",
        f"| Patrimonio final comprando | {soles(r['patrimonio_comprador'])} |",
        f"| Patrimonio final alquilando | {soles(r['patrimonio_inquilino'])} |",
        f"| Año de equilibrio | {r['anio_equilibrio'] or 'no se alcanza en el horizonte'} |",
        f"| Alquiler de equilibrio | {soles(eq) if eq else 'fuera de rango'} |",
        "",
        "## Lo que más pesa en la decisión",
        "",
    ]
    for f in s["tornado"][:3]:
        lineas.append(
            f"- **{NOMBRES.get(f['variable'], f['variable'])}**: si baja, la ventaja de comprar sería "
            f"{soles(f['ventaja_si_baja'])}; si sube, {soles(f['ventaja_si_sube'])}."
        )
    lineas += [
        "",
        "## Cómo leer esto",
        "",
        f"- Un PER mayor a ~20 años suele favorecer alquilar; menor a ~15 suele favorecer comprar. Aquí es {r['per']:.1f}.",
        f"- Si el alquiler real fuera mayor a {soles(eq) if eq else '—'}, comprar pasa a convenir.",
    ]
    if fuentes:
        lineas += ["", "## Fuentes consultadas", ""] + [f"- {u}" for u in fuentes]
    lineas += [
        "",
        "> Ejercicio educativo con supuestos simplificados. No es asesoría financiera personalizada.",
    ]
    return "\n".join(lineas)
