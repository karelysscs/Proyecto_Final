"""CLI del motor: intake, run, sensitivity, explain, listings, app."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import listings as lst
from .analysis import alquiler_equilibrio, escenarios, sensibilidad
from .explain import explicar, soles, pct
from .intake import cargar_perfil, plantilla, validar
from .model import simular


def _json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=float))


def cmd_intake(a):
    if a.plantilla or not a.perfil:
        _json(plantilla())
        return 0
    datos = json.loads(Path(a.perfil).read_text(encoding="utf-8"))
    errores = validar(datos)
    if errores:
        print("Perfil inválido:\n- " + "\n- ".join(errores))
        return 1
    print("Perfil válido.")
    return 0


def cmd_run(a):
    r = simular(cargar_perfil(a.perfil))
    if a.json:
        _json(r)
        return 0
    print(f"Recomendación: {r['recomendacion'].upper()}  |  ventaja de comprar: {soles(r['ventaja_comprar'])}"
          f"  |  año de equilibrio: {r['anio_equilibrio']}")
    print(f"{'Año':>4} {'Valor casa':>12} {'Deuda':>12} {'Pat. compra':>13} {'Pat. alquila':>13} {'Ventaja':>12}")
    for f in r["serie"]:
        print(f"{f['anio']:>4} {f['valor_vivienda']:>12,.0f} {f['saldo_deuda']:>12,.0f} "
              f"{f['patrimonio_comprador']:>13,.0f} {f['patrimonio_inquilino']:>13,.0f} {f['ventaja_comprar']:>12,.0f}")
    return 0


def cmd_sensitivity(a):
    p = cargar_perfil(a.perfil)
    s = sensibilidad(p)
    eq = alquiler_equilibrio(p)
    if a.json:
        _json({**s, "alquiler_equilibrio": eq, "escenarios": escenarios(p)})
        return 0
    print(f"Ventaja base de comprar: {soles(s['ventaja_base'])}")
    print(f"Alquiler de equilibrio: {soles(eq) if eq else 'fuera de rango'}")
    for f in s["tornado"]:
        print(f"  {f['variable']:<26} baja→ {soles(f['ventaja_si_baja']):>14}   sube→ {soles(f['ventaja_si_sube']):>14}")
    return 0


def cmd_explain(a):
    fuentes = None
    if a.listings:
        filas, _ = lst.leer(a.listings)
        fuentes = lst.control_fuentes(filas)["urls"]
    print(explicar(cargar_perfil(a.perfil), fuentes))
    return 0


def cmd_listings(a):
    filas, errores = lst.leer(a.csv)
    ctrl = lst.control_fuentes(filas)
    res = lst.resumen_por_distrito(filas)
    if a.json:
        _json({"control_fuentes": ctrl, "resumen": res, "errores": errores})
        return 0 if ctrl["dentro_del_limite"] else 1
    print(f"Fuentes: {ctrl['fuentes_usadas']}/{ctrl['max_fuentes']} "
          f"({'OK' if ctrl['dentro_del_limite'] else 'EXCEDE EL LÍMITE'})")
    for e in errores:
        print("  ! " + e)
    for d in res:
        v = f"{soles(d['venta_m2_mediana'])}/m²" if d["venta_m2_mediana"] else "—"
        al = f"{soles(d['alquiler_m2_mediana'])}/m²" if d["alquiler_m2_mediana"] else "—"
        rb = pct(d["rendimiento_bruto"]) if d["rendimiento_bruto"] else "—"
        print(f"  {d['distrito']:<22} venta {v:>14}  alquiler {al:>10}  rend. bruto {rb}")
    return 0 if ctrl["dentro_del_limite"] else 1


def cmd_app(a):
    app = Path(__file__).resolve().parent / "app" / a.archivo
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="hl.py", description="Comprar vs alquilar en Lima")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("intake", help="plantilla o validación del perfil")
    s.add_argument("perfil", nargs="?")
    s.add_argument("--plantilla", action="store_true")
    s.set_defaults(fn=cmd_intake)

    for nombre, fn in (("run", cmd_run), ("sensitivity", cmd_sensitivity)):
        s = sub.add_parser(nombre)
        s.add_argument("perfil", nargs="?")
        s.add_argument("--json", action="store_true")
        s.set_defaults(fn=fn)

    s = sub.add_parser("explain")
    s.add_argument("perfil", nargs="?")
    s.add_argument("--listings", help="CSV para listar las fuentes al final")
    s.set_defaults(fn=cmd_explain)

    s = sub.add_parser("listings")
    s.add_argument("csv")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_listings)

    s = sub.add_parser("app", help="dashboard del modelo comprar vs alquilar")
    s.set_defaults(fn=cmd_app, archivo="app.py")

    s = sub.add_parser("resultados", help="dashboard de los resultados de búsqueda del agente")
    s.set_defaults(fn=cmd_app, archivo="resultados.py")

    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
