# Referencia — fórmulas del modelo

**Tasas mensuales** a partir de tasas efectivas anuales:
`TEM = (1 + TEA)^(1/12) − 1` (igual para rentabilidad y apreciación).

**Préstamo** = precio − cuota inicial − bono.

**Cuota francesa**: `C = P · TEM / (1 − (1 + TEM)^−n)`, con n = plazo × 12.

**Alcabala** = 3 % × max(0, precio − 10 UIT) (si `aplica_alcabala`).

**Gastos de cierre** = precio × `gastos_cierre_pct` + alcabala.

**Costo mensual del comprador** = cuota + desgravamen (saldo × tasa mensual)
+ seguro del inmueble + mantenimiento + predial (sobre el valor actual) + arbitrios.

**Costo mensual del inquilino** = alquiler (sube cada 12 meses según `crecimiento_alquiler`).

**Carteras**: el inquilino arranca con cuota inicial + gastos de cierre invertidos.
Cada mes ambas carteras rinden TEM de inversión, y quien paga menos invierte la diferencia.

**Patrimonio final**
- Comprador = valor × (1 − comisión de venta) − saldo + cartera del comprador
- Inquilino = cartera del inquilino

**Ventaja real** = (comprador − inquilino) / (1 + inflación)^años.

**Alquiler de equilibrio**: bisección sobre `alquiler_mensual` hasta que la ventaja = 0.

## Limitaciones (decirlas en clase)

- Tasa fija: no modela créditos a tasa mixta ni prepagos.
- No incluye mudanzas, mobiliario ni el valor de la estabilidad de ser propietario.
- La apreciación es determinística; el tornado y la matriz de escenarios muestran la incertidumbre.
