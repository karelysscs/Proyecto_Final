# Investigación de usuarios — perfiles hipotéticos

> **Aviso de transparencia:** estos tres perfiles son **hipotéticos**. No son conversaciones
> con personas reales. Los construí como *user personas* para guiar el diseño del producto
> por falta de tiempo en el sprint. Las cifras son ilustrativas y coherentes con los valores
> de referencia del modelo (`config/defaults.json`); los precios de mercado reales del producto
> salen de `data/listings.csv`, con su URL de fuente.
>
> Próximo paso: validar cada perfil con al menos una persona real que encaje en él.

| # | Perfil | Distrito | Situación | Pregunta clave |
|---|--------|----------|-----------|----------------|
| 1 | Joven profesional que alquila | Santiago de Surco | Alquila, ahorra para la inicial | ¿Sigo alquilando o compro ya? |
| 2 | Pareja con un hijo | San Miguel / Jesús María | Alquila, con oferta de crédito del banco | ¿Me alcanza y me conviene la hipoteca? |
| 3 | Profesional independiente con ahorros | Miraflores | Tiene el dinero invertido en un depósito a plazo | ¿Compro al contado o dejo la plata invertida? |

## Patrones comunes (hipótesis a validar)
1. **Deciden "a ojo" o con un Excel incompleto:** comparan la cuota del banco con el alquiler
   y no cuentan alcabala, mantenimiento, predial ni el costo de oportunidad de la inicial.
2. **La información está dispersa:** precios en Urbania/Adondevivir, tasas en cada banco,
   rentabilidad de depósitos en otra web. Nadie la junta en un solo número.
3. **La fuente de consejo tiene conflicto de interés:** el banco y la inmobiliaria ganan si compras.
4. **Disposición a pagar baja para el usuario final** → el modelo de negocio debe apoyarse en
   bancos/inmobiliarias (leads calificados) o en un informe premium de bajo precio.

## Guía de entrevista para la validación
Para conversar 10–15 minutos (en persona o por WhatsApp) con alguien que encaje en cada perfil:

1. ¿Alquilas actualmente? ¿Cuánto pagas y en qué distrito?
2. ¿Has pensado en comprar? ¿Qué te frena?
3. La última vez que lo pensaste, ¿cómo hiciste la cuenta? (banco, Excel, familia, a ojo)
4. ¿Sabías de la alcabala y de lo que rinde tu inicial en un depósito si no compras?
5. ¿Qué te haría confiar en una recomendación de "compra" o "alquila"?
6. ¿Pagarías S/ 19 por un informe con tu caso para llevar al banco? ¿Por qué sí o no?
7. Después de usar Techito Propio: ¿qué entendiste? ¿qué te faltó?
