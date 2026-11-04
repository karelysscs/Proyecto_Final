"""Dashboard Streamlit: comprar vs alquilar en Lima.

Ejecutar: python .claude/skills/buy-vs-rent/scripts/hl.py app
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from housing_lima import listings as lst  # noqa: E402
from housing_lima.analysis import alquiler_equilibrio, escenarios, sensibilidad  # noqa: E402
from housing_lima.intake import config, plantilla  # noqa: E402
from housing_lima.model import Perfil, simular  # noqa: E402

st.set_page_config(page_title="¿Comprar o alquilar? — Lima", layout="wide")
st.title("¿Comprar o alquilar en Lima?")

base = plantilla()
cfg = config()
with st.sidebar:
    st.header("Tu caso")
    distrito = st.text_input("Distrito", base["distrito"])
    precio = st.number_input("Precio de la vivienda (S/)", 50_000, 5_000_000, int(base["precio_vivienda"]), 10_000)
    alquiler = st.number_input("Alquiler mensual equivalente (S/)", 300, 30_000, int(base["alquiler_mensual"]), 50)
    inicial = st.slider("Cuota inicial", 0.075, 0.5, base["cuota_inicial_pct"], 0.005, format="%.3f")
    tea = st.slider("TEA hipotecaria", 0.05, 0.15, base["tea_hipoteca"], 0.001, format="%.3f")
    plazo = st.slider("Plazo del crédito (años)", 5, 30, base["plazo_anios"])
    horizonte = st.slider("Horizonte de análisis (años)", 1, 30, base["horizonte_anios"])
    aprec = st.slider("Apreciación anual", -0.02, 0.10, base["apreciacion_anual"], 0.005, format="%.3f")
    crec = st.slider("Crecimiento del alquiler", 0.0, 0.10, base["crecimiento_alquiler"], 0.005, format="%.3f")
    rent = st.slider("Rentabilidad alternativa", 0.0, 0.12, base["rentabilidad_alternativa"], 0.005, format="%.3f")
    alcabala = st.checkbox("Aplica alcabala (vivienda usada)", base["aplica_alcabala"])
    bono = st.number_input("Bono (MiVivienda / Buen Pagador) S/", 0, 100_000, int(base["bono"]), 1_000)

p = Perfil.desde_dict({**base, "distrito": distrito, "precio_vivienda": precio, "alquiler_mensual": alquiler,
                       "cuota_inicial_pct": inicial, "tea_hipoteca": tea, "plazo_anios": plazo,
                       "horizonte_anios": horizonte, "apreciacion_anual": aprec, "crecimiento_alquiler": crec,
                       "rentabilidad_alternativa": rent, "aplica_alcabala": alcabala, "bono": bono,
                       "uit": cfg["uit"]})
r = simular(p)
eq = alquiler_equilibrio(p)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Recomendación", r["recomendacion"].upper())
c2.metric("Ventaja de comprar", f"S/ {r['ventaja_comprar']:,.0f}")
c3.metric("Cuota del crédito", f"S/ {r['cuota_mensual']:,.0f}")
c4.metric("Alquiler de equilibrio", f"S/ {eq:,.0f}" if eq else "—")

serie = pd.DataFrame(r["serie"]).set_index("anio")
st.subheader("Patrimonio acumulado")
st.line_chart(serie[["patrimonio_comprador", "patrimonio_inquilino"]])

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Sensibilidad (tornado)")
    t = pd.DataFrame(sensibilidad(p)["tornado"]).set_index("variable")
    st.bar_chart(t[["ventaja_si_baja", "ventaja_si_sube"]], horizontal=True)
with col_b:
    st.subheader("Escenarios: apreciación × rentabilidad")
    e = escenarios(p)
    m = pd.DataFrame(e["ventaja"],
                     index=[f"aprec {a:.0%}" for a in e["apreciaciones"]],
                     columns=[f"rent {x:.0%}" for x in e["rentabilidades"]])
    st.dataframe(m.style.format("S/ {:,.0f}").background_gradient(cmap="RdYlGn", axis=None))

st.subheader("Datos de mercado")
archivo = st.file_uploader("Sube listings.csv (generado por el agente market-data)", type="csv")
if archivo:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(archivo.getvalue())
    filas, errores = lst.leer(tmp.name)
    ctrl = lst.control_fuentes(filas)
    st.caption(f"Fuentes usadas: {ctrl['fuentes_usadas']} de {ctrl['max_fuentes']} permitidas")
    for err in errores:
        st.warning(err)
    st.dataframe(pd.DataFrame(lst.resumen_por_distrito(filas)))

st.caption("Ejercicio educativo. No es asesoría financiera personalizada.")
