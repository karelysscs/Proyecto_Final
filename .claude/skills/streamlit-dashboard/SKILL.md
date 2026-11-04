---
name: streamlit-dashboard
description: Lanza o modifica el dashboard Streamlit del análisis comprar vs alquilar (housing_lima/app/app.py). Úsala cuando el usuario quiera ver el resultado de forma interactiva, mostrarlo en clase o agregar gráficos.
---

# Dashboard Streamlit

## Lanzar

```
pip install streamlit pandas matplotlib
python .claude/skills/buy-vs-rent/scripts/hl.py app
```

Se abre en http://localhost:8501. En la barra lateral se mueven los supuestos y todo se
recalcula en vivo; abajo se puede subir `data/listings.csv` para ver el resumen por distrito
y cuántas de las 10 fuentes permitidas se usaron.

## Secciones actuales

1. Métricas: recomendación, ventaja de comprar, cuota, alquiler de equilibrio.
2. Línea de patrimonio acumulado (comprar vs alquilar).
3. Tornado de sensibilidad.
4. Matriz de escenarios apreciación × rentabilidad.
5. Datos de mercado subidos por el usuario.

## Al modificar

- No dupliques lógica financiera en la app: importa de `housing_lima` (model, analysis, listings).
- Usa gráficos nativos (`st.line_chart`, `st.bar_chart`) para no sumar dependencias.
- Verifica con `python -m py_compile` y luego lanzando la app.

Ideas para extender: ver `reference.md`.
