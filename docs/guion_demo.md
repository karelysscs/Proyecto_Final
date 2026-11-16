# Guion de la demo (3 minutos) · Techito Propio

**Antes de empezar:** abre https://techito-propio.streamlit.app 5 minutos antes. Si dice que la app está dormida,
dale a "Yes, get this app back up" y espera ~1 minuto. Ten el video de respaldo abierto en otra pestaña.

---

**0:00–0:30 · Problema**
"Si alquilas en Lima, en algún momento te preguntas: ¿compro o sigo alquilando? Hoy lo decides a ojo, con el
simulador del banco —que quiere que compres— o con un Excel que se olvida de la alcabala y de lo que rinde tu
inicial en un depósito. Equivocarte cuesta decenas de miles de soles. Por eso creé **Techito Propio**."

**0:30–2:30 · Demo en vivo**

1. **Paso 1, dónde vivir (20 s).** "Cada círculo del mapa es un distrito: su tamaño es el precio por m², calculado
   con 216 avisos reales de Urbania en 9 distritos. Las tarjetas van del más accesible al más caro y me adelantan dónde suele convenir comprar y dónde alquilar.
   Elijo **Surco**."
2. **Paso 2, mi depa (30 s).** "Estos son avisos reales en venta. Elijo este de **82 m² a S/ 391 mil**; con
   'Ver ↗' se abre el aviso real. Alquilar uno parecido cuesta **S/ 2,800 al mes**. La tasa, **7.47 %**, viene en
   vivo del Banco Central de Reserva. Pongo mi sueldo: **S/ 8,000**."
   *(Opcional, si vas bien de tiempo: "Y si ya tengo un depa en mente, lo ingreso aquí, en soles o dólares".)*
3. **Paso 3, mi asesora (40 s).** "Techi, mi asesora, me dice: **COMPRAR**, con **S/ 153 mil más** de patrimonio
   en 10 años. Me explica la cuota de S/ 2,469 y la alcabala. Y algo que ningún banco te dice: esa cuota es el
   **31 % de mi sueldo, estoy al límite**; con mi ingreso puedo apuntar a un depa de hasta S/ 380 mil."
4. **Preguntas (20 s).** "Le pregunto: **¿y si sube la tasa 1 punto?**" *(clic)* "Recalcula al instante."
5. **Viaja al futuro (15 s).** "Muevo el año: en **2036**, comprando tendría **S/ 315 mil**; alquilando e
   invirtiendo, S/ 162 mil. Y puedo **descargar mi informe** para llevarlo al banco."
6. **El giro (15 s).** "Pero si vuelvo y elijo **San Miguel**, la respuesta cambia a **ALQUILAR**: ahí el alquiler
   es barato frente al precio. Ningún banco te va a decir eso."

**2:30–3:00 · Negocio**
"Es gratis para el usuario. Ganamos con el **informe premium a S/ 19** y con **leads calificados** a bancos e
inmobiliarias a S/ 40, solo con consentimiento. Nuestro costo por usuario es casi cero porque el cálculo no usa
un LLM. Lo siguiente: más distritos y actualización automática semanal de precios."

> Cronometra el ensayo: si pasas de 2:30 en la demo, salta el paso 6 o el 5.

---

## Preguntas probables

- **"¿Es realista el cálculo?"** "El método compara patrimonio, no solo cuota contra alquiler, e incluye alcabala,
  cierre, seguros, mantenimiento y lo que rinde tu inicial invertida. El supuesto que más pesa es cuánto sube el
  depa (3 % al año). Si no subiera nada, en este caso comprar igual gana por S/ 33 mil; si todo sale mal —tasa
  9.5 %, sin apreciación fuerte— conviene alquilar. Por eso Techi te deja preguntar '¿y si el depa no sube?'."
- **"¿De dónde salen los datos?"** "216 avisos de Urbania de esta semana (12 de venta y 12 de alquiler en cada uno de los 9 distritos)
  y la API pública del BCRP para la tasa hipotecaria, los depósitos y el tipo de cambio."
- **"¿Hablaste con usuarios?"** "Armé 3 perfiles de usuario, marcados como hipotéticos en el repo; el siguiente
  paso es validarlos con entrevistas reales."
- **"¿Dónde está el modelo?"** `simular()` en `.claude/skills/buy-vs-rent/scripts/housing_lima/model.py`.
