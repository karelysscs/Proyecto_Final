# Skill_Buy_Rent

Agente de Claude Code que responde **"¿me conviene comprar o alquilar vivienda en Lima?"**
combinando datos de mercado, costo de oportunidad y un modelo financiero.

> Modo clase: la búsqueda web está limitada a **10 fuentes** y **5 búsquedas** por sesión.

## Estructura

```
Skill_Buy_Rent/
├── CLAUDE.md                     instrucciones del orquestador
├── .claude/
│   ├── settings.json             registra el hook que limita las fuentes
│   ├── hooks/limit_sources.py    bloquea WebFetch/WebSearch al pasar el tope
│   ├── skills/
│   │   ├── buy-vs-rent/          SKILL.md, reference.md, scripts/hl.py (launcher)
│   │   │   └── scripts/housing_lima/   motor: model, explain, analysis, listings, intake, cli, schemas/, config/, app/
│   │   ├── peru-listings-search/ SKILL.md, reference.md, listings_template.csv, scripts/check_listings.py
│   │   ├── peru-safe-investments/SKILL.md, reference.md, scripts/index_returns.py
│   │   ├── rent-vs-buy-model/    SKILL.md, reference.md
│   │   └── streamlit-dashboard/  SKILL.md, reference.md
│   └── agents/                   market-data, opportunity-cost, financial-analysis, streamlit-builder
└── data/                         perfil.json, listings.csv, informe.md (salidas)
```

## Uso con Claude Code

Abre la carpeta en Claude Code y pide, por ejemplo:

> ¿Me conviene comprar un depa de 90 m² en Santiago de Surco o seguir alquilando? Tengo 20 % de inicial y pienso quedarme 10 años.

## Uso directo del motor (sin agente)

```bash
python .claude/skills/buy-vs-rent/scripts/hl.py intake --plantilla > data/perfil.json
python .claude/skills/buy-vs-rent/scripts/hl.py run data/perfil.json
python .claude/skills/buy-vs-rent/scripts/hl.py sensitivity data/perfil.json
python .claude/skills/buy-vs-rent/scripts/hl.py explain data/perfil.json
python .claude/skills/peru-safe-investments/scripts/index_returns.py --horizonte 10
pip install streamlit pandas matplotlib
python .claude/skills/buy-vs-rent/scripts/hl.py app
python .claude/skills/buy-vs-rent/scripts/hl.py resultados
```

`hl.py resultados` abre el dashboard con lo que encontró el agente: la bitácora de
búsquedas y fuentes (con su cupo de 10), los avisos, el resumen por distrito y la
recomendación que sale de esos datos.

## Cambiar el límite de fuentes

Edita `busqueda.max_fuentes` y `busqueda.max_busquedas` en
`.claude/skills/buy-vs-rent/scripts/housing_lima/config/defaults.json`.
Reinicia el contador con `python .claude/hooks/limit_sources.py --reset`.

Ejercicio educativo; no es asesoría financiera.
