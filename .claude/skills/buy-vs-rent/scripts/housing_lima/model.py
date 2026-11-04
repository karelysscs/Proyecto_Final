"""Simulación mensual comprar vs alquilar."""
from dataclasses import dataclass, asdict, fields


@dataclass
class Perfil:
    precio_vivienda: float
    alquiler_mensual: float
    area_m2: float = 90
    distrito: str = ""
    cuota_inicial_pct: float = 0.20
    tea_hipoteca: float = 0.088
    plazo_anios: int = 20
    horizonte_anios: int = 10
    apreciacion_anual: float = 0.03
    crecimiento_alquiler: float = 0.03
    rentabilidad_alternativa: float = 0.05
    inflacion: float = 0.02
    mantenimiento_pct: float = 0.01
    predial_pct: float = 0.004
    arbitrios_mensual: float = 80
    gastos_cierre_pct: float = 0.015
    aplica_alcabala: bool = True
    comision_venta_pct: float = 0.03
    seguro_desgravamen_mensual: float = 0.00028
    seguro_inmueble_anual: float = 0.0003
    bono: float = 0
    uit: float = 5500

    @classmethod
    def desde_dict(cls, d):
        validos = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in validos})

    def con(self, **cambios):
        return Perfil(**{**asdict(self), **cambios})


def tasa_mensual(tasa_anual):
    return (1 + tasa_anual) ** (1 / 12) - 1


def cuota_francesa(prestamo, tem, n_meses):
    if prestamo <= 0:
        return 0.0
    if tem == 0:
        return prestamo / n_meses
    return prestamo * tem / (1 - (1 + tem) ** -n_meses)


def simular(p: Perfil):
    """Devuelve un dict con resumen y serie anual de patrimonios."""
    tem = tasa_mensual(p.tea_hipoteca)
    r_inv = tasa_mensual(p.rentabilidad_alternativa)
    r_aprec = tasa_mensual(p.apreciacion_anual)
    n = p.plazo_anios * 12
    meses = p.horizonte_anios * 12

    inicial = p.precio_vivienda * p.cuota_inicial_pct
    prestamo = max(0.0, p.precio_vivienda - inicial - p.bono)
    cuota = cuota_francesa(prestamo, tem, n)
    alcabala = 0.03 * max(0.0, p.precio_vivienda - 10 * p.uit) if p.aplica_alcabala else 0.0
    cierre = p.precio_vivienda * p.gastos_cierre_pct + alcabala

    saldo = prestamo
    valor = p.precio_vivienda
    alquiler = p.alquiler_mensual
    cartera_comprador = 0.0
    cartera_inquilino = inicial + cierre  # el inquilino invierte lo que el comprador gastó al inicio
    intereses_pagados = 0.0
    serie = []

    for m in range(1, meses + 1):
        interes = saldo * tem
        desgravamen = saldo * p.seguro_desgravamen_mensual
        if m <= n and saldo > 0:
            amortizacion = min(cuota - interes, saldo)
            pago = interes + amortizacion
            saldo -= amortizacion
            intereses_pagados += interes
        else:
            pago = 0.0
        costo_comprador = (
            pago
            + desgravamen
            + valor * p.seguro_inmueble_anual / 12
            + valor * p.mantenimiento_pct / 12
            + valor * p.predial_pct / 12
            + p.arbitrios_mensual
        )
        cartera_comprador *= 1 + r_inv
        cartera_inquilino *= 1 + r_inv
        diferencia = costo_comprador - alquiler
        if diferencia > 0:
            cartera_inquilino += diferencia
        else:
            cartera_comprador -= diferencia
        valor *= 1 + r_aprec

        if m % 12 == 0:
            anio = m // 12
            deflactor = (1 + p.inflacion) ** anio
            pat_c = valor * (1 - p.comision_venta_pct) - saldo + cartera_comprador
            pat_i = cartera_inquilino
            serie.append({
                "anio": anio,
                "valor_vivienda": valor,
                "saldo_deuda": saldo,
                "alquiler_mensual": alquiler,
                "costo_mensual_comprador": costo_comprador,
                "patrimonio_comprador": pat_c,
                "patrimonio_inquilino": pat_i,
                "ventaja_comprar": pat_c - pat_i,
                "ventaja_comprar_real": (pat_c - pat_i) / deflactor,
            })
            alquiler *= 1 + p.crecimiento_alquiler

    final = serie[-1]
    equilibrio = next((f["anio"] for f in serie if f["ventaja_comprar"] > 0), None)
    return {
        "perfil": asdict(p),
        "cuota_inicial": inicial,
        "prestamo": prestamo,
        "cuota_mensual": cuota,
        "alcabala": alcabala,
        "gastos_cierre": cierre,
        "intereses_pagados": intereses_pagados,
        "per": p.precio_vivienda / (p.alquiler_mensual * 12),
        "rendimiento_bruto_alquiler": p.alquiler_mensual * 12 / p.precio_vivienda,
        "patrimonio_comprador": final["patrimonio_comprador"],
        "patrimonio_inquilino": final["patrimonio_inquilino"],
        "ventaja_comprar": final["ventaja_comprar"],
        "ventaja_comprar_real": final["ventaja_comprar_real"],
        "anio_equilibrio": equilibrio,
        "recomendacion": "comprar" if final["ventaja_comprar"] > 0 else "alquilar",
        "serie": serie,
    }
