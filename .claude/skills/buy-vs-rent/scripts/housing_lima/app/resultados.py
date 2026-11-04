"""Dashboard Streamlit: resultados de la búsqueda del agente market-data.

Muestra la bitácora del hook (búsquedas y fuentes, con su cupo), los avisos de
data/listings.csv, el resumen por distrito y cómo esos datos alimentan el modelo.

Ejecutar: python .claude/skills/buy-vs-rent/scripts/hl.py resultados
"""
import json
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from housing_lima import listings as lst  # noqa: E402
from housing_lima.intake import config, plantilla  # noqa: E402
from housing_lima.model import Perfil, simular  # noqa: E402

RAIZ = Path(__file__).resolve().parents[6]
CSV_DEFECTO = RAIZ / "data" / "listings.csv"
ESTADO_HOOK = RAIZ / ".claude" / "hooks" / ".estado_fuentes.json"

cfg = config()
MAX_FUENTES = cfg["busqueda"]["max_fuentes"]
MAX_BUSQUEDAS = cfg["busqueda"]["max_busquedas"]

st.set_page_config(page_title="Resultados de búsqueda — Lima", layout="wide")
st.title("Resultados de la búsqueda del agente")
st.caption(f"Modo clase: máximo {MAX_FUENTES} fuentes y {MAX_BUSQUEDAS} búsquedas por sesión.")


def soles(x):
    return f"S/ {x:,.0f}" if x is not None and pd.notna(x) else "—"


def compacto(x):
    return f"S/ {x / 1000:,.0f} mil"


@st.cache_data
def leer_bitacora(_mtime):
    try:
        return json.loads(ESTADO_HOOK.read_text(encoding="utf-8"))
    except Exception:
        return {}


@st.cache_data
def leer_avisos(ruta, _mtime):
    filas, errores = lst.leer(ruta)
    return filas, errores


# ---------- Datos de entrada ----------
with st.sidebar:
    st.header("Datos")
    subido = st.file_uploader("Otro listings.csv (opcional)", type="csv")
    if subido:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(subido.getvalue())
        ruta_csv = Path(tmp.name)
        st.caption(f"Usando: {subido.name}")
    else:
        ruta_csv = CSV_DEFECTO
        st.caption("Usando: data/listings.csv")
    if st.button("Recargar"):
        st.cache_data.clear()

bitacora = leer_bitacora(ESTADO_HOOK.stat().st_mtime if ESTADO_HOOK.exists() else 0)

if ruta_csv.exists():
    filas, errores = leer_avisos(str(ruta_csv), ruta_csv.stat().st_mtime)
else:
    filas, errores = [], []

if not filas and not bitacora:
    st.info(
        "Todavía no hay resultados. Pídele al agente en Claude Code, por ejemplo:\n\n"
        "> Usa el agente market-data para buscar departamentos de 90 m² en venta y alquiler "
        "en Santiago de Surco.\n\n"
        "Cuando termine, pulsa **Recargar** en la barra lateral."
    )
    st.stop()

avisos = pd.DataFrame(filas)
ctrl = lst.control_fuentes(filas)

# ---------- KPIs ----------
sesiones = sorted(bitacora.items(), key=lambda kv: kv[1].get("inicio", ""), reverse=True)
sesion_actual = sesiones[0][1] if sesiones else {"urls": [], "busquedas": 0, "eventos": []}

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Fuentes (CSV)", f"{ctrl['fuentes_usadas']} / {MAX_FUENTES}")
k2.metric("Fuentes (agente)", f"{len(sesion_actual['urls'])} / {MAX_FUENTES}")
k3.metric("Búsquedas", f"{sesion_actual['busquedas']} / {MAX_BUSQUEDAS}")
k4.metric("Venta", int((avisos["operacion"] == "venta").sum()) if len(avisos) else 0)
k5.metric("Alquiler", int((avisos["operacion"] == "alquiler").sum()) if len(avisos) else 0)
st.progress(min(len(sesion_actual["urls"]) / MAX_FUENTES, 1.0),
            text=f"Cupo de fuentes usado en la última sesión: {len(sesion_actual['urls'])} de {MAX_FUENTES}")

if not ctrl["dentro_del_limite"]:
    st.error(f"El CSV cita {ctrl['fuentes_usadas']} fuentes; el máximo es {MAX_FUENTES}.")
for e in errores:
    st.warning(e)
if len(avisos) and avisos["notas"].fillna("").str.contains("EJEMPLO").any():
    st.warning("El CSV todavía tiene filas de EJEMPLO de la plantilla.")

tab_bit, tab_fuentes, tab_avisos, tab_distritos, tab_modelo = st.tabs(
    ["Bitácora del agente", "Fuentes", "Avisos", "Por distrito", "Llevar al modelo"]
)

# ---------- Bitácora ----------
with tab_bit:
    if not sesiones:
        st.info("El hook todavía no registró búsquedas en este proyecto.")
    else:
        etiquetas = {f"{v.get('inicio', '¿?')}  ·  {k[:8]}": k for k, v in sesiones}
        elegida = etiquetas[st.selectbox("Sesión de Claude Code", list(etiquetas))]
        eventos = pd.DataFrame(bitacora[elegida].get("eventos", []))
        if eventos.empty:
            st.caption("Sesión registrada antes de que el hook guardara la bitácora; solo hay URLs:")
            st.dataframe(pd.DataFrame({"url": bitacora[elegida]["urls"]}), hide_index=True)
        else:
            eventos["hora"] = pd.to_datetime(eventos["hora"]).dt.strftime("%H:%M:%S")
            eventos["tipo"] = eventos["tipo"].map({"busqueda": "🔎 búsqueda", "fuente": "🌐 fuente"})
            eventos["resultado"] = eventos["resultado"].map(
                {"permitida": "✅ permitida", "repetida": "↺ repetida (sin costo)", "bloqueada": "⛔ bloqueada"})
            st.dataframe(eventos[["hora", "tipo", "valor", "resultado"]], hide_index=True,
                         use_container_width=True,
                         column_config={"valor": st.column_config.TextColumn("consulta / URL", width="large")})
            bloqueos = (eventos["resultado"] == "⛔ bloqueada").sum()
            if bloqueos:
                st.caption(f"El límite de la clase bloqueó {bloqueos} intento(s) en esta sesión.")

# ---------- Fuentes ----------
with tab_fuentes:
    if avisos.empty:
        st.info("No hay avisos en el CSV todavía.")
    else:
        fuentes = (avisos.groupby(["url", "fuente"])
                   .agg(avisos=("url", "size"),
                        venta=("operacion", lambda s: (s == "venta").sum()),
                        alquiler=("operacion", lambda s: (s == "alquiler").sum()),
                        consultado=("fecha_consulta", "max"))
                   .reset_index())
        fuentes.insert(0, "dominio", fuentes["url"].map(lambda u: urlparse(u).netloc))
        abiertas = set(sesion_actual["urls"])
        fuentes["abierta_por_el_agente"] = fuentes["url"].isin(abiertas) if abiertas else None
        st.dataframe(fuentes.sort_values("avisos", ascending=False), hide_index=True, use_container_width=True,
                     column_config={"url": st.column_config.LinkColumn("url", width="large")})
        st.bar_chart(fuentes.groupby("dominio")[["venta", "alquiler"]].sum(), horizontal=True)

# ---------- Avisos ----------
with tab_avisos:
    if avisos.empty:
        st.info("No hay avisos en el CSV todavía.")
    else:
        c1, c2, c3 = st.columns(3)
        distritos = sorted(avisos["distrito"].unique())
        sel_d = c1.multiselect("Distrito", distritos, default=distritos)
        sel_o = c2.multiselect("Operación", ["venta", "alquiler"], default=["venta", "alquiler"])
        rango = c3.slider("Área (m²)", int(avisos["area_m2"].min()), int(avisos["area_m2"].max()) + 1,
                          (int(avisos["area_m2"].min()), int(avisos["area_m2"].max()) + 1))
        f = avisos[avisos["distrito"].isin(sel_d) & avisos["operacion"].isin(sel_o)
                   & avisos["area_m2"].between(*rango)]
        st.dataframe(
            f[["distrito", "operacion", "precio", "moneda", "precio_pen", "area_m2", "precio_m2",
               "dormitorios", "banos", "fuente", "url", "notas"]],
            hide_index=True, use_container_width=True,
            column_config={
                "precio_pen": st.column_config.NumberColumn("precio S/", format="%.0f"),
                "precio_m2": st.column_config.NumberColumn("S/ por m²", format="%.0f"),
                "url": st.column_config.LinkColumn("url"),
            })
        st.caption(f"{len(f)} avisos · USD convertidos a S/ con tipo de cambio {cfg['tipo_cambio']}")
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Venta: área vs precio")
            v = f[f["operacion"] == "venta"]
            if len(v):
                st.scatter_chart(v, x="area_m2", y="precio_pen", color="distrito")
        with g2:
            st.subheader("Alquiler: área vs precio")
            a = f[f["operacion"] == "alquiler"]
            if len(a):
                st.scatter_chart(a, x="area_m2", y="precio_pen", color="distrito")

# ---------- Por distrito ----------
resumen = pd.DataFrame(lst.resumen_por_distrito(filas)) if filas else pd.DataFrame()
with tab_distritos:
    if resumen.empty:
        st.info("No hay avisos en el CSV todavía.")
    else:
        st.dataframe(resumen, hide_index=True, use_container_width=True, column_config={
            "venta_m2_mediana": st.column_config.NumberColumn("venta S/ por m² (mediana)", format="%.0f"),
            "alquiler_m2_mediana": st.column_config.NumberColumn("alquiler S/ por m² (mediana)", format="%.1f"),
            "rendimiento_bruto": st.column_config.NumberColumn("rendimiento bruto", format="%.3f"),
            "per": st.column_config.NumberColumn("PER (años)", format="%.1f"),
        })
        st.subheader("Rendimiento bruto del alquiler por distrito")
        st.bar_chart(resumen.dropna(subset=["rendimiento_bruto"]).set_index("distrito")["rendimiento_bruto"])
        st.caption("PER > 20 suele favorecer alquilar; PER < 15 suele favorecer comprar.")

# ---------- Llevar al modelo ----------
with tab_modelo:
    completos = resumen.dropna(subset=["venta_m2_mediana", "alquiler_m2_mediana"]) if len(resumen) else resumen
    if completos.empty:
        st.info("Se necesita al menos un distrito con avisos de venta y de alquiler.")
    else:
        base = plantilla()
        c1, c2 = st.columns(2)
        distrito = c1.selectbox("Distrito", completos["distrito"])
        area = c2.number_input("Área de la vivienda (m²)", 30, 400, int(base["area_m2"]))
        fila = completos.set_index("distrito").loc[distrito]
        precio = fila["venta_m2_mediana"] * area
        alquiler = fila["alquiler_m2_mediana"] * area
        p = Perfil.desde_dict({**base, "distrito": distrito, "area_m2": area, "precio_vivienda": precio,
                               "alquiler_mensual": alquiler, "uit": cfg["uit"]})
        r = simular(p)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Precio estimado", compacto(precio))
        m2.metric("Alquiler / mes", soles(alquiler))
        m3.metric("Conviene", r["recomendacion"].capitalize())
        m4.metric(f"Ventaja comprar ({p.horizonte_anios} a)", compacto(r["ventaja_comprar"]))
        st.line_chart(pd.DataFrame(r["serie"]).set_index("anio")[["patrimonio_comprador", "patrimonio_inquilino"]])
        st.caption("Resto de supuestos tomados de config/defaults.json. Para ajustarlos usa el dashboard "
                   "principal (hl.py app).")

st.caption("Ejercicio educativo. No es asesoría financiera personalizada.")
