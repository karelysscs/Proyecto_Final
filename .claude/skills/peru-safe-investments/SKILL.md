---
name: peru-safe-investments
description: Estima el costo de oportunidad del dinero (cuota inicial y ahorro mensual) con instrumentos de bajo riesgo en Perú - depósitos a plazo, fondos mutuos de renta fija, bonos soberanos, Letras del Tesoro. Úsala para fijar la "rentabilidad_alternativa" del modelo comprar vs alquilar.
---

# Inversiones seguras en Perú — costo de oportunidad

## Pasos

1. Si hay presupuesto de búsqueda disponible (comparte el tope de **10 fuentes / 5 búsquedas**
   con el resto del agente), actualiza tasas con 1–2 fuentes como máximo
   (SBS: tasas pasivas promedio; BCRP: rendimiento de bonos soberanos). Si no, usa las tasas por defecto.
2. Calcula:
   ```
   python .claude/skills/peru-safe-investments/scripts/index_returns.py --horizonte 10
   ```
   Para sobrescribir tasas: `--tasa deposito_plazo_1a=0.05 --tasa bono_soberano_10a=0.065`
3. Toma el valor `tasa_recomendada` (nominal anual, después de impuestos) y escríbelo en
   `rentabilidad_alternativa` de `data/perfil.json`.
4. Explica en 2–3 líneas por qué elegiste esa tasa y su rango (mín.–máx.).

## Reglas

- Usa rendimientos **después del impuesto a la renta de 5 %** sobre ganancias de capital
  e intereses de personas naturales (los depósitos tienen exoneraciones parciales: ver `reference.md`).
- No recomiendes productos o entidades concretas; habla de tipos de instrumento.
