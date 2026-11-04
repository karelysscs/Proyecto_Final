"""Valida un listings.csv y verifica que no supere el límite de fuentes.

Uso: python check_listings.py data/listings.csv
Sale con código 1 si hay errores o si se excede el máximo de fuentes.
"""
import sys
from pathlib import Path

MOTOR = Path(__file__).resolve().parents[2] / "buy-vs-rent" / "scripts"
sys.path.insert(0, str(MOTOR))

from housing_lima import listings as lst  # noqa: E402


def main(ruta):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    filas, errores = lst.leer(ruta)
    ctrl = lst.control_fuentes(filas)
    n_venta = sum(r["operacion"] == "venta" for r in filas)
    n_alq = sum(r["operacion"] == "alquiler" for r in filas)
    print(f"Filas válidas: {len(filas)} (venta {n_venta}, alquiler {n_alq})")
    print(f"Fuentes: {ctrl['fuentes_usadas']}/{ctrl['max_fuentes']}  dominios: {', '.join(ctrl['dominios'])}")
    for e in errores:
        print("  ! " + e)
    if not ctrl["dentro_del_limite"]:
        print(f"ERROR: se usaron {ctrl['fuentes_usadas']} fuentes; el máximo es {ctrl['max_fuentes']}.")
    if any("EJEMPLO" in (r.get("notas") or "") for r in filas):
        print("Aviso: quedan filas de EJEMPLO de la plantilla.")
    return 0 if ctrl["dentro_del_limite"] and not errores else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
