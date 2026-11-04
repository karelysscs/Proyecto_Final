---
name: peru-listings-search
description: Busca avisos de venta y alquiler de vivienda en Lima/Perú (Urbania, Adondevivir, Nexo Inmobiliario, BCRP, etc.) y los guarda en un CSV normalizado. Úsala cuando se necesiten precios por m² o alquileres de mercado por distrito. Modo clase - máximo 10 fuentes y 5 búsquedas.
---

# Búsqueda de avisos — Perú

## Presupuesto de búsqueda (modo clase)

- **Máximo 10 fuentes** (URLs distintas con WebFetch) y **5 búsquedas** (WebSearch).
- El hook `.claude/hooks/limit_sources.py` bloquea la herramienta al llegar al tope.
  Si te bloquea, **no insistas**: cierra el CSV con lo que tengas.
- Planifica antes de buscar. Reparto sugerido de las 10 fuentes:
  - 1 fuente agregada de precios (p. ej. reporte de precios por m² del BCRP).
  - 4–5 páginas de resultados de **venta** del distrito objetivo.
  - 4–5 páginas de resultados de **alquiler** del mismo distrito.
- Prefiere páginas de listado (muchos avisos por URL) antes que avisos individuales:
  así una sola fuente te da varias filas.

## Pasos

1. Copia la plantilla: `listings_template.csv` → `data/listings.csv`.
2. Haz como máximo 5 búsquedas, p. ej. `departamento venta Santiago de Surco 90 m2`.
3. Abre como máximo 10 URLs y extrae de cada una todas las filas que puedas
   (precio, moneda, m², dormitorios, distrito). Usa la **misma URL** en todas las filas
   que salgan de esa página.
4. Valida: `python .claude/skills/peru-listings-search/scripts/check_listings.py data/listings.csv`
5. Reporta: número de filas de venta y de alquiler, fuentes usadas (n/10) y limitaciones.

## Reglas

- No inventes avisos. Si un dato no aparece, deja la celda vacía.
- `operacion` es `venta` o `alquiler`; `moneda` es `PEN` o `USD` (no conviertas tú).
- `fecha_consulta` en formato AAAA-MM-DD.

Portales y tips: ver `reference.md`.
