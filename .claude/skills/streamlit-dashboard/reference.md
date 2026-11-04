# Referencia — streamlit-dashboard

## API usada

| Elemento | Para qué |
|---|---|
| `st.sidebar` + `st.slider` / `st.number_input` | Supuestos del perfil |
| `st.metric` | KPIs principales |
| `st.line_chart(df)` | Patrimonio por año (índice = año) |
| `st.bar_chart(df, horizontal=True)` | Tornado (requiere Streamlit ≥ 1.36) |
| `df.style.background_gradient` | Matriz de escenarios (requiere matplotlib) |
| `st.file_uploader` | Subir `listings.csv` |

## Extensiones sugeridas

- Pestaña "Mapa" con precio por m² por distrito (`st.map` necesita lat/lon por distrito).
- Botón para descargar el informe de `explain.py` (`st.download_button`).
- Comparar dos distritos lado a lado con `st.columns`.
- Cachear cálculos pesados con `@st.cache_data`.
