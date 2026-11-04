"""Hook PreToolUse: limita las fuentes web del agente (modo clase).

- WebFetch: cuenta URLs distintas; al superar `max_fuentes` bloquea.
- WebSearch: cuenta consultas; al superar `max_busquedas` bloquea.

Claude Code envía el evento como JSON por stdin. Salir con código 2 bloquea la
herramienta y el texto de stderr se le muestra a Claude como motivo.

Uso manual:  python limit_sources.py --reset   |   python limit_sources.py --estado
"""
import json
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CONFIG = AQUI.parent / "skills" / "buy-vs-rent" / "scripts" / "housing_lima" / "config" / "defaults.json"
ESTADO = AQUI / ".estado_fuentes.json"


def limites():
    try:
        b = json.loads(CONFIG.read_text(encoding="utf-8"))["busqueda"]
        return int(b["max_fuentes"]), int(b["max_busquedas"])
    except Exception:
        return 10, 5


def leer_estado():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def guardar_estado(estado):
    ESTADO.write_text(json.dumps(estado, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    if "--reset" in sys.argv:
        ESTADO.unlink(missing_ok=True)
        print("Contador de fuentes reiniciado.")
        return 0
    if "--estado" in sys.argv:
        print(json.dumps(leer_estado(), indent=2, ensure_ascii=False))
        return 0

    evento = json.load(sys.stdin)
    herramienta = evento.get("tool_name", "")
    entrada = evento.get("tool_input", {}) or {}
    sesion = evento.get("session_id", "sin-sesion")
    max_fuentes, max_busquedas = limites()

    estado = leer_estado()
    s = estado.setdefault(sesion, {"urls": [], "busquedas": 0})
    s.setdefault("eventos", [])
    s.setdefault("inicio", datetime.now().isoformat(timespec="seconds"))

    def registrar(tipo, valor, resultado):
        s["eventos"].append({"hora": datetime.now().isoformat(timespec="seconds"),
                             "tipo": tipo, "valor": valor, "resultado": resultado})
        guardar_estado(estado)

    if herramienta == "WebFetch":
        url = (entrada.get("url") or "").strip()
        if url in s["urls"]:
            registrar("fuente", url, "repetida")  # releer una fuente ya contada no consume cupo
            return 0
        if len(s["urls"]) >= max_fuentes:
            registrar("fuente", url, "bloqueada")
            print(
                f"Límite de {max_fuentes} fuentes alcanzado (modo clase). "
                "Trabaja con las fuentes ya consultadas: " + ", ".join(s["urls"]),
                file=sys.stderr,
            )
            return 2
        s["urls"].append(url)
        registrar("fuente", url, "permitida")
    elif herramienta == "WebSearch":
        consulta = entrada.get("query", "")
        if s["busquedas"] >= max_busquedas:
            registrar("busqueda", consulta, "bloqueada")
            print(
                f"Límite de {max_busquedas} búsquedas alcanzado (modo clase). "
                "Usa los resultados que ya tienes.",
                file=sys.stderr,
            )
            return 2
        s["busquedas"] += 1
        registrar("busqueda", consulta, "permitida")
    return 0


if __name__ == "__main__":
    sys.exit(main())
