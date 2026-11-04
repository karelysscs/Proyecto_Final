# Referencia — peru-safe-investments

Tasas por defecto (nominales anuales en PEN, referenciales nov-2026, **verificar**):

| Instrumento | Tasa | Liquidez | Impuesto | Notas |
|---|---|---|---|---|
| Depósito a plazo 1 año | 4.5 % | Baja | 5 % sobre intereses (exoneración parcial hasta 5 UIT/año) | Fondo de Seguro de Depósitos hasta ~S/ 125 mil |
| Fondo mutuo renta fija / corto plazo | 4.8 % | Alta | 5 % | Rentabilidad variable, no garantizada |
| Letras del Tesoro (1 año) | 4.4 % | Media | 5 % | Riesgo soberano |
| Bono soberano Perú 10 años | 6.3 % | Media | 5 % | Riesgo de precio si se vende antes |
| Cuenta de ahorro | 1.5 % | Alta | exonerada | Solo para el fondo de emergencia |

## Cómo se arma la tasa recomendada

`index_returns.py` aplica el impuesto, calcula la tasa real con la inflación meta
y pondera por horizonte:

- Horizonte ≤ 3 años → depósitos y fondos de corto plazo.
- Horizonte 4–9 años → mezcla de depósitos, fondos y bonos.
- Horizonte ≥ 10 años → mayor peso a bonos soberanos.

Fuentes para actualizar: SBS (tasas pasivas promedio del sistema), BCRP (curva de
rendimientos soberanos), SMV (rentabilidad de fondos mutuos).
