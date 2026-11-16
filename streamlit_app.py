"""Techito Propio: ¿compro o alquilo en Lima? (app pública en Streamlit Community Cloud).

Ejecutar en local:  streamlit run streamlit_app.py

Recorrido guiado en 3 pasos:
  1. ¿Dónde quieres vivir?  -> mapa Folium de 4 distritos con precios reales (Urbania).
  2. Elige tu depa          -> avisos reales en venta vs. el alquiler de uno parecido.
  3. Tu asesora hipotecaria -> veredicto conversacional + preguntas que recalculan el
                               modelo en vivo con tasas del API del BCRP.
"""
import base64
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
    "Magdalena del Mar": {"coord": (-12.0908, -77.0710), "emoji": "⛵", "frase": "Costa Verde, céntrico y en crecimiento", "corto": "Magdalena"},
    "Pueblo Libre": {"coord": (-12.0749, -77.0630), "emoji": "🏺", "frase": "Tranquilo, tradicional y con museos"},
    "Lince": {"coord": (-12.0843, -77.0347), "emoji": "🚲", "frase": "Pequeño, céntrico y a pasos de San Isidro"},
    "La Victoria": {"coord": (-12.0732, -77.0177), "emoji": "⚽", "frase": "Santa Catalina y Balconcillo, precio de entrada"},
    "San Borja": {"coord": (-12.1010, -76.9990), "emoji": "🌿", "frase": "Arbolado, ordenado y con buenos colegios"},
}
DISTRITOS["Santiago de Surco"]["corto"] = "Surco"
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
             "rentabilidad_alternativa": RENT_BCRP, "aplica_alcabala": ss.get("alcabala", True)}
    datos.update(cambios)
    return Perfil.desde_dict(datos)


def soles(x):
    return f"S/ {x:,.0f}"


LIMITE_CUOTA = 0.30  # referencia usual de los bancos: cuota / ingreso neto


def informe_html(p, r, eq):
    """Informe descargable (producto 'Informe Premium')."""
    import html
    import re

    def md(t):
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(t))

    conversacion = "".join(
        f"<p class='yo'>🙋 {md(m[4:])}</p>" if m.startswith("YO::") else f"<p class='techi'>🧑‍💼 {md(m)}</p>"
        for m in ss.chat)
    filas = [("Distrito", ss.distrito), ("Depa", ss.casa_desc), ("Precio", soles(p.precio_vivienda)),
             ("Alquiler de uno parecido", soles(p.alquiler_mensual) + "/mes"),
             ("Cuota inicial", f"{soles(r['cuota_inicial'])} ({p.cuota_inicial_pct:.0%})"),
             ("Crédito", f"{soles(r['prestamo'])} a {p.plazo_anios} años, TEA {p.tea_hipoteca * 100:.2f} %"),
             ("Cuota mensual", soles(r["cuota_mensual"])),
             ("Gastos de cierre (incl. alcabala)", f"{soles(r['gastos_cierre'])} ({soles(r['alcabala'])})"),
             ("Patrimonio final si compras", soles(r["patrimonio_comprador"])),
             ("Patrimonio final si alquilas e inviertes", soles(r["patrimonio_inquilino"])),
             ("Alquiler de equilibrio", soles(eq) + "/mes" if eq else "—"),
             ("Años que vivirías ahí", str(p.horizonte_anios))]
    tabla = "".join(f"<tr><td>{a}</td><td><b>{b}</b></td></tr>" for a, b in filas)
    checklist = ["Cotiza la TEA en al menos 3 bancos y compara la TCEA (incluye seguros).",
                 "Pide la partida registral del depa en SUNARP y verifica que no tenga cargas.",
                 "Confirma si aplica alcabala (vivienda usada) o si es primera venta.",
                 "Revisa si calificas al Bono MiVivienda o al Bono del Buen Pagador.",
                 "Pregunta el mantenimiento mensual y el predial del depa.",
                 "Guarda un fondo de emergencia de 3 a 6 cuotas antes de firmar."]
    lista = "".join(f"<li>{c}</li>" for c in checklist)
    veredicto = "COMPRAR" if r["recomendacion"] == "comprar" else "ALQUILAR e invertir la diferencia"
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Techito Propio · Informe {html.escape(ss.distrito)}</title>
<style>body{{font-family:Georgia,serif;background:#FFF9F2;color:#2E2A3A;max-width:760px;margin:2rem auto;padding:0 1rem}}
h1{{color:#D9583B;margin-bottom:0}}.v{{background:#D9583B;color:#FFF9F2;padding:.8rem 1rem;border-radius:12px;font-size:1.2rem}}
table{{width:100%;border-collapse:collapse}}td{{padding:.4rem;border-bottom:1px solid #F1D2BD}}
.techi{{background:#FCEBDD;padding:.6rem .8rem;border-radius:10px}}.yo{{text-align:right;color:#5a5368}}
small{{color:#8a8296}}</style></head><body>
<h1>🏠 Techito Propio</h1><small>Informe generado el {time.strftime('%d/%m/%Y')} · datos: Urbania (nov. 2026) y BCRP</small>
<p class="v">Recomendación: <b>{veredicto}</b> en un horizonte de {p.horizonte_anios} años.</p>
<h2>Tu caso en números</h2><table>{tabla}</table>
<h2>Tu conversación con Techi</h2>{conversacion}
<h2>Checklist antes de ir al banco</h2><ul>{lista}</ul>
<p><small>Herramienta educativa con supuestos simplificados; no es asesoría financiera personalizada.
Aviso del depa: {html.escape(ss.casa_url)}</small></p></body></html>"""


def escribir(texto):
    """Efecto de 'escribiendo…' para los mensajes nuevos de la asesora."""
    for palabra in texto.split(" "):
        time.sleep(0.02)
        yield palabra + " "


# ------------------------------------------------------------------ marca (estética "Lima de noche")
TEJA, AMBAR, CREMA, TINTA, SALVIA, CIAN = "#FF6B3D", "#FFB547", "#EDE9F7", "#EDE9F7", "#3DDBD9", "#3DDBD9"
ASSETS = RAIZ / "assets"
st.logo(str(ASSETS / "logo_noche.svg"), size="large", icon_image=str(ASSETS / "icono.svg"))
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&display=swap');
  .stApp {{
    background:
      radial-gradient(1200px 500px at 85% -10%, rgba(255,107,61,.18), transparent 60%),
      radial-gradient(900px 500px at -10% 110%, rgba(61,219,217,.12), transparent 60%),
      linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px) 0 0 / 40px 40px,
      linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px) 0 0 / 40px 40px,
      #0B0A14;
  }}
  .block-container {{ padding-top: 3.8rem; }}
  h1, h2, h3, h4, .tp-paso, .tp-chip {{ font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -.01em; }}
  .tp-marca {{ display: flex; align-items: center; justify-content: center; gap: .9rem; margin: 0 0 .5rem 0; }}
  .tp-marca img {{ width: 64px; height: 64px; filter: drop-shadow(0 0 18px rgba(255,107,61,.45)); }}
  .tp-nombre {{ font-family: 'Space Grotesk', sans-serif; font-size: 3rem; font-weight: 700; line-height: 1;
               letter-spacing: -.03em; color: {CREMA}; text-shadow: 0 0 28px rgba(237,233,247,.18); }}
  .tp-nombre span {{ background: linear-gradient(90deg, {TEJA}, {AMBAR}); -webkit-background-clip: text;
                    background-clip: text; color: transparent; }}
  .tp-hero {{ text-align: center; max-width: 820px; margin: 0 auto; }}
  .tp-hero h1 {{ font-size: 1.9rem; line-height: 1.15; margin: 0 0 .4rem 0; padding: 0; color: {CREMA} !important; }}
  .tp-hero h1 span {{ background: linear-gradient(90deg, {TEJA}, {AMBAR}, {CIAN}); -webkit-background-clip: text;
                     background-clip: text; color: transparent; filter: drop-shadow(0 0 18px rgba(255,107,61,.35)); }}
  .tp-hero p {{ font-size: 1.05rem; color: #B5AECB; margin: 0 0 .8rem 0; }}
  .tp-chip {{ display: inline-block; background: rgba(255,255,255,.05); color: {AMBAR}; border: 1px solid rgba(255,181,71,.35);
             border-radius: 999px; padding: .2rem .75rem; margin: 0 .3rem .3rem 0; font-size: .82rem; font-weight: 600;
             backdrop-filter: blur(6px); }}
  .tp-pasos {{ display: flex; gap: .5rem; margin: .6rem 0 1.2rem 0; }}
  .tp-paso {{ flex: 1; text-align: center; padding: .55rem; border-radius: 12px; font-weight: 600;
             background: rgba(255,255,255,.04); color: #7D7697; border: 1px solid #2C2748; }}
  .tp-paso.activo {{ background: linear-gradient(90deg, {TEJA}, {AMBAR}); color: #160F0A; border-color: transparent;
                    box-shadow: 0 0 22px rgba(255,107,61,.45); }}
  .tp-paso.hecho {{ color: {CIAN}; border-color: rgba(61,219,217,.4); }}
  div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 16px; background: rgba(255,255,255,.035);
       border-color: rgba(255,255,255,.09) !important; backdrop-filter: blur(10px);
       transition: border-color .2s, box-shadow .2s; }}
  div[data-testid="stVerticalBlockBorderWrapper"]:hover {{ border-color: rgba(255,107,61,.55) !important;
       box-shadow: 0 0 24px rgba(255,107,61,.15); }}
  .stButton button, .stLinkButton a, .stDownloadButton button {{ border-radius: 999px; font-weight: 600; }}
  .stButton button[kind="primary"], .stDownloadButton button[kind="primary"] {{
       background: linear-gradient(90deg, {TEJA}, {AMBAR}); color: #160F0A; border: none;
       box-shadow: 0 0 18px rgba(255,107,61,.35); }}
  .stButton button[kind="primary"]:hover {{ box-shadow: 0 0 28px rgba(255,181,71,.6); }}
  div[data-testid="stMetricValue"] {{ color: {AMBAR}; font-family: 'Space Grotesk', sans-serif;
       text-shadow: 0 0 16px rgba(255,181,71,.35); }}
  .tp-badge {{ display: inline-block; border-radius: 999px; padding: .15rem .65rem; font-size: .8rem; font-weight: 700; }}
  .tp-badge.comprar {{ background: rgba(61,219,217,.12); color: {CIAN}; border: 1px solid rgba(61,219,217,.45); }}
  .tp-badge.alquilar {{ background: rgba(255,181,71,.12); color: {AMBAR}; border: 1px solid rgba(255,181,71,.45); }}
  .tp-mini {{ font-size: .9rem; color: #B5AECB; margin: .2rem 0 .5rem 0; }}
  .tp-mini b {{ color: {CREMA}; }}
  .tp-confianza {{ display: flex; gap: 1rem; flex-wrap: wrap; background: rgba(255,255,255,.035);
                  border: 1px solid rgba(255,255,255,.08); border-radius: 16px;
                  padding: .8rem 1.1rem; margin-top: 1.2rem; font-size: .9rem; color: #B5AECB; }}
  .tp-confianza div {{ flex: 1; min-width: 220px; }}
  .tp-confianza b {{ color: {CREMA}; }}
  .tp-confianza a {{ color: {CIAN}; }}
  .tp-futuro {{ display: flex; gap: 1rem; }}
  .tp-futuro div {{ flex: 1; border-radius: 16px; padding: .9rem 1rem; background: rgba(255,255,255,.04);
                   border: 1px solid rgba(255,255,255,.1); }}
  .tp-futuro .c {{ border-color: rgba(255,107,61,.5); box-shadow: 0 0 20px rgba(255,107,61,.15); }}
  .tp-futuro .a {{ border-color: rgba(61,219,217,.5); box-shadow: 0 0 20px rgba(61,219,217,.12); }}
  .tp-futuro small {{ color: #B5AECB; }}
  .tp-futuro b {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; display: block; }}
  .tp-futuro .c b {{ color: {TEJA}; }} .tp-futuro .a b {{ color: {CIAN}; }}
</style>
""", unsafe_allow_html=True)

LOGO_B64 = base64.b64encode((ASSETS / "icono_noche.svg").read_bytes()).decode()
st.markdown(f"""
<div class="tp-marca">
  <img src="data:image/svg+xml;base64,{LOGO_B64}" alt="Logo de Techito Propio">
  <div class="tp-nombre">Techito <span>Propio</span></div>
</div>""", unsafe_allow_html=True)

if ss.paso == 1:
    st.markdown(f"""
<div class="tp-hero">
  <h1>¿Compro o alquilo? <span>Te lo decimos con números.</span></h1>
  <p>Avisos reales, tasas en vivo del BCRP y un modelo financiero completo. Gratis, en 1 minuto
  y sin que nadie te quiera vender nada.</p>
  <span class="tp-chip">🏘️ {len(df)} avisos reales</span><span class="tp-chip">🏦 Tasas BCRP en vivo</span>
  <span class="tp-chip">🔓 Cálculo abierto</span>
</div>""", unsafe_allow_html=True)

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
        mapa = folium.Map(location=(-12.105, -77.04), zoom_start=12, scrollWheelZoom=False,
                          tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                          attr="Esri, HERE, Garmin, © OpenStreetMap contributors")
        folium.TileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
                         attr="Esri", overlay=True, name="Etiquetas").add_to(mapa)
        for d, info in DISTRITOS.items():
            fila = resumen.loc[d]
            elegido = d == ss.distrito
            folium.CircleMarker(
                info["coord"], radius=fila["venta_m2_mediana"] / 340,
                color=AMBAR, fill=True, fill_color=TEJA, fill_opacity=0.55,
                weight=3, tooltip=d,
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
        tarjetas = sorted(((d, *adelanto(d, TEA_BCRP, RENT_BCRP)) for d in DISTRITOS), key=lambda t: t[1])
        st.markdown("<span class='tp-mini'>Depa de 90 m², del más accesible al más caro:</span>",
                    unsafe_allow_html=True)
        with st.container(height=440, border=False):
            cuadros = st.columns(3)
            for i, (d, precio90, alq90, veredicto) in enumerate(tarjetas):
                info = DISTRITOS[d]
                with cuadros[i % 3].container(border=True):
                    st.markdown(f"**{info['emoji']} {info.get('corto', d)}**  \n"
                                f"<div class='tp-mini'>Comprar <b>{soles(precio90)}</b><br>"
                                f"Alquilar <b>{soles(alq90)}/mes</b></div>"
                                f"<span class='tp-badge {veredicto}'>"
                                f"{'✅ COMPRAR' if veredicto == 'comprar' else '🔑 ALQUILAR'}</span>",
                                unsafe_allow_html=True)
                    st.button("Ver depas →", key=f"btn_{d}", type="primary", help=info["frase"],
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
        modo = st.segmented_control("¿Qué depa analizamos?", ["🏘️ Avisos del mercado", "✍️ Tengo mi propio depa"],
                                    default="🏘️ Avisos del mercado", key="modo_depa", label_visibility="collapsed")
    if modo == "✍️ Tengo mi propio depa":
        with lista, st.container(border=True):
            st.markdown("**Cuéntame del depa que tienes en mente**  \n<span class='tp-mini'>Uno que viste en un "
                        "portal, en un proyecto o que te ofrecieron. Lo comparamos con el mercado de "
                        f"{d}.</span>", unsafe_allow_html=True)
            c1, c2 = st.columns([3, 2])
            monto = c1.number_input("Precio", 30_000, 20_000_000, int(ss.get("mi_monto", 450_000)), 5_000, key="mi_monto")
            moneda = c2.radio("Moneda", ["S/", "US$"], horizontal=True, key="mi_moneda")
            c3, c4, c5 = st.columns(3)
            m2 = c3.number_input("Área (m²)", 20, 1_000, int(ss.get("mi_m2", 90)), 1, key="mi_m2")
            dorm = c4.number_input("Dormitorios", 1, 8, int(ss.get("mi_dorm", 3)), 1, key="mi_dorm")
            banos = c5.number_input("Baños", 1, 8, int(ss.get("mi_banos", 2)), 1, key="mi_banos")
            estreno = st.checkbox("Es de estreno (primera venta: no paga alcabala)", key="mi_estreno")
            link = st.text_input("Link del aviso (opcional)", key="mi_link", placeholder="https://…")
            tc = ind["tipo_cambio"]["valor"]
            precio_pen = monto * tc if moneda == "US$" else monto
            m2_mercado = fila["venta_m2_mediana"]
            dif = precio_pen / m2 / m2_mercado - 1
            st.markdown(f"<span class='tp-mini'>= <b>{soles(precio_pen)}</b>"
                        + (f" (TC {tc:.3f}, BCRP)" if moneda == "US$" else "")
                        + f" · <b>{soles(precio_pen / m2)}/m²</b>, un <b>{abs(dif):.0%} "
                        f"{'más caro' if dif > 0 else 'más barato'}</b> que la mediana de {d} "
                        f"({soles(m2_mercado)}/m²).</span>", unsafe_allow_html=True)
            if dif > 0.25:
                st.warning("Está bastante por encima del mercado del distrito: vale la pena negociar el precio.", icon="💬")
            elif dif < -0.25:
                st.info("Está muy por debajo del mercado: revisa bien el estado del depa y su partida en SUNARP.", icon="🔎")
        casa = {"precio_pen": float(precio_pen), "area_m2": float(m2), "dormitorios": dorm, "banos": banos,
                "aviso": link.strip()}
        ss.alcabala = not estreno
    else:
        with lista, st.container(height=470, border=False):
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
        casa = ventas[ventas["id"] == ss.aviso_id].iloc[0].to_dict()
        ss.alcabala = True

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
        ingreso = st.number_input("💼 Tu ingreso neto mensual (opcional)", 0, 300_000, int(ss.get("ingreso", 0)), 500,
                                  help="Para decirte si el banco te prestaría y hasta qué precio te alcanza. No se guarda.")
        ss.update({"precio": float(casa["precio_pen"]), "area": area, "alquiler": float(alquiler),
                   "inicial": inicial, "plazo": plazo, "tea": tea, "horizonte": horizonte,
                   "casa_url": casa["aviso"], "ingreso": ingreso, "casa_desc":
                   f"{area:.0f} m², {casa['dormitorios']} dorm., {casa['banos']} baños"})
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
        if pregunta == "sueldo":
            return capacidad()
        return ""

    def capacidad():
        """¿Me alcanza? Regla referencial: la cuota no debería pasar ~30 % del ingreso neto."""
        if not ss.ingreso:
            return ("Para responderte necesito tu **ingreso neto mensual**: vuelve al paso anterior (← Cambiar depa) "
                    "y escríbelo. No lo guardamos.")
        ratio = r["cuota_mensual"] / ss.ingreso
        tem = (1 + ss.tea) ** (1 / 12) - 1
        prestamo_max = ss.ingreso * LIMITE_CUOTA * (1 - (1 + tem) ** -(ss.plazo * 12)) / tem
        precio_max = prestamo_max / (1 - ss.inicial)
        if ratio <= LIMITE_CUOTA:
            veredicto = "✅ **Te alcanza.** Estás dentro de lo que suelen aceptar los bancos."
        elif ratio <= 0.40:
            veredicto = "⚠️ **Estás al límite.** Algunos bancos te pedirán más inicial o un codeudor."
        else:
            veredicto = "❌ **Hoy no te alcanza.** Es probable que el banco no apruebe este crédito."
        return (f"La cuota de **{soles(r['cuota_mensual'])}** sería el **{ratio:.0%}** de tu ingreso "
                f"({soles(ss.ingreso)}). Como referencia, los bancos suelen pedir que no pase de ~{LIMITE_CUOTA:.0%}. "
                f"{veredicto} Con tu sueldo y {ss.inicial:.0%} de inicial, podrías apuntar a un depa de hasta "
                f"**{soles(precio_max)}**.")

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
        if ss.ingreso:
            ss.chat.append(capacidad())
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
                     "⚖️ ¿Qué alquiler haría que comprar convenga?": "equilibrio",
                     "🧾 ¿Me alcanza con mi sueldo?": "sueldo"}
        fila1, fila2 = st.columns(3), st.columns(3)
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
        anio = st.slider("🚀 Viaja al futuro: elige un año", int(serie.index.min()), int(serie.index.max()),
                         int(serie.index.max()), format="Año %d", key="viaje")
        ano_cal = time.localtime().tm_year + anio
        pc, pa = serie.loc[anio, "Si compras"], serie.loc[anio, "Si alquilas e inviertes"]
        st.markdown(f"""<div class="tp-futuro">
  <div class="c"><small>En {ano_cal}, si compras</small><b>{soles(pc)}</b><small>depa menos deuda</small></div>
  <div class="a"><small>En {ano_cal}, si alquilas</small><b>{soles(pa)}</b><small>lo que invertiste</small></div>
</div>""", unsafe_allow_html=True)
        st.caption(("🏠 En ese año vas ganando comprando" if pc > pa else "🔑 En ese año vas ganando alquilando")
                   + f" por {soles(abs(pc - pa))}.")
        st.markdown("**Tu patrimonio año a año**")
        st.line_chart(serie, y_label="S/", x_label="Año", height=280, color=[TEJA, CIAN])
        if ss.casa_url:
            st.link_button("Ver el aviso del depa elegido ↗", ss.casa_url, use_container_width=True)
        with st.container(border=True):
            st.markdown("**📄 Tu informe personal**  \n<span class='tp-mini'>Tu caso, los números clave, la "
                        "conversación con Techi y un checklist para ir al banco. "
                        "<b>Plan Premium: S/ 19</b> · gratis durante la demo.</span>", unsafe_allow_html=True)
            st.download_button("Descargar mi informe", informe_html(p, r, eq),
                               file_name=f"techito-propio-{ss.distrito.lower().replace(' ', '-')}.html",
                               mime="text/html", type="primary", use_container_width=True)

    with st.expander("📋 Fuentes de los datos"):
        st.markdown(f"- Precios: {int(resumen.loc[ss.distrito, 'n_venta'])} avisos de venta y "
                    f"{int(resumen.loc[ss.distrito, 'n_alquiler'])} de alquiler en Urbania ({ss.distrito}, nov. 2026).")
        for v in ind.values():
            valor = f"{v['valor']:.3f}" if v["nombre"].startswith("Tipo") else f"{v['valor'] * 100:.2f} %"
            estado = "en vivo" if v["en_vivo"] else "valor por defecto, el API no respondió"
            st.markdown(f"- {v['nombre']}: **{valor}** ({v['periodo']}, {estado}) · [BCRP]({v['url']})")

    n1, n2, _ = st.columns([1, 1, 4])
    n1.button("← Cambiar depa", on_click=ir, args=(2,))
    n2.button("Empezar de nuevo", on_click=lambda: ss.update(paso=1, distrito=None, aviso_id=None, chat=[]))

st.markdown(f"""
<div class="tp-confianza">
  <div>📊 <b>Datos reales</b><br>{len(df)} avisos de Urbania de {len(DISTRITOS)} distritos (nov. 2026) y tasas del BCRP
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
