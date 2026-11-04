# Referencia — buy-vs-rent

## Estructura del motor (`scripts/housing_lima/`)

| Módulo | Rol |
|---|---|
| `model.py` | `Perfil` (dataclass) y `simular()` mes a mes |
| `analysis.py` | `sensibilidad()`, `alquiler_equilibrio()`, `escenarios()` |
| `explain.py` | `explicar()` → informe Markdown en español |
| `listings.py` | Lectura/validación de `listings.csv`, resumen por distrito, límite de fuentes |
| `intake.py` | Carga perfil + defaults, valida contra el schema |
| `config/defaults.json` | Supuestos por defecto, tipo de cambio, UIT y **límite de búsqueda** |
| `schemas/` | JSON Schema del perfil y de un aviso |
| `app/app.py` | Dashboard Streamlit |

## Supuestos peruanos por defecto (verificar)

- **TEA hipotecaria** 8.8 % (rango bancario típico 7.5–10.5 %; ver SBS).
- **Cuota inicial** mínima 7.5 % con Fondo MiVivienda, 10–20 % en banca regular.
- **Alcabala** 3 % sobre (precio − 10 UIT), la paga el comprador; no aplica en la
  primera venta de inmueble nuevo (ahí hay IGV incluido). Desactívala con
  `"aplica_alcabala": false`.
- **Gastos de cierre** (notaría, SUNARP, tasación) ≈ 1.5 % del precio.
- **Predial** progresivo 0.2–1 % del autovalúo; se usa 0.4 % del valor como aproximación.
- **Seguro de desgravamen** ≈ 0.028 % mensual sobre el saldo; **seguro del inmueble** ≈ 0.03 % anual.
- **Comisión de venta** al final del horizonte: 3 %.
- **Inflación** meta BCRP 2 % (rango 1–3 %).

## Lógica de comparación

Ambos parten con el mismo dinero. El comprador usa la cuota inicial + gastos de cierre;
el inquilino invierte ese mismo monto a `rentabilidad_alternativa`. Cada mes, quien
tiene el menor desembolso invierte la diferencia. Al final del horizonte:

- Patrimonio comprador = valor × (1 − comisión) − saldo de deuda + su cartera
- Patrimonio inquilino = su cartera

También se reportan en soles reales (descontando inflación).
