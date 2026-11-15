"""Techito Propio: ¿compro o alquilo en Lima? (app pública en Streamlit Community Cloud).

Ejecutar en local:  streamlit run streamlit_app.py

Recorrido guiado en 3 pasos:
  1. ¿Dónde quieres vivir?  -> mapa Folium de 4 distritos con precios reales (Urbania).
  2. Elige tu depa          -> avisos reales en venta vs. el alquiler de uno parecido.
  3. Tu asesora hipotecaria -> veredicto conversacional + preguntas que recalculan el
                               modelo en vivo con tasas del API del BCRP.
"""
import sys
import time
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
DISTRITOS = {
    "Miraflores": {"coord": (-12.1211, -77.0297), "emoji": "🌊", "frase": "Malecón, vida de barrio y oficinas cerca"},
    "Santiago de Surco": {"coord": (-12.1459, -76.9918), "emoji": "🌳", "frase": "Residencial, parques y colegios"},
    "Jesús María": {"coord": (-12.0769, -77.0470), "emoji": "🏛️", "frase": "Céntrico, Campo de Marte y buena conexión"},
    "San Miguel": {"coord": (-12.0777, -77.0910), "emoji": "🛍️", "frase": "Familiar, cerca al mar y a centros comerciales"},
}
ASESORA = "🧑‍💼"

st.set_page_config(page_title="Techito Propio · ¿Compro o alquilo?", page_icon=str(RAIZ / "assets" / "icono.svg"), layout="wide")


# ------------------------------------------------------------------ datos
@st.cache_data(ttl=6 * 3600, show_spinner="Consultando tasas en el BCRP…")
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


ind = datos_bcrp()
df, resumen = datos_mercado()
base = plantilla()
TEA_BCRP = ind["tea_hipoteca"]["valor"]
RENT_BCRP = ind["rentabilidad_alternativa"]["valor"]

ss = st.session_state
ss.setdefault("paso", 1)
ss.setdefault("distrito", None)
ss.setdefault("aviso_id", None)
ss.setdefault("chat", [])


def ir(paso):
    ss.paso = paso
    if paso < 3:
        ss.chat = []


def perfil(**cambios):
    datos = {**base, "uit": config()["uit"], "distrito": ss.distrito, "precio_vivienda": ss.precio,
             "alquiler_mensual": ss.alquiler, "area_m2": ss.area, "cuota_inicial_pct": ss.inicial,
             "horizonte_anios": ss.horizonte, "plazo_anios": ss.plazo, "tea_hipoteca": ss.tea,
             "rentabilidad_alternativa": RENT_BCRP, "aplica_alcabala": True}
    datos.update(cambios)
    return Perfil.desde_dict(datos)


def soles(x):
    return f"S/ {x:,.0f}"


def escribir(texto):
    """Efecto de 'escribiendo…' para los mensajes nuevos de la asesora."""
    for palabra in texto.split(" "):
        time.sleep(0.02)
        yield palabra + " "


# ------------------------------------------------------------------ marca
TEJA, AMBAR, CREMA, TINTA, SALVIA = "#D9583B", "#F2A541", "#FFF9F2", "#2E2A3A", "#5B8E7D"
ASSETS = RAIZ / "assets"
st.logo(str(ASSETS / "logo.svg"), size="large", icon_image=str(ASSETS / "icono.svg"))
st.markdown(f"""
<style>
  .block-container {{ padding-top: 2.2rem; }}
  h1, h2, h3 {{ color: {TINTA}; }}
  .tp-hero h1 {{ font-size: 2.6rem; line-height: 1.1; margin: 0 0 .4rem 0; }}
  .tp-hero h1 span {{ color: {TEJA}; }}
  .tp-hero p {{ font-size: 1.08rem; color: #5a5368; margin: 0 0 .8rem 0; }}
  .tp-chip {{ display: inline-block; background: #FCEBDD; color: {TEJA}; border: 1px solid #F1D2BD;
             border-radius: 999px; padding: .2rem .7rem; margin: 0 .3rem .3rem 0; font-size: .85rem; font-weight: 600; }}
  .tp-pasos {{ display: flex; gap: .5rem; margin: .6rem 0 1.2rem 0; }}
  .tp-paso {{ flex: 1; text-align: center; padding: .55rem; border-radius: 12px; font-weight: 600;
             background: #FCEBDD; color: #9a8f86; border: 1px solid #F1D2BD; }}
  .tp-paso.activo {{ background: {TEJA}; color: {CREMA}; border-color: {TEJA}; }}
  .tp-paso.hecho {{ background: #F7D9C9; color: {TEJA}; }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px; background: #FFFDF9; }}
  .stButton button, .stLinkButton a {{ border-radius: 999px; font-weight: 600; }}
  div[data-testid="stMetricValue"] {{ color: {TEJA}; }}
</style>
""", unsafe_allow_html=True)

if ss.paso == 1:
    h_txt, h_img = st.columns([3, 2], gap="large", vertical_alignment="center")
    with h_txt:
        st.markdown("""
<div class="tp-hero">
  <h1>¿Compro o alquilo?<br><span>Te lo decimos con números.</span></h1>
  <p>Tu asesora para decidir si comprar o seguir alquilando en Lima: avisos reales,
  tasas en vivo del BCRP y un modelo financiero completo. Gratis y sin que nadie te quiera vender nada.</p>
  <span class="tp-chip">🏘️ 96 avisos reales</span><span class="tp-chip">🏦 Tasas BCRP en vivo</span>
  <span class="tp-chip">🗺️ 4 distritos</span><span class="tp-chip">⏱️ 1 minuto</span>
</div>""", unsafe_allow_html=True)
    with h_img:
        st.image(str(ASSETS / "hero.svg"), use_container_width=True)

pasos = ["① Dónde vivir", "② Tu depa", "③ Tu asesora"]
st.markdown('<div class="tp-pasos">' + "".join(
    f'<div class="tp-paso {"activo" if i + 1 == ss.paso else "hecho" if i + 1 < ss.paso else ""}">{p}</div>'
    for i, p in enumerate(pasos)) + "</div>", unsafe_allow_html=True)

# ================================================================== PASO 1
if ss.paso == 1:
    st.subheader("¿Dónde te gustaría vivir?")
    st.write("Toca un distrito en el mapa o elige una tarjeta. Los precios salen de avisos reales publicados hoy.")
    col_mapa, col_cards = st.columns([3, 2], gap="large")
    with col_mapa:
        mapa = folium.Map(location=(-12.108, -77.035), zoom_start=12)
        for d, info in DISTRITOS.items():
            fila = resumen.loc[d]
            elegido = d == ss.distrito
            folium.CircleMarker(
                info["coord"], radius=fila["venta_m2_mediana"] / 250,
                color=TEJA if elegido else SALVIA, fill=True, fill_color=TEJA if elegido else AMBAR,
                fill_opacity=0.6,
                weight=4 if elegido else 2, tooltip=d,
                popup=folium.Popup(f"<b>{d}</b><br>Venta: S/ {fila['venta_m2_mediana']:,.0f}/m²<br>"
                                   f"Alquiler: S/ {fila['alquiler_m2_mediana']:,.0f}/m² al mes", max_width=220),
            ).add_to(mapa)
        salida = st_folium(mapa, height=460, use_container_width=True,
                           returned_objects=["last_object_clicked_tooltip"], key="mapa_distritos")
        clic = (salida or {}).get("last_object_clicked_tooltip")
        if clic in DISTRITOS and clic != ss.distrito:
            ss.distrito = clic
            ss.aviso_id = None
            st.rerun()
    with col_cards:
        for d, info in DISTRITOS.items():
            fila = resumen.loc[d]
            with st.container(border=True):
                st.markdown(f"**{info['emoji']} {d}**" + ("  ✅" if d == ss.distrito else ""))
                st.caption(info["frase"])
                a, b, c = st.columns([2, 2, 1.4])
                a.markdown(f"Venta  \n**{soles(fila['venta_m2_mediana'])}/m²**")
                b.markdown(f"Alquiler  \n**{soles(fila['alquiler_m2_mediana'] * 90)}/mes**")
                if c.button("Elegir", key=f"btn_{d}", type="primary" if d == ss.distrito else "secondary"):
                    ss.distrito = d
                    ss.aviso_id = None
                    st.rerun()
        st.caption("Alquiler referencial de un depa de 90 m².")
    if ss.distrito:
        st.button(f"Continuar con {ss.distrito} →", type="primary", on_click=ir, args=(2,))

# ================================================================== PASO 2
elif ss.paso == 2:
    d = ss.distrito
    fila = resumen.loc[d]
    st.subheader(f"{DISTRITOS[d]['emoji']} Elige el depa que te gustaría comprar en {d}")
    st.write("Estos son avisos reales en venta. Elige uno y lo comparamos con lo que pagarías por alquilar uno parecido.")

    ventas = df[(df["distrito"] == d) & (df["operacion"] == "venta")].sort_values("precio_pen").reset_index(drop=True)
    if ss.aviso_id is None:
        ss.aviso_id = ventas.loc[(ventas["area_m2"] - 90).abs().idxmin(), "id"]  # el más cercano a 90 m²
    cols = st.columns(4)
    for i, v in ventas.iterrows():
        with cols[i % 4].container(border=True):
            elegido = v["id"] == ss.aviso_id
            st.markdown(f"**{soles(v['precio_pen'])}**" + ("  ✅" if elegido else ""))
            st.caption(f"{v['area_m2']:.0f} m² · {v['dormitorios']} dorm. · {v['banos']} baños · "
                       f"{soles(v['precio_m2'])}/m²")
            b1, b2 = st.columns(2)
            if b1.button("Elegir", key=f"av_{v['id']}", type="primary" if elegido else "secondary"):
                ss.aviso_id = v["id"]
                st.rerun()
            b2.link_button("Ver", v["aviso"])

    casa = ventas[ventas["id"] == ss.aviso_id].iloc[0]
    area = float(casa["area_m2"])
    alq_estimado = round(fila["alquiler_m2_mediana"] * area, -1)

    st.divider()
    izq, der = st.columns(2, gap="large")
    with izq:
        st.markdown("### 🏠 Comprar")
        st.metric("Precio del depa elegido", soles(casa["precio_pen"]), f"{area:.0f} m² · {casa['dormitorios']} dorm.",
                  delta_color="off")
        inicial = st.slider("¿Cuánto tienes de cuota inicial?", 7.5, 50.0, 20.0, 0.5, format="%.1f %%") / 100
        st.caption(f"Equivale a {soles(casa['precio_pen'] * inicial)}")
        plazo = st.select_slider("Plazo del crédito", options=[10, 15, 20, 25, 30], value=20,
                                 format_func=lambda x: f"{x} años")
        tea = st.slider("Tasa del crédito (TEA)", 5.0, 15.0, round(TEA_BCRP * 100, 2), 0.05, format="%.2f %%",
                        help=f"Por defecto, el promedio de la banca según el BCRP ({ind['tea_hipoteca']['periodo']}).") / 100
    with der:
        st.markdown("### 🔑 Alquilar")
        st.metric("Alquiler de un depa parecido", soles(alq_estimado) + "/mes",
                  f"mediana de {int(fila['n_alquiler'])} avisos en {d}", delta_color="off")
        ya_alquilo = st.toggle("Ya alquilo y quiero poner lo que pago")
        alquiler = st.number_input("Alquiler mensual (S/)", 300, 50_000, int(alq_estimado), 50) if ya_alquilo else alq_estimado
        horizonte = st.slider("¿Cuántos años piensas vivir ahí?", 3, 30, 10)
        st.caption(f"Si no compras, tu inicial se invierte en un depósito a plazo al "
                   f"{RENT_BCRP * 100:.2f} % anual (BCRP).")

    ss.update({"precio": float(casa["precio_pen"]), "area": area, "alquiler": float(alquiler),
               "inicial": inicial, "plazo": plazo, "tea": tea, "horizonte": horizonte,
               "casa_url": casa["aviso"]})
    n1, n2 = st.columns([1, 5])
    n1.button("← Cambiar distrito", on_click=ir, args=(1,))
    n2.button("Hablar con mi asesora →", type="primary", on_click=ir, args=(3,))

# ================================================================== PASO 3
else:
    p = perfil()
    r = simular(p)
    eq = alquiler_equilibrio(p)
    comprar = r["recomendacion"] == "comprar"

    def anios_para_comprar():
        for h in range(1, 31):
            if simular(perfil(horizonte_anios=h))["recomendacion"] == "comprar":
                return h
        return None

    def respuesta(pregunta):
        if pregunta == "inicial":
            nueva = min(ss.inicial + 0.10, 0.5)
            rr = simular(perfil(cuota_inicial_pct=nueva))
            return (f"Si das **{nueva:.0%}** de inicial ({soles(ss.precio * nueva)}), tu cuota baja a "
                    f"**{soles(rr['cuota_mensual'])}** y la ventaja de comprar pasa a **{soles(rr['ventaja_comprar'])}** "
                    f"(hoy es {soles(r['ventaja_comprar'])}). "
                    + ("Ojo: esa plata también podría rendir en un depósito, por eso no siempre ayuda tanto."))
        if pregunta == "tasa":
            rr = simular(perfil(tea_hipoteca=ss.tea + 0.01))
            return (f"Si el banco te cobra **{(ss.tea + 0.01) * 100:.2f} %** en vez de {ss.tea * 100:.2f} %, tu cuota sube a "
                    f"**{soles(rr['cuota_mensual'])}** y la ventaja de comprar queda en **{soles(rr['ventaja_comprar'])}**. "
                    f"Por eso vale la pena negociar la tasa con 2 o 3 bancos.")
        if pregunta == "anios":
            h = anios_para_comprar()
            if h is None:
                return "Con estos números, comprar **no llega a convenir ni en 30 años**. El alquiler aquí está barato frente al precio."
            return (f"Comprar empieza a convenir si te quedas **{h} años o más**. Antes de eso, los costos de entrar "
                    f"y salir (alcabala, cierre, comisión de venta) pesan más que lo que ganas.")
        if pregunta == "precio":
            rr = simular(perfil(apreciacion_anual=0.0))
            return (f"Si el depa **no sube de precio** en {ss.horizonte} años, la ventaja de comprar sería "
                    f"**{soles(rr['ventaja_comprar'])}** → conviene **{rr['recomendacion'].upper()}**. "
                    f"Asumí que sube {base['apreciacion_anual']:.0%} al año, como la inflación más un poco.")
        if pregunta == "equilibrio":
            return (f"Comprar conviene si alquilar un depa así cuesta más de **{soles(eq)}/mes**. "
                    f"Hoy cuesta {soles(ss.alquiler)}." if eq else "No encontré un alquiler de equilibrio en un rango razonable.")
        return ""

    if not ss.chat:
        motivo = sensibilidad(p)["tornado"][0]
        ss.chat = [
            f"¡Hola! Soy **Techi**, tu asesora hipotecaria. Revisé el depa de **{soles(ss.precio)}** "
            f"en **{ss.distrito}** ({ss.area:.0f} m²) frente a alquilar uno parecido por **{soles(ss.alquiler)}/mes**.",
            (f"✅ **Mi recomendación: COMPRAR.** En {ss.horizonte} años terminarías con **{soles(r['ventaja_comprar'])} "
             f"más** de patrimonio que alquilando.") if comprar else
            (f"🔑 **Mi recomendación: ALQUILAR e invertir la diferencia.** En {ss.horizonte} años terminarías con "
             f"**{soles(-r['ventaja_comprar'])} más** que comprando."),
            f"Tu cuota sería **{soles(r['cuota_mensual'])}/mes** con una inicial de {soles(r['cuota_inicial'])}, "
            f"más {soles(r['gastos_cierre'])} de gastos de cierre (incluye {soles(r['alcabala'])} de alcabala). "
            f"Lo que más mueve esta decisión es la **{NOMBRES.get(motivo['variable'], motivo['variable'])}**.",
        ]
        ss.animar = len(ss.chat)

    st.subheader(f"{ASESORA} Tu asesora hipotecaria")
    chat_col, graf_col = st.columns([3, 2], gap="large")
    with chat_col:
        animar = ss.pop("animar", 0)
        for i, msg in enumerate(ss.chat):
            rol, texto = ("user", msg[4:]) if msg.startswith("YO::") else ("assistant", msg)
            with st.chat_message(rol, avatar="🙋" if rol == "user" else ASESORA):
                if rol == "assistant" and i >= len(ss.chat) - animar:
                    st.write_stream(escribir(texto))
                else:
                    st.markdown(texto)
        st.caption("Pregúntale a Techi:")
        preguntas = {"💰 ¿Y si doy más inicial?": "inicial", "📈 ¿Y si sube la tasa 1 punto?": "tasa",
                     "⏳ ¿Cuántos años debo quedarme?": "anios", "🏚️ ¿Y si el depa no sube de precio?": "precio",
                     "⚖️ ¿Qué alquiler haría que comprar convenga?": "equilibrio"}
        bcols = st.columns(len(preguntas))
        for (texto, clave), col in zip(preguntas.items(), bcols):
            if col.button(texto, key=f"q_{clave}", use_container_width=True):
                ss.chat += ["YO::" + texto, respuesta(clave)]
                ss.animar = 1
                st.rerun()
    with graf_col:
        a, b = st.columns(2)
        a.metric("Cuota del crédito", soles(r["cuota_mensual"]) + "/mes")
        b.metric("Alquiler", soles(ss.alquiler) + "/mes")
        serie = pd.DataFrame(r["serie"]).set_index("anio")[["patrimonio_comprador", "patrimonio_inquilino"]]
        serie.columns = ["Si compras", "Si alquilas e inviertes"]
        st.markdown("**Tu patrimonio año a año**")
        st.line_chart(serie, y_label="S/", x_label="Año", height=280)
        st.link_button("Ver el aviso del depa elegido ↗", ss.casa_url)

    with st.expander("📋 Fuentes de los datos"):
        st.markdown(f"- Precios: {int(resumen.loc[ss.distrito, 'n_venta'])} avisos de venta y "
                    f"{int(resumen.loc[ss.distrito, 'n_alquiler'])} de alquiler en Urbania ({ss.distrito}, 15/11/2026).")
        for v in ind.values():
            valor = f"{v['valor']:.3f}" if v["nombre"].startswith("Tipo") else f"{v['valor'] * 100:.2f} %"
            estado = "en vivo" if v["en_vivo"] else "valor por defecto, el API no respondió"
            st.markdown(f"- {v['nombre']}: **{valor}** ({v['periodo']}, {estado}) · [BCRP]({v['url']})")

    n1, n2, _ = st.columns([1, 1, 4])
    n1.button("← Cambiar depa", on_click=ir, args=(2,))
    n2.button("Empezar de nuevo", on_click=lambda: ss.update(paso=1, distrito=None, aviso_id=None, chat=[]))

st.divider()
st.caption("Techito Propio · herramienta educativa con supuestos simplificados; no es asesoría financiera personalizada.")
