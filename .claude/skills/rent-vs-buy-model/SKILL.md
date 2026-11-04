---
name: rent-vs-buy-model
description: Metodología del modelo financiero comprar vs alquilar (cuota francesa con TEA, alcabala, seguros, predial, costo de oportunidad, patrimonio neto, año y alquiler de equilibrio, sensibilidad). Úsala al correr, interpretar o ajustar el modelo de housing_lima.
---

# Modelo comprar vs alquilar

El modelo se ejecuta con el launcher de `buy-vs-rent`; esta skill explica **cómo
usarlo e interpretarlo** correctamente.

## Ejecución

```
python .claude/skills/buy-vs-rent/scripts/hl.py run data/perfil.json
python .claude/skills/buy-vs-rent/scripts/hl.py sensitivity data/perfil.json
python .claude/skills/buy-vs-rent/scripts/hl.py explain data/perfil.json --listings data/listings.csv
```

## Cómo calibrar el perfil con los datos de mercado

- `precio_vivienda` = mediana venta S/ por m² del distrito × m² del usuario.
- `alquiler_mensual` = mediana alquiler S/ por m² × m² del usuario.
- `rentabilidad_alternativa` = `tasa_recomendada` de `peru-safe-investments`.
- `apreciacion_anual`: si no hay datos, usa 2–4 % nominal y dilo como supuesto.

## Interpretación

1. **Recomendación** = signo de la ventaja de comprar al final del horizonte.
2. **Año de equilibrio**: primer año en que comprar supera a alquilar. Si no existe,
   alquilar gana en todo el horizonte.
3. **Alquiler de equilibrio**: alquiler a partir del cual comprar conviene.
4. **Tornado**: las 3 variables con mayor rango son las que hay que discutir con el usuario.
5. **PER** (precio / alquiler anual): > 20 suele favorecer alquilar; < 15, comprar.

Fórmulas: ver `reference.md`.
