"""Costo de oportunidad con instrumentos de bajo riesgo en Perú.

Uso:
  python index_returns.py --horizonte 10
  python index_returns.py --horizonte 5 --tasa deposito_plazo_1a=0.05 --inflacion 0.025 --json
"""
import argparse
import json
import sys

TASAS = {  # nominales anuales en PEN, referenciales (verificar en SBS/BCRP/SMV)
    "deposito_plazo_1a": 0.045,
    "fondo_mutuo_renta_fija": 0.048,
    "letras_tesoro_1a": 0.044,
    "bono_soberano_10a": 0.063,
}
IMPUESTO = 0.05

PESOS = {  # por horizonte
    "corto": {"deposito_plazo_1a": 0.5, "fondo_mutuo_renta_fija": 0.3, "letras_tesoro_1a": 0.2},
    "medio": {"deposito_plazo_1a": 0.35, "fondo_mutuo_renta_fija": 0.3, "bono_soberano_10a": 0.35},
    "largo": {"deposito_plazo_1a": 0.2, "fondo_mutuo_renta_fija": 0.2, "bono_soberano_10a": 0.6},
}


def tramo(horizonte):
    return "corto" if horizonte <= 3 else "medio" if horizonte < 10 else "largo"


def calcular(horizonte, tasas, inflacion):
    netas = {k: v * (1 - IMPUESTO) for k, v in tasas.items()}
    reales = {k: (1 + v) / (1 + inflacion) - 1 for k, v in netas.items()}
    pesos = PESOS[tramo(horizonte)]
    recomendada = sum(netas[k] * w for k, w in pesos.items())
    usadas = [netas[k] for k in pesos]
    return {
        "horizonte_anios": horizonte,
        "tramo": tramo(horizonte),
        "inflacion": inflacion,
        "tasas_netas": netas,
        "tasas_reales": reales,
        "pesos": pesos,
        "tasa_recomendada": round(recomendada, 4),
        "tasa_recomendada_real": round((1 + recomendada) / (1 + inflacion) - 1, 4),
        "rango": [round(min(usadas), 4), round(max(usadas), 4)],
        "valor_futuro_por_sol": round((1 + recomendada) ** horizonte, 4),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizonte", type=int, default=10)
    ap.add_argument("--inflacion", type=float, default=0.02)
    ap.add_argument("--tasa", action="append", default=[], help="instrumento=tasa, p.ej. bono_soberano_10a=0.065")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    tasas = dict(TASAS)
    for t in a.tasa:
        k, v = t.split("=")
        if k not in tasas:
            ap.error(f"instrumento desconocido: {k}. Opciones: {', '.join(tasas)}")
        tasas[k] = float(v)

    r = calcular(a.horizonte, tasas, a.inflacion)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    print(f"Horizonte {r['horizonte_anios']} años (tramo {r['tramo']}), inflación {r['inflacion']:.1%}")
    for k in r["tasas_netas"]:
        print(f"  {k:<24} neta {r['tasas_netas'][k]:.2%}   real {r['tasas_reales'][k]:.2%}")
    print(f"Tasa recomendada (nominal, neta): {r['tasa_recomendada']:.2%}  "
          f"| real: {r['tasa_recomendada_real']:.2%}  | rango {r['rango'][0]:.2%}–{r['rango'][1]:.2%}")


if __name__ == "__main__":
    main()
