# Referencia — peru-listings-search

## Fuentes útiles

| Fuente | Qué aporta | Nota |
|---|---|---|
| urbania.pe | Avisos de venta y alquiler | Listados por distrito; precios en USD y PEN |
| adondevivir.com | Avisos de venta y alquiler | Mismo grupo que Urbania |
| nexoinmobiliario.pe | Proyectos nuevos (primera venta) | Útil para ver precio de estreno; sin alcabala |
| bcrp.gob.pe (estadísticas) | Precio promedio por m² por distrito | Serie trimestral, buena referencia agregada |
| ASEI / CAPECO | Informes del mercado de edificaciones | Contexto de oferta y demanda |

## Qué guardar

- Una fila por aviso. Si un listado muestra 20 avisos, puedes guardar los 20 con la misma URL:
  cuenta como **una** fuente.
- Para el BCRP, guarda una fila por distrito con `notas = "promedio BCRP"`.

## Errores comunes

- Mezclar m² techados y m² totales: usa área techada si está disponible y anótalo en `notas`.
- Avisos duplicados entre Urbania y Adondevivir: si el título y el precio coinciden, guarda solo uno.
- Alquileres "con mantenimiento incluido": anótalo en `notas`.
