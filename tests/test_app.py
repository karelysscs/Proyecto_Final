"""Pruebas del recorrido completo de la app (pytest tests/)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
DISTRITOS = ["Miraflores", "Santiago de Surco", "Jesús María", "San Miguel",
             "Magdalena del Mar", "Pueblo Libre", "Lince", "La Victoria", "San Borja"]


def boton(at, texto):
    return next(b for b in at.button if b.label == texto)


def distrito(at, d):
    return next(b for b in at.button if b.key == f"btn_{d}")


def iniciar():
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception
    return at


def test_portada():
    at = iniciar()
    html = " ".join(m.value for m in at.markdown)
    assert "Techito" in html and "¿Compro o alquilo?" in html


@pytest.mark.parametrize("distrito_", DISTRITOS)
def test_recorrido_por_distrito(distrito_):
    at = iniciar()
    distrito(at, distrito_).click().run()
    assert not at.exception
    assert at.session_state.paso == 2
    boton(at, "Ver qué me conviene →").click().run()
    assert not at.exception
    assert at.session_state.paso == 3
    chat = " ".join(m.value for m in at.markdown)
    assert "COMPRAR" in chat or "ALQUILAR" in chat


def test_preguntas_a_techi():
    at = iniciar()
    distrito(at, "Santiago de Surco").click().run()
    boton(at, "Ver qué me conviene →").click().run()
    for b in [b for b in at.button if b.key and b.key.startswith("q_")]:
        b.click().run()
        assert not at.exception, b.key


def test_depa_propio_en_dolares():
    at = iniciar()
    distrito(at, "San Miguel").click().run()
    at.session_state.modo_depa = "✍️ Tengo mi propio depa"
    at.run()
    at.number_input(key="mi_monto").set_value(120_000).run()
    at.radio(key="mi_moneda").set_value("US$").run()
    assert not at.exception
    boton(at, "Ver qué me conviene →").click().run()
    assert not at.exception and at.session_state.paso == 3
