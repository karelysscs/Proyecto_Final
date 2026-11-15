# Arquitectura — Techito Propio

```mermaid
flowchart TB
    subgraph Backoffice["Backoffice (Claude Code, offline)"]
        AG[Agente market-data<br/>skill peru-listings-search] -->|navegador / WebFetch<br/>tope: hook limit_sources.py| URB[(Urbania)]
        AG --> CSV[data/listings.csv<br/>precio, m², distrito, URL]
    end
    subgraph App["App pública (Streamlit Community Cloud)"]
        UI[streamlit_app.py<br/>entradas del usuario]
        L[listings.py<br/>mediana S/ por m² por distrito]
        B[bcrp.py<br/>API BCRP con caché de 6 h]
        M[model.py<br/>simulación mensual]
        A[analysis.py<br/>equilibrio y sensibilidad]
        MAP[Folium<br/>mapa de 4 distritos]
    end
    CSV --> L
    BCRP[(API BCRP<br/>PN07848NM · PN07815NM · PD04640PD)] --> B
    UI --> M
    L --> M
    B --> M
    M --> A
    M --> MAP
    A --> UI
    MAP --> UI
```

## Flujo de una consulta
1. El usuario elige distrito, m², cuota inicial, horizonte y plazo.
2. `listings.py` calcula precio = mediana S/ por m² de venta × m², y alquiler = mediana S/ por m² de alquiler × m².
3. `bcrp.py` trae la TEA hipotecaria y la tasa de depósitos a plazo (costo de oportunidad).
4. `model.py` simula mes a mes los dos caminos: comprar (cuota, seguros, predial, mantenimiento, alcabala, venta al final) y alquilar e invertir la diferencia.
5. La app muestra la recomendación, el patrimonio, el mapa comparativo, la sensibilidad y los avisos fuente.
