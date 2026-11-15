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
  .tp-badge {{ display: inline-block; border-radius: 999px; padding: .15rem .65rem; font-size: .8rem; font-weight: 700; }}
  .tp-badge.comprar {{ background: #DCEBE4; color: #2F6B57; }}
  .tp-badge.alquilar {{ background: #FDE9C8; color: #9A5B00; }}
  .tp-mini {{ font-size: .9rem; color: #5a5368; margin: .2rem 0 .5rem 0; }}
  .tp-mini b {{ color: {TINTA}; }}
  .tp-confianza {{ display: flex; gap: 1rem; flex-wrap: wrap; background: #FCEBDD; border-radius: 14px;
                  padding: .8rem 1.1rem; margin-top: 1.2rem; font-size: .9rem; color: #5a5368; }}
  .tp-confianza div {{ flex: 1; min-width: 220px; }}
  .tp-confianza b {{ color: {TINTA}; }}
</style>
""", unsafe_allow_html=True)

if ss.paso == 1:
    h_txt, h_img = st.columns([4, 1], gap="medium", vertical_alignment="center")
    with h_txt:
        st.markdown("""
<div class="tp-hero">
  <h1 style="font-size:2.1rem">¿Compro o alquilo? <span>Te lo decimos con números.</span></h1>
  <p>Avisos reales, tasas en vivo del BCRP y un modelo financiero completo. Gratis, en 1 minuto
  y sin que nadie te quiera vender nada.</p>
  <span class="tp-chip">🏘️ 96 avisos reales</span><span class="tp-chip">🏦 Tasas BCRP en vivo</span>
  <span class="tp-chip">🔓 Cálculo abierto</span>
</div>""", unsafe_allow_html=True)
    with h_img:
        st.image(str(ASSETS / "hero.svg"), width=230)

pasos = ["① Dónde vivir", "② Tu depa", "③ Tu asesora"]
st.markdown('<div class="tp-pasos">' + "".join(
    f'<div class="tp-paso {"activo" if i + 1 == ss.paso else "hecho" if i + 1 < ss.paso else ""}">{p}</div>'
    for i, p in enumerate(pasos)) + "</div>", unsafe_allow_html=True)

# ================================================================== PASO 1
def elegir_distrito(d):
    ss.distrito = d
    ss.aviso_id = None
    ir(2)


@st.cache_data
def adelanto(d, tea, rent):
    """Veredicto de referencia por distrito: depa de 90 m², 20 % de inicial, 10 años."""
    fila = resumen.loc[d]
    pr = Perfil.desde_dict({**base, "uit": config()["uit"], "area_m2": 90, "tea_hipoteca": tea,
                            "rentabilidad_alternativa": rent,
                            "precio_vivienda": round(fila["venta_m2_mediana"] * 90, -3),
                            "alquiler_mensual": round(fila["alquiler_m2_mediana"] * 90, -1)})
    return pr.precio_vivienda, pr.alquiler_mensual, simular(pr)["recomendacion"]


if ss.paso == 1:
    st.markdown("#### ¿Dónde te gustaría vivir?  \n"
                "<span class='tp-mini'>Toca un círculo del mapa o una tarjeta y pasamos al siguiente paso.</span>",
                unsafe_allow_html=True)
    col_mapa, col_cards = st.columns([5, 6], gap="medium")
    with col_mapa:
        mapa = folium.Map(location=(-12.105, -77.04), zoom_start=12, scrollWheelZoom=False)
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
        salida = st_folium(mapa, height=440, use_container_width=True,
                           returned_objects=["last_object_clicked_tooltip"], key="mapa_distritos")
        clic = (salida or {}).get("last_object_clicked_tooltip")
        if clic in DISTRITOS and clic != ss.get("clic_previo"):  # evita re-disparar al volver al paso 1
            ss.clic_previo = clic
            elegir_distrito(clic)
            st.rerun()
    with col_cards:
        cuadros = st.columns(2)
        for i, (d, info) in enumerate(DISTRITOS.items()):
            precio90, alq90, veredicto = adelanto(d, TEA_BCRP, RENT_BCRP)
            with cuadros[i % 2].container(border=True):
                st.markdown(f"**{info['emoji']} {d}**  \n<span class='tp-mini'>{info['frase']}</span>",
                            unsafe_allow_html=True)
                st.markdown(f"<div class='tp-mini'>Depa de 90 m²<br>Comprar <b>{soles(precio90)}</b><br>"
                            f"Alquilar <b>{soles(alq90)}/mes</b></div>"
                            f"<span class='tp-badge {veredicto}'>"
                            f"{'✅ suele convenir COMPRAR' if veredicto == 'comprar' else '🔑 suele convenir ALQUILAR'}</span>",
                            unsafe_allow_html=True)
                corto = {"Santiago de Surco": "Surco"}.get(d, d)
                st.button(f"Ver depas en {corto} →", key=f"btn_{d}", type="primary",
                          use_container_width=True, on_click=elegir_distrito, args=(d,))
        st.caption("Referencia con 20 % de inicial, 10 años y la tasa promedio del BCRP. "
                   "En el siguiente paso lo ajustas a tu caso.")

# ================================================================== PASO 2
elif ss.paso == 2:
    d = ss.distrito
    fila = resumen.loc[d]
    st.markdown(f"#### {DISTRITOS[d]['emoji']} ¿Qué depa te gustaría en {d}?  \n"
                "<span class='tp-mini'>Avisos reales en venta. Elige uno y a la derecha lo comparamos con alquilar uno parecido.</span>",
                unsafe_allow_html=True)

    ventas = df[(df["distrito"] == d) & (df["operacion"] == "venta")].sort_values("precio_pen").reset_index(drop=True)
    if ss.aviso_id is None:
        ss.aviso_id = ventas.loc[(ventas["area_m2"] - 90).abs().idxmin(), "id"]  # el más cercano a 90 m²

    lista, panel = st.columns([6, 5], gap="large")
    with lista:
        with st.container(height=520, border=False):
            cols = st.columns(2)
            for i, v in ventas.iterrows():
                elegido = v["id"] == ss.aviso_id
                with cols[i % 2].container(border=True):
                    st.markdown(f"**{soles(v['precio_pen'])}**" + ("  ✅" if elegido else "") +
                                f"  \n<span class='tp-mini'>{v['area_m2']:.0f} m² · {v['dormitorios']} dorm. · "
                                f"{v['banos']} baños · {soles(v['precio_m2'])}/m²</span>", unsafe_allow_html=True)
                    b1, b2 = st.columns([3, 2])
                    b1.button("Este me gusta" if not elegido else "Elegido", key=f"av_{v['id']}",
                              type="primary" if elegido else "secondary", use_container_width=True,
                              on_click=lambda i=v["id"]: ss.update(aviso_id=i))
                    b2.link_button("Ver ↗", v["aviso"], use_container_width=True)

    casa = ventas[ventas["id"] == ss.aviso_id].iloc[0]
    area = float(casa["area_m2"])
    alq_estimado = round(fila["alquiler_m2_mediana"] * area, -1)

    with panel, st.container(border=True):
        st.markdown(f"**Tu elección:** {area:.0f} m² · {casa['dormitorios']} dorm. en {d}")
        c_comp, c_alq = st.columns(2)
        c_comp.metric("🏠 Comprarlo", soles(casa["precio_pen"]))
        with c_alq:
            ya_alquilo = st.toggle("Ya alquilo", help="Pon lo que pagas hoy en vez del estimado.")
            if ya_alquilo:
                alquiler = st.number_input("Tu alquiler (S/ al mes)", 300, 50_000, int(alq_estimado), 50)
            else:
                alquiler = alq_estimado
                st.metric("🔑 Alquilar uno parecido", soles(alq_estimado) + "/mes",
                          f"mediana de {int(fila['n_alquiler'])} avisos", delta_color="off")
        inicial = st.slider("Tu cuota inicial", 7.5, 50.0, 20.0, 0.5, format="%.1f %%") / 100
        st.caption(f"= {soles(casa['precio_pen'] * inicial)}. Si no compras, esa plata rinde "
                   f"{RENT_BCRP * 100:.2f} % al año en un depósito a plazo (BCRP).")
        horizonte = st.slider("¿Cuántos años vivirías ahí?", 3, 30, 10)
        with st.expander("Ajustar el crédito"):
            plazo = st.select_slider("Plazo", options=[10, 15, 20, 25, 30], value=20, format_func=lambda x: f"{x} años")
            tea = st.slider("Tasa (TEA)", 5.0, 15.0, round(TEA_BCRP * 100, 2), 0.05, format="%.2f %%",
                            help=f"Promedio de la banca según el BCRP ({ind['tea_hipoteca']['periodo']}).") / 100
        ss.update({"precio": float(casa["precio_pen"]), "area": area, "alquiler": float(alquiler),
                   "inicial": inicial, "plazo": plazo, "tea": tea, "horizonte": horizonte,
                   "casa_url": casa["aviso"]})
        st.button("Ver qué me conviene →", type="primary", use_container_width=True, on_click=ir, args=(3,))
        st.button("← Cambiar distrito", use_container_width=True, on_click=ir, args=(1,))

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
        fila1, fila2 = st.columns(3), st.columns(2)
        for (texto, clave), col in zip(preguntas.items(), list(fila1) + list(fila2)):
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

st.markdown(f"""
<div class="tp-confianza">
  <div>📊 <b>Datos reales</b><br>96 avisos de Urbania (15/11/2026) y tasas del BCRP
  ({ind['tea_hipoteca']['periodo']}).</div>
  <div>🔓 <b>Cálculo abierto</b><br>Cualquiera puede revisar el modelo en
  <a href="https://github.com/karelysscs/Proyecto_Final" target="_blank">GitHub</a>.</div>
  <div>🔒 <b>No guardamos tus datos</b><br>Todo se calcula al momento; no pedimos nombre, correo ni DNI.</div>
</div>""", unsafe_allow_html=True)
with st.expander("¿Cómo calculamos?"):
    st.markdown(
        "Simulamos **mes a mes** dos caminos durante los años que vivirías ahí:\n"
        "- **Comprar:** cuota inicial, crédito con cuota fija (TEA), seguros, predial, arbitrios, mantenimiento, "
        "alcabala y gastos de cierre, y al final vender el depa (con comisión) a un precio que sube 3 % al año.\n"
        "- **Alquilar:** pagas el alquiler (sube 3 % al año) e **inviertes** la cuota inicial y cada mes en que "
        "alquilar sale más barato que la cuota, a la tasa de depósitos a plazo del BCRP.\n\n"
        "Gana el camino con **más patrimonio al final**. Precio y alquiler son medianas de avisos reales del distrito.")
st.caption("Techito Propio · herramienta educativa con supuestos simplificados; no es asesoría financiera personalizada.")
