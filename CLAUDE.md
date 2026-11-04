# Skill_Buy_Rent — Agente "¿Comprar o alquilar en Lima?"

Agente de Claude Code que ayuda a una persona a decidir si le conviene **comprar** o
**alquilar** una vivienda en Lima (Perú), con datos de mercado, costo de oportunidad
e informe/dashboard final.

## Flujo del agente (orquestado por la skill `buy-vs-rent`)

1. **Intake** — recoger el perfil del usuario (precio objetivo, alquiler, cuota inicial,
   horizonte, distrito). `python .claude/skills/buy-vs-rent/scripts/hl.py intake --plantilla`
2. **market-data** (subagente) — busca avisos de venta y alquiler con la skill
   `peru-listings-search` y llena `data/listings.csv`.
3. **opportunity-cost** (subagente) — estima la rentabilidad alternativa segura
   (depósitos a plazo, fondos mutuos, bonos soberanos) con `peru-safe-investments`.
4. **financial-analysis** (subagente) — corre el modelo (`rent-vs-buy-model`),
   sensibilidad y alquiler de equilibrio, y redacta la explicación.
5. **streamlit-builder** (subagente, opcional) — levanta el dashboard (`streamlit-dashboard`).

## Límite de búsqueda (modo demostración en clase)

- **Máximo 10 fuentes** (URLs distintas abiertas con WebFetch) y **5 búsquedas web** por sesión.
- El límite vive en un solo lugar:
  `.claude/skills/buy-vs-rent/scripts/housing_lima/config/defaults.json` → `busqueda`.
- Lo hace cumplir el hook `.claude/hooks/limit_sources.py` (registrado en
  `.claude/settings.json`): al llegar al tope, Claude Code bloquea la herramienta.
- Para reiniciar el contador: `python .claude/hooks/limit_sources.py --reset`.

## Reglas

- Montos en soles (PEN) salvo que se indique; convertir USD con `tipo_cambio` del config.
- Todo número de mercado debe citar su fuente (columna `url` del CSV).
- El resultado es educativo; no es asesoría financiera personalizada.
