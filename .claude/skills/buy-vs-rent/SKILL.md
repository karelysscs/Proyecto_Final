---
name: buy-vs-rent
description: Orquesta la decisión "¿comprar o alquilar vivienda en Lima/Perú?". Úsala cuando el usuario pregunte si le conviene comprar o alquilar, quiera comparar hipoteca vs alquiler, o pida un análisis inmobiliario personal en Perú. Coordina intake, datos de mercado (máx. 10 fuentes), costo de oportunidad, modelo financiero y dashboard.
---

# Buy vs Rent — Lima

Eres el orquestador. El motor de cálculo está en `scripts/housing_lima/` y se llama
siempre a través del launcher `scripts/hl.py` (no importes módulos sueltos).

## Pasos

1. **Intake.** Pide al usuario lo mínimo: precio de la vivienda (o distrito + m²),
   alquiler equivalente, cuota inicial, horizonte en años. Genera la plantilla con
   `python .claude/skills/buy-vs-rent/scripts/hl.py intake --plantilla > data/perfil.json`,
   complétala y valida con `hl.py intake data/perfil.json`.
2. **Datos de mercado.** Delega al subagente `market-data` (skill `peru-listings-search`).
   **Tope: 10 fuentes y 5 búsquedas** — el hook las bloquea al llegar al límite.
   Resultado: `data/listings.csv`. Resúmelo con `hl.py listings data/listings.csv`.
3. **Costo de oportunidad.** Delega a `opportunity-cost` (skill `peru-safe-investments`)
   y escribe la tasa resultante en `rentabilidad_alternativa` del perfil.
4. **Análisis.** Delega a `financial-analysis`: `hl.py run`, `hl.py sensitivity`,
   `hl.py explain` sobre `data/perfil.json`.
5. **Dashboard (opcional).** Delega a `streamlit-builder`: `hl.py app`.

## Comandos del launcher

| Comando | Qué hace |
|---|---|
| `hl.py intake --plantilla` | Imprime un perfil de ejemplo en JSON |
| `hl.py intake perfil.json` | Valida el perfil contra `schemas/perfil.schema.json` |
| `hl.py run perfil.json [--json]` | Simulación año a año comprar vs alquilar |
| `hl.py sensitivity perfil.json` | Tornado de sensibilidad + alquiler de equilibrio |
| `hl.py explain perfil.json` | Informe en español (Markdown) |
| `hl.py listings listings.csv` | Resumen por distrito y control del límite de fuentes |
| `hl.py app` | Lanza el dashboard Streamlit |

Detalles de supuestos y fórmulas: ver `reference.md`.

## Reglas

- Cita la fuente de cada dato de mercado. Si el hook bloquea más búsquedas, trabaja
  con lo que ya tienes y dilo en el informe.
- Termina siempre con: recomendación, año de equilibrio, 3 supuestos que más pesan y
  la advertencia de que es un ejercicio educativo.
