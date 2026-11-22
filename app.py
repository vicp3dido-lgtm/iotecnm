"""Aplicación IoTecNM — Costo mínimo y Ruta crítica (Streamlit).
Instituto Tecnológico Nacional de México · Tuxtla Gutiérrez
"""
import base64
import html
import os
import time

import pandas as pd
import streamlit as st

from logica import ProblemaNoBalanceado, costo_minimo, fmt, ruta_critica

try:  # para saber qué sesión es cada visitante (usuarios en línea)
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:  # pragma: no cover
    get_script_run_ctx = None

st.set_page_config(page_title="Aplicación IoTecNM", page_icon="🎓", layout="wide",
                   initial_sidebar_state="collapsed")

ss = st.session_state
CARPETA = os.path.dirname(os.path.abspath(__file__))

# ==========================================================================
# PALETAS (todas en azul, color del Instituto) Y TEMAS
# ==========================================================================
PALETAS = {
    "Azul TecNM":      dict(icono="🔵", primary="#1B396A", secondary="#2F6DB5", accent="#5B9BD5", soft="#E3ECF8", soft2="#EEF3FB"),
    "Azul cielo":      dict(icono="🩵", primary="#1F6FB8", secondary="#4C9BE0", accent="#8EC5F5", soft="#E3F1FD", soft2="#EEF7FE"),
    "Verde esmeralda": dict(icono="🟢", primary="#0F6B4B", secondary="#2E9E75", accent="#6CCBA5", soft="#E1F4EC", soft2="#EEF8F3"),
    "Turquesa":        dict(icono="🌊", primary="#0B6E7F", secondary="#1F9DB3", accent="#7ACFDC", soft="#DDF2F6", soft2="#EBF8FA"),
    "Morado":          dict(icono="🟣", primary="#4B2C82", secondary="#7A55C2", accent="#B79BEA", soft="#ECE6F8", soft2="#F4F0FB"),
    "Rosa":            dict(icono="🌸", primary="#A8326E", secondary="#D8559A", accent="#F2A0CB", soft="#FBE4F0", soft2="#FDF0F7"),
    "Guinda":          dict(icono="🔴", primary="#7A1F3D", secondary="#B03A5E", accent="#E08AA5", soft="#F6E1E8", soft2="#FBEFF3"),
    "Naranja":         dict(icono="🟠", primary="#B3470C", secondary="#E8742A", accent="#F5A66B", soft="#FCE9DC", soft2="#FEF3EB"),
    "Dorado":          dict(icono="🟡", primary="#7A5A00", secondary="#C99A1B", accent="#F0CB6A", soft="#FBF1D2", soft2="#FDF8E6"),
    "Grafito":         dict(icono="⚫", primary="#2B3340", secondary="#556070", accent="#9AA7B8", soft="#E6EAF0", soft2="#F1F3F7"),
}
CLARO = dict(bg="#EAF0F9", surface="#FFFFFF", text="#0F172A", muted="#5B6B86",
             border="#D3DDEC", shadow="0 8px 24px rgba(27,57,106,.14)")
OSCURO = dict(bg="#0C1424", surface="#14223A", text="#E8EEF9", muted="#9FB0CC",
              border="#243656", shadow="0 8px 24px rgba(0,0,0,.45)")

ss.setdefault("paleta", "Azul TecNM")
ss.setdefault("tema", "Sistema")
ss.setdefault("nombre", "")  # nombre registrado: se conserva en todas las páginas
ss.setdefault("vista", "inicio")
ss.setdefault("cm_version", 0)
ss.setdefault("cm_m", 3)
ss.setdefault("cm_n", 3)
ss.setdefault("cm_datos", None)
ss.setdefault("cm_res", None)
ss.setdefault("cm_err", None)
ss.setdefault("cpm_version", 0)
ss.setdefault("cpm_datos", None)
ss.setdefault("cpm_n_act", 3)
ss.setdefault("cpm_res", None)
ss.setdefault("cpm_err", None)


def leer_imagen(nombres):
    """Devuelve (base64, mime) de la primera imagen que exista, o None."""
    for nombre in nombres:
        ruta = os.path.join(CARPETA, nombre)
        if os.path.exists(ruta):
            ext = nombre.rsplit(".", 1)[-1].lower()
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[ext]
            with open(ruta, "rb") as f:
                return base64.b64encode(f.read()).decode(), mime
    return None


def paisaje_svg(p):
    """Ilustración vectorial plana de Tuxtla: cañón, montañas, ciudad y palmeras."""
    pr, se, ac = p["primary"], p["secondary"], p["accent"]

    def palmera(x, alto=84, escala=1.0):
        y = 322 - alto
        hojas = "".join(
            f'<ellipse cx="{x + dx}" cy="{y + dy}" rx="{26 * escala}" ry="{6 * escala}" '
            f'transform="rotate({ang} {x + dx} {y + dy})"/>'
            for dx, dy, ang in ((-20, 4, -28), (20, 4, 28), (-12, -6, -62), (12, -6, 62), (0, -10, 90)))
        return (f'<path d="M{x},322 Q{x + 8},{322 - alto / 2} {x},{y}" stroke="{pr}" stroke-width="{5 * escala}" fill="none"/>'
                f'<g fill="{pr}">{hojas}</g>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 360" preserveAspectRatio="xMidYMax slice">
<polygon points="0,250 80,190 150,230 250,150 330,215 420,170 520,235 600,185 690,235 780,165 870,220 950,150 1040,215 1120,175 1200,230 1200,360 0,360" fill="{ac}" opacity=".55"/>
<polygon points="0,150 40,120 75,160 110,95 150,170 190,130 235,215 290,240 340,360 0,360" fill="{se}" opacity=".55"/>
<polygon points="1200,150 1160,120 1125,160 1090,95 1050,170 1010,130 965,215 910,240 860,360 1200,360" fill="{se}" opacity=".55"/>
<polygon points="0,200 55,165 100,205 145,150 195,225 250,258 300,360 0,360" fill="{pr}" opacity=".9"/>
<polygon points="1200,200 1145,165 1100,205 1055,150 1005,225 950,258 900,360 1200,360" fill="{pr}" opacity=".9"/>
<polygon points="0,300 120,270 250,285 340,235 430,262 540,205 660,262 770,222 860,265 950,285 1080,270 1200,300 1200,360 0,360" fill="{se}" opacity=".8"/>
<g fill="{pr}" opacity=".95">
<rect x="360" y="270" width="26" height="52"/><rect x="390" y="256" width="22" height="66"/>
<rect x="418" y="276" width="30" height="46"/>
<rect x="468" y="262" width="24" height="60"/><rect x="496" y="250" width="22" height="72"/>
<path d="M548,322 V252 Q548,226 566,226 Q584,226 584,252 V322 Z"/><rect x="564" y="200" width="4" height="26"/><rect x="558" y="208" width="16" height="4"/>
<rect x="592" y="268" width="34" height="54"/><rect x="632" y="256" width="24" height="66"/>
<rect x="662" y="274" width="30" height="48"/><rect x="698" y="260" width="22" height="62"/>
<rect x="726" y="250" width="30" height="72"/><rect x="762" y="272" width="26" height="50"/>
<rect x="794" y="258" width="22" height="64"/>
</g>
<g fill="#ffffff" opacity=".6">
<rect x="366" y="282" width="4" height="5"/><rect x="374" y="282" width="4" height="5"/>
<rect x="396" y="270" width="4" height="5"/><rect x="474" y="276" width="4" height="5"/>
<rect x="502" y="266" width="4" height="5"/><rect x="598" y="282" width="4" height="5"/>
<rect x="608" y="282" width="4" height="5"/><rect x="638" y="270" width="4" height="5"/>
<rect x="732" y="264" width="4" height="5"/><rect x="742" y="264" width="4" height="5"/>
<rect x="800" y="272" width="4" height="5"/>
</g>
{palmera(215, 92)}{palmera(290, 70, .85)}{palmera(910, 70, .85)}{palmera(985, 92)}
<rect x="0" y="322" width="1200" height="14" fill="{pr}"/>
<rect x="0" y="336" width="1200" height="12" fill="{se}" opacity=".75"/>
<rect x="0" y="348" width="1200" height="12" fill="{ac}" opacity=".6"/>
</svg>"""


def camion_svg(p):
    """Combi oscura de transporte (como la ilustración de referencia)."""
    ac, se = p["accent"], p["secondary"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
<path d="M10,70 V40 Q10,16 36,16 H150 Q172,16 182,38 L192,56 Q196,62 196,68 V72 H10 Z" fill="#171d2b"/>
<path d="M10,52 Q80,40 196,60 V68 Q100,54 10,66 Z" fill="#3a4357"/>
<path d="M26,26 H50 V44 H22 Q22,26 26,26 Z" fill="#eaf3fc"/><rect x="56" y="26" width="30" height="18" rx="2" fill="#eaf3fc"/>
<rect x="92" y="26" width="30" height="18" rx="2" fill="#eaf3fc"/>
<path d="M128,26 H150 Q162,26 168,40 L172,44 H128 Z" fill="#eaf3fc"/>
<rect x="188" y="54" width="8" height="6" rx="2" fill="#ffd54a"/>
<circle cx="52" cy="76" r="15" fill="#0d111b"/><circle cx="52" cy="76" r="7" fill="{se}"/><circle cx="52" cy="76" r="3" fill="{ac}"/>
<circle cx="150" cy="76" r="15" fill="#0d111b"/><circle cx="150" cy="76" r="7" fill="{se}"/><circle cx="150" cy="76" r="3" fill="{ac}"/>
</svg>"""


def rgba(hex_, a):
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{a})"


def emblema_html():
    """Escudo del Instituto: usa logo_tecnm.png (transparente) como un 'sol' detrás del paisaje."""
    if os.path.exists(os.path.join(CARPETA, "logo_tecnm.png")):
        return '<div class="emblema"><div class="logo-sol" role="img" aria-label="Instituto Tecnológico de Tuxtla Gutiérrez"></div></div>'
    return ('<div class="emblema"><div class="emblema-vacio"><span>TecNM</span>'
            '<small>Guarda aquí tu logo<br>como <b>logo_tecnm.png</b></small></div></div>')


def tema_de_streamlit():
    """'light' o 'dark' según el tema que Streamlit está usando (sigue al sistema)."""
    try:
        return st.context.theme.type
    except Exception:
        return None


def construir_css():
    p = PALETAS.get(ss.paleta, PALETAS["Azul TecNM"])
    claro = dict(CLARO, title=p["primary"], soft=p["soft"], soft2=p["soft2"],
                 logo=p["primary"], halo=rgba(p["accent"], .32))
    oscuro = dict(OSCURO, title=p["accent"], soft="#1A2D4D", soft2="#162640",
                  logo=p["accent"], halo=rgba(p["accent"], .30))

    def variables(d):
        return ";".join(f"--{k}:{v}" for k, v in d.items())

    cam64 = base64.b64encode(camion_svg(p).encode()).decode()
    raiz = (f":root{{--primary:{p['primary']};--secondary:{p['secondary']};--accent:{p['accent']};"
            f"--camion:url('data:image/svg+xml;base64,{cam64}');}}")
    if ss.tema == "Claro":
        temas = f":root{{{variables(claro)}}}"
    elif ss.tema == "Oscuro":
        temas = f":root{{{variables(oscuro)}}}"
    else:  # Sistema: sigue el modo claro/oscuro del dispositivo
        temas = (f":root{{{variables(claro)}}}"
                 f"@media (prefers-color-scheme: dark){{:root{{{variables(oscuro)}}}}}")

    extra = ""
    # el escudo se usa como máscara: toma el color de la paleta y del tema
    if os.path.exists(os.path.join(CARPETA, "logo_tecnm.png")):
        with open(os.path.join(CARPETA, "logo_tecnm.png"), "rb") as f:
            logo64 = base64.b64encode(f.read()).decode()
        mascara = f"url('data:image/png;base64,{logo64}') center/contain no-repeat"
        extra += f".logo-sol{{-webkit-mask:{mascara};mask:{mascara};}}"

    fondo = leer_imagen(["fondo_tuxtla.jpg", "fondo_tuxtla.jpeg", "fondo_tuxtla.png", "fondo_tuxtla.webp"])
    if fondo:
        b64, mime = fondo
        extra += (".st-key-hero{background-image:linear-gradient(180deg,rgba(255,255,255,.80) 0%,rgba(27,57,106,.25) 100%),"
                  f"url('data:{mime};base64,{b64}');background-size:cover;background-position:center;}}")
    else:
        svg64 = base64.b64encode(paisaje_svg(p).encode()).decode()
        extra += (".st-key-hero::after{content:'';position:absolute;left:0;right:0;bottom:0;height:clamp(260px,30vw,440px);"
                  f"background:url('data:image/svg+xml;base64,{svg64}') no-repeat center bottom/100% 100%;"
                  "pointer-events:none;z-index:3;}")

    # si el usuario fuerza un tema distinto al del sistema, las tablas de entrada (que son de Streamlit)
    # se invierten para que combinen con el resto de la página
    real = tema_de_streamlit()
    if ss.tema in ("Claro", "Oscuro") and real in ("light", "dark"):
        if ("light" if ss.tema == "Claro" else "dark") != real:
            extra += '[data-testid="stDataFrame"]{filter:invert(1) hue-rotate(180deg);}'

    return f"<style>{ESTILO_BASE}{raiz}{temas}{extra}</style>"


ESTILO_BASE = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,500&family=Poppins:wght@400;500;600&display=swap');
html, body, .stApp { background: var(--bg) !important; font-family: 'Poppins', sans-serif; }
header[data-testid="stHeader"], footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
.block-container { padding: 3.2rem 1rem 1rem 1rem !important; max-width: 100% !important; width: 100% !important; }
[data-testid="stMainBlockContainer"], [data-testid="stAppViewContainer"] .main { max-width: 100% !important; }
@media (min-width: 900px) { .block-container { padding: 3.2rem 1.6rem 1rem 1.6rem !important; } }
.stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stWidgetLabel"] p, .stApp [data-testid="stCaptionContainer"] { color: var(--text); }
.stApp [data-testid="stCaptionContainer"] p { color: var(--muted); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--title) !important; font-family: 'Playfair Display', serif !important;
  font-style: italic; font-weight: 500 !important; }

/* menú ☰ fijo en la esquina superior izquierda */
.st-key-menu { position: fixed; top: 12px; left: 14px; z-index: 1000; width: auto !important; }
[data-testid="stPopoverBody"] { min-width: 300px; max-width: 340px; background: var(--surface) !important; border: 1px solid var(--border); }
[data-testid="stPopoverBody"] p, [data-testid="stPopoverBody"] label, [data-testid="stPopoverBody"] span { color: var(--text); }

/* campos de texto, números y casillas */
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"], .stApp input, .stApp textarea {
  background: var(--surface) !important; color: var(--text) !important; border-radius: 10px; }
.stApp [data-baseweb="input"] { border-color: var(--border) !important; }
.stApp [data-testid="stNumberInputContainer"], .stApp [data-testid="stNumberInputContainer"] > div {
  background: var(--surface) !important; border-color: var(--border) !important; border-radius: 10px; }
.stApp [data-testid="stNumberInput"] button { background: var(--soft) !important; color: var(--text) !important; border: none !important; }
.stApp [data-baseweb="checkbox"] > span:first-child { background-color: var(--surface) !important; border: 2px solid var(--accent) !important; }

/* botones */
.stApp button[kind="primary"], .stApp [data-testid="stBaseButton-primary"] {
  background: var(--primary) !important; color: #fff !important; border: 1px solid var(--accent) !important;
  border-radius: 999px !important; font-weight: 600; padding: .45rem 1.2rem; }
.stApp button[kind="secondary"], .stApp [data-testid="stBaseButton-secondary"] {
  background: var(--surface) !important; color: var(--title) !important; border: 1px solid var(--accent) !important;
  border-radius: 999px !important; font-weight: 500; }
.stApp button:hover { filter: brightness(1.08); }
.stApp button[kind="primary"] p, .stApp [data-testid="stBaseButton-primary"] p { color: #fff !important; }
.stApp button[kind="secondary"] p, .stApp [data-testid="stBaseButton-secondary"] p { color: var(--title) !important; }

/* ===== portada ===== */
.st-key-hero { position: relative; overflow: hidden; background-color: var(--surface); border-radius: 28px; box-shadow: var(--shadow);
  padding: 1.6rem 1.4rem 3rem 1.4rem; min-height: max(680px, calc(100vh - 4.6rem)); border: 1px solid var(--border); }
.hero-titulo { font-family: 'Playfair Display', serif; font-style: italic; font-weight: 500; font-size: clamp(2.2rem, 5.6vw, 4rem);
  color: var(--text) !important; text-align: center; letter-spacing: .02em; margin: 1.2rem 0 .1rem 0; line-height: 1.1; }
.hero-sub { text-align: center; font-size: clamp(.8rem, 1.5vw, 1rem); letter-spacing: .08em; color: var(--muted) !important;
  text-transform: uppercase; margin-bottom: .6rem; }
.hero-texto { text-align: center; color: var(--muted) !important; max-width: 560px; margin: 0 auto 1rem auto; font-size: .95rem; }
.st-key-hero .stButton { position: relative; z-index: 5; }
.st-key-go_cm, .st-key-go_cpm, .st-key-go_cm .stButton, .st-key-go_cpm .stButton,
.st-key-go_cm [data-testid="stButton"], .st-key-go_cpm [data-testid="stButton"] { display: flex !important; justify-content: center !important; width: 100% !important; }
.st-key-go_cm button, .st-key-go_cpm button { width: 200px; padding: .9rem 1rem; font-size: 1.05rem; box-shadow: var(--shadow); }
.emblema { position: relative; display: flex; justify-content: center; align-items: center; padding-top: 3.4rem; }
.emblema::before { content: ""; position: absolute; left: 50%; top: calc(3.4rem + 130px); width: 380px; height: 380px;
  transform: translate(-50%, -50%); border-radius: 50%; background: radial-gradient(circle, var(--halo) 0%, transparent 68%); }
.logo-sol { position: relative; width: 230px; height: 300px; background: var(--logo); }
.emblema-vacio { width: 190px; height: 190px; border-radius: 50%; background: var(--primary); display: flex; flex-direction: column;
  align-items: center; justify-content: center; border: 5px solid var(--accent); box-shadow: var(--shadow); text-align: center; }
.emblema-vacio span { color: #fff !important; font-size: 2rem; font-weight: 600; }
.emblema-vacio small { color: #dbe7fa !important; font-size: .68rem; margin-top: .3rem; }
.emblema-vacio b { color: #fff !important; }
@media (max-width: 760px) {
    .emblema { padding-top: 1rem; }
  .emblema::before { top: calc(1rem + 130px); }
}


/* combi de transporte que recorre la ciudad (pseudo-elemento de la portada, igual que el paisaje) */
.st-key-hero::before { content: ""; position: absolute; z-index: 4; pointer-events: none;
  width: 14%; aspect-ratio: 2/1; left: -16%;
  bottom: calc(clamp(260px, 30vw, 440px) * 0.066);
  background: var(--camion) no-repeat center/contain;
  animation: recorrer 18s linear infinite, rebote .45s ease-in-out infinite alternate; }
@keyframes recorrer { from { left: -16%; } to { left: 104%; } }
@keyframes rebote { from { transform: translateY(0); } to { transform: translateY(-2px); } }
@media (prefers-reduced-motion: reduce) { .st-key-hero::before { animation: none; left: 12%; } }

/* registro obligatorio */
.st-key-registro { max-width: 680px; margin: 8vh auto 0 auto; background: var(--surface); border: 1px solid var(--border);
  border-radius: 26px; padding: 1.8rem 1.6rem; box-shadow: var(--shadow); }
.st-key-registro .reg-inst { font-size: clamp(1.5rem, 4.2vw, 2.2rem); margin: .2rem 0 .3rem 0; }
.st-key-registro .reg-app { font-size: clamp(2.2rem, 6vw, 3.2rem); margin: 0 0 1.2rem 0; }

/* ===== barra lateral de navegación (como un panel) ===== */
.st-key-nav { background: var(--primary); border-radius: 26px; padding: 1.2rem .9rem; box-shadow: var(--shadow); min-height: 420px; }
.st-key-nav .nav-logo { font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.6rem; margin-bottom: 1rem;
  text-align: center; color: #fff !important; }
.stApp .st-key-nav button, .stApp .st-key-nav [data-testid^="stBaseButton"] { width: 100%; justify-content: flex-start; text-align: left;
  background: transparent !important; border: 1px solid transparent !important; border-radius: 14px !important; white-space: nowrap; }
.stApp .st-key-nav button p { color: #fff !important; }
.stApp .st-key-nav button:hover { background: rgba(255,255,255,.16) !important; }
.stApp .st-key-nav button[kind="primary"], .stApp .st-key-nav [data-testid="stBaseButton-primary"] {
  background: #fff !important; border-color: #fff !important; }
.stApp .st-key-nav button[kind="primary"] p, .stApp .st-key-nav [data-testid="stBaseButton-primary"] p { color: var(--primary) !important; }

.st-key-nav [data-testid="stPageLink-NavLink"] { border-radius: 14px; padding: .5rem .8rem; background: transparent; }
.st-key-nav [data-testid="stPageLink-NavLink"] p, .st-key-nav [data-testid="stPageLink-NavLink"] span { color: #fff !important; font-weight: 500; }
.st-key-nav [data-testid="stPageLink-NavLink"]:hover { background: rgba(255,255,255,.16); }
.st-key-nav [data-testid="stPageLink-NavLink"][aria-current="page"] { background: #fff; }
.st-key-nav [data-testid="stPageLink-NavLink"][aria-current="page"] p, .st-key-nav [data-testid="stPageLink-NavLink"][aria-current="page"] span { color: var(--primary) !important; }

[data-testid="InputInstructions"] { display: none !important; }
.st-key-grid_cm, .st-key-grid_cpm { overflow-x: auto; padding-bottom: .3rem; }
.st-key-grid_cm [data-testid="stHorizontalBlock"], .st-key-grid_cpm [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
.st-key-grid_cm [data-testid="stColumn"], .st-key-grid_cpm [data-testid="stColumn"] { min-width: 92px !important; }

/* ===== tarjetas de pasos ===== */
.st-key-paso1, .st-key-paso2, .st-key-paso3, .st-key-panel, .st-key-encabezado {
  background: var(--surface); border: 1px solid var(--border); border-radius: 22px; padding: 1.1rem 1.2rem; box-shadow: var(--shadow); }
.st-key-paso1 { background: linear-gradient(135deg, var(--soft), var(--surface)); }
.st-key-paso2 { background: linear-gradient(135deg, var(--soft2), var(--surface)); }
.st-key-paso3 { background: linear-gradient(135deg, var(--soft), var(--surface)); }
.paso-titulo { display: flex; align-items: center; gap: .6rem; font-family: 'Playfair Display', serif; font-style: italic;
  font-size: 1.35rem; color: var(--title) !important; margin-bottom: .6rem; }
.paso-num { background: var(--primary); color: #fff !important; width: 30px; height: 30px; border-radius: 50%; display: inline-flex;
  align-items: center; justify-content: center; font-size: .9rem; font-style: normal; font-family: 'Poppins', sans-serif; border: 2px solid var(--accent); }
.vacio { color: var(--muted) !important; font-size: .92rem; }

/* tablas de resultados */
.tabla-wrap { overflow-x: auto; margin: .3rem 0 .6rem 0; }
.tabla-io { border-collapse: collapse; width: 100%; font-size: .9rem; }
.tabla-io th { background: var(--primary); color: #fff !important; padding: .45rem .7rem; text-align: center; }
.tabla-io th:first-child { border-top-left-radius: 10px; } .tabla-io th:last-child { border-top-right-radius: 10px; }
.tabla-io td { padding: .4rem .7rem; text-align: center; border-bottom: 1px solid var(--border); color: var(--text) !important; }
.tabla-io td.izq { text-align: left; }
.tabla-io td.asig { background: var(--accent); color: #fff !important; font-weight: 600; }
.tabla-io tr.crit td { background: var(--soft); font-weight: 600; color: var(--title) !important; }
.total { display: inline-block; background: var(--primary); color: #fff !important; padding: .55rem 1.2rem; border-radius: 14px;
  font-size: 1.15rem; font-weight: 600; border: 2px solid var(--accent); margin: .3rem 0; }
.ruta { font-size: 1.05rem; font-weight: 600; color: var(--title) !important; }
.lista-pasos { font-size: .88rem; line-height: 1.7; color: var(--text) !important; }
.lista-pasos code { background: var(--soft); color: var(--text) !important; padding: .1rem .4rem; border-radius: 6px; }

/* usuarios en línea */
.panel-titulo { font-family: 'Playfair Display', serif; font-style: italic; color: var(--title) !important; font-size: 1.3rem; margin-bottom: .5rem; }
.usuario { display: flex; align-items: center; gap: .6rem; padding: .35rem 0; border-bottom: 1px solid var(--border); }
.avatar { width: 34px; height: 34px; border-radius: 50%; background: var(--primary); color: #fff !important; display: flex;
  align-items: center; justify-content: center; font-weight: 600; border: 2px solid var(--accent); }
.punto { width: 9px; height: 9px; border-radius: 50%; background: #2ecc71; margin-left: auto; }
.contador { font-size: 2rem; font-weight: 600; color: var(--title) !important; line-height: 1; }
.muestra { display: inline-block; width: 24px; height: 24px; border-radius: 6px; margin-right: 4px; border: 1px solid var(--border); }
"""


# ==========================================================================
# UTILIDADES
# ==========================================================================
def numero(valor, descripcion):
    """Convierte una celda a número o lanza un error claro."""
    try:
        if valor is None or (isinstance(valor, float) and pd.isna(valor)) or str(valor).strip() == "":
            raise ValueError
        return float(str(valor).replace(",", "."))
    except ValueError:
        raise ValueError(f"Dato inválido o vacío: {descripcion}.")


def esc(x):
    return html.escape(str(x))


def tabla_html(encabezados, filas, resaltadas=None, filas_crit=None, izq=()):
    """Tabla HTML propia (respeta paleta y tema)."""
    resaltadas = resaltadas or set()
    filas_crit = filas_crit or set()
    out = ['<div class="tabla-wrap"><table class="tabla-io"><thead><tr>']
    out += [f"<th>{esc(h)}</th>" for h in encabezados]
    out.append("</tr></thead><tbody>")
    for i, fila in enumerate(filas):
        out.append('<tr class="crit">' if i in filas_crit else "<tr>")
        for j, celda in enumerate(fila):
            clases = []
            if (i, j) in resaltadas:
                clases.append("asig")
            if j in izq:
                clases.append("izq")
            cl = f' class="{" ".join(clases)}"' if clases else ""
            out.append(f"<td{cl}>{esc(celda)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def titulo_paso(n, texto):
    st.markdown(f'<div class="paso-titulo"><span class="paso-num">{n}</span>{esc(texto)}</div>',
                unsafe_allow_html=True)


# ==========================================================================
# USUARIOS EN LÍNEA (conteo anónimo + nombres que cada persona decida escribir)
# ==========================================================================
@st.cache_resource
def registro_visitas():
    return {}


def id_sesion():
    try:
        ctx = get_script_run_ctx()
        return ctx.session_id if ctx else "local"
    except Exception:
        return "local"


@st.fragment(run_every=20)
def panel_usuarios():
    reg = registro_visitas()
    ahora = time.time()
    mi_id = id_sesion()
    reg[mi_id] = {"alias": (ss.get("nombre") or "").strip()[:20], "t": ahora}
    for k in [k for k, v in reg.items() if ahora - v["t"] > 75]:
        reg.pop(k, None)

    total = len(reg)
    con_nombre = [(k, v["alias"]) for k, v in reg.items() if v["alias"]]
    anonimos = total - len(con_nombre)

    partes = ['<div class="panel-titulo">Usuarios en línea</div>',
              f'<div class="contador">{total}</div><div class="vacio">conectados ahora</div><br>']
    for k, alias in con_nombre[:8]:
        tu = " (tú)" if k == mi_id else ""
        partes.append(f'<div class="usuario"><div class="avatar">{esc(alias[0].upper())}</div>'
                      f'<div>{esc(alias)}{tu}</div><div class="punto"></div></div>')
    if anonimos > 0:
        partes.append(f'<div class="vacio" style="margin-top:.6rem">+ {anonimos} visitante(s) sin nombre</div>')
    st.markdown("".join(partes), unsafe_allow_html=True)


# ==========================================================================
# MENÚ ☰ (esquina superior izquierda)
# ==========================================================================
def guardar_nombre():
    ss.nombre = (ss.get("nombre_menu") or "").strip()[:20]


def menu_superior():
    with st.container(key="menu"):
        with st.popover("☰"):
            st.markdown("**🎨 Paleta de colores**")
            st.radio("Paleta", list(PALETAS), key="paleta", label_visibility="collapsed",
                     format_func=lambda n: f"{PALETAS[n]['icono']}  {n}")
            muestras = "".join(
                f'<span class="muestra" style="background:{PALETAS[ss.paleta][c]}"></span>'
                for c in ("primary", "secondary", "accent", "soft"))
            st.markdown(muestras, unsafe_allow_html=True)
            st.markdown("**🌓 Tema**")
            st.radio("Tema", ["Sistema", "Claro", "Oscuro"], key="tema", label_visibility="collapsed")
            st.caption("«Sistema» sigue el modo claro u oscuro de tu dispositivo (Windows, Mac, Linux, iOS, Android).")
            st.markdown("**👤 Registro (obligatorio)**")
            st.text_input("Nombre", value=ss.nombre, key="nombre_menu", on_change=guardar_nombre, max_chars=20, placeholder="Escribe tu nombre",
                          label_visibility="collapsed")
            st.caption("Es obligatorio: tu nombre aparece en la lista de usuarios en línea. Si lo borras, la página te lo pedirá de nuevo.")
    if ss.vista != "inicio":
        st.markdown("<div class='vacio' style='text-align:center'>Aplicación IoTecNM · Instituto Tecnológico Nacional de México, Tuxtla Gutiérrez</div>",
                    unsafe_allow_html=True)


# ==========================================================================
# REGISTRO OBLIGATORIO
# ==========================================================================
def registrar():
    nombre = (ss.get("alias_nuevo") or "").strip()
    if len(nombre) < 2:
        ss.reg_err = "Escribe tu nombre (mínimo 2 letras) para continuar."
    else:
        ss.nombre = nombre[:20]
        ss.reg_err = None


def pantalla_registro():
    with st.container(key="registro"):
        st.markdown('<div class="hero-titulo reg-inst">Instituto Tecnológico Nacional Tuxtla Gutiérrez</div>'
                    '<div class="hero-titulo reg-app">Aplicación IoTecNM</div>', unsafe_allow_html=True)
        with st.form("form_registro", border=False):
            st.text_input("Tu nombre", key="alias_nuevo", max_chars=20, placeholder="Escribe tu nombre")
            st.form_submit_button("Entrar", type="primary", on_click=registrar)
        if ss.get("reg_err"):
            st.error(ss.reg_err)


# ==========================================================================
# PORTADA
# ==========================================================================
def portada():
    with st.container(key="hero"):
        st.markdown('<div class="hero-titulo">Aplicación IoTecNM</div>'
                    '<div class="hero-sub">Instituto Tecnológico Nacional Tuxtla Gutiérrez</div>'
                    '<div class="hero-texto">Resuelve problemas de Investigación de Operaciones paso a paso: '
                    'método de costo mínimo y ruta crítica (CPM).</div>', unsafe_allow_html=True)
        izq, centro, der = st.columns([1, 1, 1], vertical_alignment="center")
        with izq:
            if st.button("Costo mínimo", key="go_cm", type="primary"):
                st.switch_page(PAG_COSTO)
        with centro:
            st.markdown(emblema_html(), unsafe_allow_html=True)
        with der:
            if st.button("Ruta crítica", key="go_cpm", type="primary"):
                st.switch_page(PAG_RUTA)


# ==========================================================================
# NAVEGACIÓN LATERAL (vista de métodos)
# ==========================================================================
def navegacion():
    with st.container(key="nav"):
        st.markdown('<div class="nav-logo">IoTecNM</div>', unsafe_allow_html=True)
        st.page_link(PAG_INICIO, label="Inicio", icon="🏠")
        st.page_link(PAG_COSTO, label="Costo mínimo", icon="📦")
        st.page_link(PAG_RUTA, label="Ruta crítica", icon="🧭")


def encabezado(titulo, subtitulo):
    with st.container(key="encabezado"):
        st.page_link(PAG_INICIO, label="Volver al inicio", icon="⬅️")
        st.markdown(f"## {titulo}")
        st.caption(subtitulo)


# ==========================================================================
# COSTO MÍNIMO
# ==========================================================================
def cm_ejemplo():
    ss.cm_m, ss.cm_n = 3, 3
    ss.cm_datos = pd.DataFrame(
        [[4, 8, 6, 30], [5, 3, 7, 40], [6, 4, 5, 30], [20, 50, 30, None]],
        index=["O1", "O2", "O3", "Demanda"], columns=["D1", "D2", "D3", "Oferta"], dtype="float")
    ss.cm_version += 1
    ss.cm_res = ss.cm_err = None


def cm_limpiar():
    ss.cm_m, ss.cm_n = 3, 3
    ss.cm_datos = None
    ss.cm_version += 1
    ss.cm_res = ss.cm_err = None


def vista_costo_minimo():
    encabezado("Método de costo mínimo",
               "Solución inicial factible de un problema de transporte: siempre se asigna primero a la ruta más barata.")

    # ---- Paso 1: datos
    with st.container(key="paso1"):
        titulo_paso(1, "Ingresa los datos a calcular")
        c1, c2 = st.columns(2)
        m = int(c1.number_input("Orígenes (m)", 1, 10, ss.cm_m, key=f"m_{ss.cm_version}"))
        n = int(c2.number_input("Destinos (n)", 1, 10, ss.cm_n, key=f"n_{ss.cm_version}"))
        datos = ss.cm_datos
        v = ss.cm_version

        def inicial(a, b):
            try:
                if datos is not None and datos.shape == (m + 1, n + 1):
                    x = datos.iloc[a, b]
                    return "" if pd.isna(x) else fmt(float(x))
            except Exception:
                pass
            return ""

        anchos = [1.1] + [1] * n + [1.2]
        txt_c = [[None] * n for _ in range(m)]
        txt_o, txt_d = [None] * m, [None] * n
        with st.container(key="grid_cm"):
            enc = st.columns(anchos)
            enc[0].markdown("**Origen**")
            for b in range(n):
                enc[b + 1].markdown(f"**Destino {b + 1}**")
            enc[n + 1].markdown("**Oferta**")
            for a in range(m):
                fila = st.columns(anchos)
                fila[0].markdown(f"**O{a + 1}**")
                for b in range(n):
                    txt_c[a][b] = fila[b + 1].text_input(f"Costo de O{a + 1} a D{b + 1}", value=inicial(a, b),
                                                          key=f"c_{v}_{a}_{b}", label_visibility="collapsed", placeholder="Costo")
                txt_o[a] = fila[n + 1].text_input(f"Oferta de O{a + 1}", value=inicial(a, n),
                                                  key=f"o_{v}_{a}", label_visibility="collapsed", placeholder="Oferta")
            fila = st.columns(anchos)
            fila[0].markdown("**Demanda**")
            for b in range(n):
                txt_d[b] = fila[b + 1].text_input(f"Demanda de D{b + 1}", value=inicial(m, b),
                                                  key=f"d_{v}_{b}", label_visibility="collapsed", placeholder="Demanda")
        st.caption("Escribe los costos en la cuadrícula, la oferta en la última columna y la demanda en la última fila.")
        balancear = st.checkbox("Balancear automáticamente (origen/destino ficticio)")
        b1, b2, b3, _ = st.columns([1, 1, 1, 2.2])
        resolver = b1.button("Resolver", type="primary", key="cm_res_btn")
        b2.button("Ejemplo", key="cm_ej", on_click=cm_ejemplo)
        b3.button("Limpiar", key="cm_lim", on_click=cm_limpiar)

        if resolver:
            ss.cm_res = ss.cm_err = None
            try:
                costos = [[numero(txt_c[a][b], f"costo de O{a + 1} a D{b + 1}") for b in range(n)] for a in range(m)]
                oferta = [numero(txt_o[a], f"oferta de O{a + 1}") for a in range(m)]
                demanda = [numero(txt_d[b], f"demanda de D{b + 1}") for b in range(n)]
                ss.cm_res = costo_minimo(costos, oferta, demanda, balancear)
            except ProblemaNoBalanceado as e:
                ss.cm_err = f'{e} Marca la casilla "Balancear automáticamente" o corrige los datos.'
            except ValueError as e:
                ss.cm_err = str(e)
        if ss.cm_err:
            st.error(ss.cm_err)

    r = ss.cm_res

    # ---- Paso 2: procedimiento
    with st.container(key="paso2"):
        titulo_paso(2, "Mostrar procedimiento")
        if not r:
            st.markdown('<div class="vacio">Aquí aparecerá el paso a paso cuando presiones <b>Resolver</b>.</div>',
                        unsafe_allow_html=True)
        else:
            if r["aviso"]:
                st.info(r["aviso"])
            filas = [[p["paso"], f'{p["origen"]} → {p["destino"]}', fmt(p["costo"]), fmt(p["cantidad"]), p["nota"]]
                     for p in r["pasos"]]
            st.markdown(tabla_html(["Paso", "Celda", "Costo", "Asignar", "Explicación"], filas, izq=(4,)),
                        unsafe_allow_html=True)

    # ---- Paso 3: resultados
    with st.container(key="paso3"):
        titulo_paso(3, "Resultados")
        if not r:
            st.markdown('<div class="vacio">Todavía no hay resultados.</div>', unsafe_allow_html=True)
        else:
            st.markdown("**Matriz de asignaciones**")
            enc = [""] + r["columnas"]
            filas, resaltadas = [], set()
            for i, nombre in enumerate(r["filas"]):
                fila = [nombre]
                for j in range(len(r["columnas"])):
                    if r["basica"][i][j]:
                        fila.append(fmt(r["asignacion"][i][j]))
                        resaltadas.add((i, j + 1))
                    else:
                        fila.append("–")
                filas.append(fila)
            st.markdown(tabla_html(enc, filas, resaltadas=resaltadas), unsafe_allow_html=True)
            st.markdown(f'<div class="total">Costo total = {esc(fmt(r["costo_total"]))}</div>', unsafe_allow_html=True)
            detalle = " + ".join(f'({fmt(p["cantidad"])}×{fmt(p["costo"])})' for p in r["pasos"] if p["cantidad"] > 0)
            if detalle:
                st.markdown(f'<div class="lista-pasos">CT = <code>{esc(detalle)}</code></div>', unsafe_allow_html=True)
            st.caption(f'Celdas básicas: {r["celdas_basicas"]} (m + n − 1 = {r["celdas_esperadas"]}). '
                       'Es una solución inicial factible; no garantiza ser la óptima (para eso se aplica MODI).')


# ==========================================================================
# RUTA CRÍTICA
# ==========================================================================
def cpm_ejemplo():
    ss.cpm_datos = pd.DataFrame({
        "Actividad": ["A", "B", "C", "D", "E"],
        "Duración": [3.0, 4.0, 2.0, 5.0, 2.0],
        "Predecesoras": ["", "A", "A", "B,C", "D"],
    })
    ss.cpm_n_act = 5
    ss.cpm_version += 1
    ss.cpm_res = ss.cpm_err = None


def cpm_limpiar():
    ss.cpm_datos = None
    ss.cpm_n_act = 3
    ss.cpm_version += 1
    ss.cpm_res = ss.cpm_err = None


def pasos_cpm(r):
    """Cálculos explicados de la pasada hacia adelante y hacia atrás."""
    pred, suc = {}, {}
    for a, b in r["aristas"]:
        pred.setdefault(b, []).append(a)
        suc.setdefault(a, []).append(b)
    f = {x["Actividad"]: x for x in r["filas"]}
    adelante, atras = [], []
    for a in r["orden"]:
        ps = pred.get(a, [])
        if ps:
            lista = ", ".join(f"FT({p})={fmt(f[p]['FT'])}" for p in ps)
            adelante.append(f"IT({a}) = máx({lista}) = {fmt(f[a]['IT'])}  ·  FT({a}) = {fmt(f[a]['IT'])} + {fmt(f[a]['Duración'])} = {fmt(f[a]['FT'])}")
        else:
            adelante.append(f"IT({a}) = 0  ·  FT({a}) = 0 + {fmt(f[a]['Duración'])} = {fmt(f[a]['FT'])}")
    for a in reversed(r["orden"]):
        ss_ = suc.get(a, [])
        if ss_:
            lista = ", ".join(f"ITa({s})={fmt(f[s]['ITa'])}" for s in ss_)
            fta = f"FTa({a}) = mín({lista}) = {fmt(f[a]['FTa'])}"
        else:
            fta = f"FTa({a}) = duración del proyecto = {fmt(f[a]['FTa'])}"
        atras.append(f"{fta}  ·  ITa({a}) = {fmt(f[a]['FTa'])} − {fmt(f[a]['Duración'])} = {fmt(f[a]['ITa'])}  ·  Holgura = {fmt(f[a]['Holgura'])}")
    return adelante, atras


def diagrama_dot(r):
    criticas = {x["Actividad"] for x in r["filas"] if x["Crítica"]}
    aristas_crit = {(a, b) for ruta in r["rutas"] for a, b in zip(ruta, ruta[1:])}
    p = PALETAS.get(ss.paleta, PALETAS["Azul TecNM"])
    dot = ["digraph G { rankdir=LR; bgcolor=transparent; node [shape=box, style=\"rounded,filled\", fontname=Helvetica, fontcolor=white];"]
    for x in r["filas"]:
        es = x["Actividad"] in criticas
        relleno = p["primary"] if es else "#7A8CA8"
        etiqueta = f'{x["Actividad"]}\\n({fmt(x["Duración"])})\\nIT={fmt(x["IT"])}  FT={fmt(x["FT"])}'
        dot.append(f'"{x["Actividad"]}" [label="{etiqueta}", fillcolor="{relleno}", color="{p["accent"] if es else relleno}"];')
    for a, b in r["aristas"]:
        if (a, b) in aristas_crit:
            dot.append(f'"{a}" -> "{b}" [color="{p["accent"]}", penwidth=3];')
        else:
            dot.append(f'"{a}" -> "{b}" [color="#8A97AD"];')
    dot.append("}")
    return "\n".join(dot)


def vista_ruta_critica():
    encabezado("Método de ruta crítica (CPM)",
               "Calcula inicios y fines tempranos y tardíos, las holguras y la ruta que define la duración del proyecto.")

    # ---- Paso 1: datos
    with st.container(key="paso1"):
        titulo_paso(1, "Ingresa los datos a calcular")
        st.caption("Escribe cada actividad, su duración y sus predecesoras separadas por coma (vacío = ninguna).")
        n_act = int(st.number_input("Número de actividades", 1, 30, ss.cpm_n_act, key=f"nact_{ss.cpm_version}"))
        datos = ss.cpm_datos
        v = ss.cpm_version

        def ini(a, col):
            try:
                if datos is not None and a < len(datos):
                    x = datos.iloc[a][col]
                    if col == "Duración":
                        return "" if pd.isna(x) else fmt(float(x))
                    return "" if pd.isna(x) else str(x)
            except Exception:
                pass
            return ""

        anchos = [.9, 1, 2]
        filas_txt = []
        with st.container(key="grid_cpm"):
            enc = st.columns(anchos)
            enc[0].markdown("**Actividad**")
            enc[1].markdown("**Duración**")
            enc[2].markdown("**Predecesoras** (A,B)")
            for a in range(n_act):
                f = st.columns(anchos)
                x1 = f[0].text_input(f"Actividad {a + 1}", value=ini(a, "Actividad"), key=f"a_{v}_{a}",
                                     label_visibility="collapsed", placeholder="Ej. A")
                x2 = f[1].text_input(f"Duración {a + 1}", value=ini(a, "Duración"), key=f"d_{v}_{a}",
                                     label_visibility="collapsed", placeholder="Duración")
                x3 = f[2].text_input(f"Predecesoras {a + 1}", value=ini(a, "Predecesoras"), key=f"p_{v}_{a}",
                                     label_visibility="collapsed", placeholder="Vacío = ninguna")
                filas_txt.append((x1, x2, x3))
        d1, d2, d3, _ = st.columns([1, 1, 1, 2.2])
        calcular = d1.button("Calcular", type="primary", key="cpm_calc")
        d2.button("Ejemplo", key="cpm_ej", on_click=cpm_ejemplo)
        d3.button("Limpiar", key="cpm_lim", on_click=cpm_limpiar)

        if calcular:
            ss.cpm_res = ss.cpm_err = None
            try:
                actividades = []
                for idx, (x1, x2, x3) in enumerate(filas_txt):
                    act, dur, pred = (x1 or "").strip(), (x2 or "").strip(), (x3 or "").strip()
                    if not act and not dur and not pred:
                        continue  # fila vacía
                    if not act:
                        raise ValueError(f"Falta el nombre de la actividad en la fila {idx + 1}.")
                    dur_n = numero(dur, f"duración de la actividad {act}")
                    preds = [p.strip() for p in pred.replace(";", ",").replace(" ", ",").split(",") if p.strip()]
                    actividades.append((act, dur_n, preds))
                ss.cpm_res = ruta_critica(actividades)
            except ValueError as e:
                ss.cpm_err = str(e)
        if ss.cpm_err:
            st.error(ss.cpm_err)

    r = ss.cpm_res

    # ---- Paso 2: procedimiento
    with st.container(key="paso2"):
        titulo_paso(2, "Mostrar procedimiento")
        if not r:
            st.markdown('<div class="vacio">Aquí aparecerá el paso a paso cuando presiones <b>Calcular</b>.</div>',
                        unsafe_allow_html=True)
        else:
            adelante, atras = pasos_cpm(r)
            st.markdown("**Pasada hacia adelante** (IT = máx FT de predecesoras · FT = IT + duración)")
            st.markdown('<div class="lista-pasos">' + "<br>".join(esc(x) for x in adelante) + "</div>",
                        unsafe_allow_html=True)
            st.markdown("**Pasada hacia atrás** (FTa = mín ITa de sucesoras · ITa = FTa − duración · Holgura = ITa − IT)")
            st.markdown('<div class="lista-pasos">' + "<br>".join(esc(x) for x in atras) + "</div>",
                        unsafe_allow_html=True)

    # ---- Paso 3: resultados
    with st.container(key="paso3"):
        titulo_paso(3, "Resultados")
        if not r:
            st.markdown('<div class="vacio">Todavía no hay resultados.</div>', unsafe_allow_html=True)
        else:
            filas = [[x["Actividad"], fmt(x["Duración"]), fmt(x["IT"]), fmt(x["FT"]), fmt(x["ITa"]),
                      fmt(x["FTa"]), fmt(x["Holgura"]), "SÍ" if x["Crítica"] else ""] for x in r["filas"]]
            crit = {i for i, x in enumerate(r["filas"]) if x["Crítica"]}
            st.markdown(tabla_html(["Actividad", "Dur.", "IT", "FT", "ITa", "FTa", "Holgura", "Crítica"], filas,
                                   filas_crit=crit), unsafe_allow_html=True)
            st.markdown(f'<div class="total">Duración total = {esc(fmt(r["duracion"]))}</div>', unsafe_allow_html=True)
            if len(r["rutas"]) == 1:
                st.markdown(f'<div class="ruta">Ruta crítica: {esc(" → ".join(r["rutas"][0]))}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ruta">Rutas críticas ({len(r["rutas"])}):</div>', unsafe_allow_html=True)
                for ruta in r["rutas"]:
                    st.markdown(f'<div class="ruta">• {esc(" → ".join(ruta))}</div>', unsafe_allow_html=True)
            st.markdown("**Diagrama de red** (resaltada, la ruta crítica)")
            st.graphviz_chart(diagrama_dot(r))
            st.caption("IT = inicio temprano, FT = fin temprano, ITa = inicio tardío, FTa = fin tardío. "
                       "Las actividades con holgura 0 son críticas.")


# ==========================================================================
# PROGRAMA PRINCIPAL
# ==========================================================================
def con_panel(vista):
    col_main, col_lado = st.columns([4.6, 1.4])
    with col_main:
        vista()
    with col_lado:
        with st.container(key="panel"):
            panel_usuarios()


def pagina_inicio():
    portada()


def pagina_costo():
    con_panel(vista_costo_minimo)


def pagina_ruta():
    con_panel(vista_ruta_critica)


PAG_INICIO = st.Page(pagina_inicio, title="Inicio", icon="🏠", default=True)
PAG_COSTO = st.Page(pagina_costo, title="Costo mínimo", icon="📦", url_path="costo-minimo")
PAG_RUTA = st.Page(pagina_ruta, title="Ruta crítica", icon="🧭", url_path="ruta-critica")

st.markdown(construir_css(), unsafe_allow_html=True)
if not (ss.get("nombre") or "").strip():
    pantalla_registro()
    st.stop()

pagina = st.navigation([PAG_INICIO, PAG_COSTO, PAG_RUTA], position="hidden")
ss.vista = {"costo-minimo": "costo", "ruta-critica": "ruta"}.get(pagina.url_path, "inicio")
menu_superior()
pagina.run()