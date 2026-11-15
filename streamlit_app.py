"""¿Compro o alquilo? — app pública (Streamlit Community Cloud).

Ejecutar en local:  streamlit run streamlit_app.py

Flujo: el usuario elige distrito y tamaño -> la app toma precios de mercado reales
(data/listings.csv, avisos de Urbania) y tasas en vivo del BCRP -> corre el modelo
financiero -> muestra la recomendación, el patrimonio en el tiempo, un mapa
comparando los 4 distritos y los avisos usados como fuente.
"""
import sys
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / ".claude" / "skills" / "buy-vs-rent" / "scripts"))

from housing_lima import bcrp  # noqa: E402
from housing_lima import listings as lst  # noqa: E402
from housing_lima.analysis import alquiler_equilibrio, sensibilidad  # noqa: E402
from housing_lima.explain import NOMBRES  # noqa: E402
from housing_lima.intake import config, plantilla  # noqa: E402
from housing_lima.model import Perfil, simular  # noqa: E402

LISTINGS = RAIZ / "data" / "listings.csv"
# Centro aproximado de cada distrito (para el mapa).
COORDS = {
    "Miraflores": (-12.1211, -77.0297),
    "Santiago de Surco": (-12.1459, -76.9918),
    "Jesús María": (-12.0769, -77.0470),
    "San Miguel": (-12.0777, -77.0910),
}

st.set_page_config(page_title="¿Compro o alquilo? — Lima", page_icon="🏠", layout="wide")


@st.cache_data(ttl=6 * 3600, show_spinner="Consultando el BCRP…")
def datos_bcrp():
    base = plantilla()
    return bcrp.indicadores({"tipo_cambio": config()["tipo_cambio"],
                             "tea_hipoteca": base["tea_hipoteca"],
                             "rentabilidad_alternativa": base["rentabilidad_alternativa"]})


@st.cache_data
def datos_mercado():
    filas, _ = lst.leer(LISTINGS)
    df = pd.DataFrame(filas)
    df["aviso"] = df["notas"].str.extract(r"aviso: (\S+?);")
    resumen = pd.DataFrame(lst.resumen_por_distrito(filas)).set_index("distrito")
    return df, resumen


def perfil_para(distrito, area, resumen, extra):
    fila = resumen.loc[distrito]
    precio = round(fila["venta_m2_mediana"] * area, -3)
    alquiler = round(fila["alquiler_m2_mediana"] * area, -1)
    return Perfil.desde_dict({**plantilla(), **extra, "distrito": distrito, "area_m2": area,
                              "precio_vivienda": precio, "alquiler_mensual": alquiler,
                              "uit": config()["uit"]})


ind = datos_bcrp()
df, resumen = datos_mercado()
base = plantilla()

# ---------------------------------------------------------------- encabezado
st.title("🏠 ¿Compro o alquilo en Lima?")
st.caption("Te decimos si te conviene comprar o seguir alquilando, con precios reales del mercado "
           "y tasas del BCRP. Gratis, en 1 minuto, sin que un banco ni una inmobiliaria te vendan nada.")

# ---------------------------------------------------------------- entradas
with st.sidebar:
    st.header("1. Tu caso")
    distrito = st.selectbox("Distrito", list(COORDS), index=list(COORDS).index("Santiago de Surco"))
    area = st.slider("Tamaño del departamento (m²)", 40, 200, 90, 5)
    inicial = st.slider("Cuota inicial (% del precio)", 7.5, 50.0, 20.0, 0.5) / 100
    horizonte = st.slider("¿Cuántos años piensas vivir ahí?", 3, 30, 10)
    plazo = st.slider("Plazo del crédito (años)", 5, 30, 20)

    st.header("2. Supuestos")
    tea = st.slider("TEA hipotecaria (%)", 5.0, 15.0, round(ind["tea_hipoteca"]["valor"] * 100, 2), 0.05) / 100
    rent = st.slider("Rentabilidad de tu ahorro si no compras (%)", 0.0, 12.0,
                     round(ind["rentabilidad_alternativa"]["valor"] * 100, 2), 0.05) / 100
    with st.expander("Más supuestos"):
        aprec = st.slider("Apreciación anual de la vivienda (%)", -2.0, 10.0, base["apreciacion_anual"] * 100, 0.5) / 100
        crec = st.slider("Crecimiento anual del alquiler (%)", 0.0, 10.0, base["crecimiento_alquiler"] * 100, 0.5) / 100
        alcabala = st.checkbox("Vivienda usada (paga alcabala)", base["aplica_alcabala"])
        bono = st.number_input("Bono MiVivienda / Buen Pagador (S/)", 0, 100_000, 0, 1_000)

extra = {"cuota_inicial_pct": inicial, "horizonte_anios": horizonte, "plazo_anios": plazo,
         "tea_hipoteca": tea, "rentabilidad_alternativa": rent, "apreciacion_anual": aprec,
         "crecimiento_alquiler": crec, "aplica_alcabala": alcabala, "bono": bono}
p = perfil_para(distrito, area, resumen, extra)

with st.sidebar:
    st.header("3. Precio y alquiler")
    st.caption(f"Calculados con la mediana de {int(resumen.loc[distrito, 'n_venta'])} avisos de venta y "
               f"{int(resumen.loc[distrito, 'n_alquiler'])} de alquiler en {distrito}. Puedes ajustarlos.")
    precio = st.number_input("Precio del depa (S/)", 50_000, 10_000_000, int(p.precio_vivienda), 5_000)
    alquiler = st.number_input("Alquiler mensual de un depa similar (S/)", 300, 50_000, int(p.alquiler_mensual), 50)
p = p.con(precio_vivienda=precio, alquiler_mensual=alquiler)

r = simular(p)
eq = alquiler_equilibrio(p)

# ---------------------------------------------------------------- resultado
comprar = r["recomendacion"] == "comprar"
mensaje = (f"**Te conviene COMPRAR.** En {horizonte} años terminarías con "
           f"S/ {abs(r['ventaja_comprar']):,.0f} más de patrimonio que alquilando.") if comprar else (
           f"**Te conviene ALQUILAR e invertir la diferencia.** En {horizonte} años terminarías con "
           f"S/ {abs(r['ventaja_comprar']):,.0f} más de patrimonio que comprando.")
(st.success if comprar else st.info)(mensaje)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cuota del crédito", f"S/ {r['cuota_mensual']:,.0f}/mes")
c2.metric("Alquiler actual", f"S/ {p.alquiler_mensual:,.0f}/mes")
c3.metric("Alquiler de equilibrio", f"S/ {eq:,.0f}" if eq else "—",
          help="Si el alquiler fuera mayor a este monto, comprar pasaría a convenir.")
c4.metric("Años de alquiler para pagar el depa (PER)", f"{r['per']:.1f}",
          help="Precio / alquiler anual. Más de ~20 suele favorecer alquilar; menos de ~15, comprar.")

st.caption(f"Cuota inicial S/ {r['cuota_inicial']:,.0f} · gastos de cierre S/ {r['gastos_cierre']:,.0f} "
           f"(alcabala S/ {r['alcabala']:,.0f}) · año de equilibrio: "
           f"{r['anio_equilibrio'] or 'no se alcanza en tu horizonte'}")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Patrimonio", "🗺️ Mapa de distritos", "🔎 Qué pesa más", "📋 Avisos y fuentes"])

with tab1:
    serie = pd.DataFrame(r["serie"]).set_index("anio")[["patrimonio_comprador", "patrimonio_inquilino"]]
    serie.columns = ["Si compras", "Si alquilas e inviertes"]
    st.line_chart(serie, y_label="Patrimonio (S/)", x_label="Año")

with tab2:
    st.caption(f"Mismo caso ({area} m², {inicial:.0%} de inicial, {horizonte} años) en los 4 distritos. "
               "Verde = conviene comprar, azul = conviene alquilar. El tamaño del círculo es el precio por m².")
    mapa = folium.Map(location=(-12.105, -77.035), zoom_start=12)
    filas_mapa = []
    for d, (lat, lon) in COORDS.items():
        pd_ = perfil_para(d, area, resumen, extra)
        rd = simular(pd_)
        fila = resumen.loc[d]
        color = "#1a9850" if rd["recomendacion"] == "comprar" else "#2c7bb6"
        popup = (f"<b>{d}</b><br>Venta: S/ {fila['venta_m2_mediana']:,.0f}/m²<br>"
                 f"Alquiler: S/ {fila['alquiler_m2_mediana']:,.1f}/m² al mes<br>"
                 f"PER: {1 / fila['rendimiento_bruto']:.1f} años<br>"
                 f"<b>{rd['recomendacion'].upper()}</b> (S/ {rd['ventaja_comprar']:,.0f})")
        folium.CircleMarker((lat, lon), radius=fila["venta_m2_mediana"] / 300, color=color, fill=True,
                            fill_opacity=0.6, weight=3 if d == distrito else 1,
                            popup=folium.Popup(popup, max_width=250), tooltip=d).add_to(mapa)
        filas_mapa.append({"Distrito": d, "Precio venta S/ por m²": round(fila["venta_m2_mediana"]),
                           "Alquiler S/ por m² al mes": round(fila["alquiler_m2_mediana"], 1),
                           "PER (años)": round(1 / fila["rendimiento_bruto"], 1),
                           "Recomendación": rd["recomendacion"].upper(),
                           "Ventaja de comprar (S/)": round(rd["ventaja_comprar"])})
    col_m, col_t = st.columns([3, 2])
    with col_m:
        st_folium(mapa, height=420, use_container_width=True, returned_objects=[])
    with col_t:
        st.dataframe(pd.DataFrame(filas_mapa).set_index("Distrito"), width="stretch")

with tab3:
    st.caption("Cuánto cambia la ventaja de comprar si cada supuesto sube o baja (análisis de sensibilidad).")
    t = pd.DataFrame(sensibilidad(p)["tornado"])
    t["variable"] = t["variable"].map(lambda v: NOMBRES.get(v, v))
    t = t.set_index("variable")[["ventaja_si_baja", "ventaja_si_sube"]]
    t.columns = ["Si baja", "Si sube"]
    st.bar_chart(t, horizontal=True)

with tab4:
    st.caption(f"Avisos de Urbania consultados el 15/11/2026 en {distrito}. Precios en soles; m² totales.")
    ver = df[df["distrito"] == distrito][["operacion", "precio_pen", "area_m2", "dormitorios", "precio_m2", "aviso"]]
    st.dataframe(ver.rename(columns={"operacion": "Operación", "precio_pen": "Precio (S/)", "area_m2": "m²",
                                     "dormitorios": "Dorm.", "precio_m2": "S/ por m²", "aviso": "Aviso"}),
                 column_config={"Aviso": st.column_config.LinkColumn(display_text="ver aviso"),
                                "Precio (S/)": st.column_config.NumberColumn(format="%,.0f"),
                                "S/ por m²": st.column_config.NumberColumn(format="%,.0f")},
                 hide_index=True, width="stretch")
    st.markdown("**Datos del BCRP (API en vivo)**")
    for v in ind.values():
        valor = f"{v['valor']:.3f}" if v["nombre"].startswith("Tipo") else f"{v['valor'] * 100:.2f} %"
        estado = "en vivo" if v["en_vivo"] else "valor por defecto, el API no respondió"
        st.markdown(f"- {v['nombre']}: **{valor}** ({v['periodo']}, {estado}) — [fuente]({v['url']})")

st.divider()
st.caption("Herramienta educativa con supuestos simplificados. No es asesoría financiera personalizada.")
