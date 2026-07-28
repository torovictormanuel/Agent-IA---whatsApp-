# CONTEXTO DE DOMINIO: SECTOR INMOBILIARIO EN ARGENTINA

Este documento define la lógica de negocio, reglas financieras, legales y
terminología del mercado inmobiliario argentino para la configuración de un
agente conversacional. Vive en `/knowledge` porque es exactamente el tipo de
archivo que la Fase 2 de `CLAUDE.md` (Pregunta 7) espera que el usuario
coloque aquí — Claude Code lo lee y lo incorpora al system prompt.

---

## 1. TERMINOLOGÍA Y CONCEPTOS CLAVE

* **Tipologías:**
  * **PH (Propiedad Horizontal):** Viviendas divididas bajo régimen de propiedad horizontal pero habitualmente sin expensas o con expensas muy bajas, sin ascensor ni grandes áreas comunes.
  * **Departamento / Piso / Semipiso:** "Piso" indica un departamento por planta; "Semipiso", dos por planta.
  * **Ambientes:** En Argentina las propiedades se miden por "ambientes" (ej. 2 ambientes = 1 dormitorio + 1 living/comedor). La cocina y el baño no cuentan como ambientes.
  * **Studio / Monoambiente:** Propiedad de un solo espacio integrable.

* **Superficies:**
  * **Cubierta (m²):** Espacio bajo techo.
  * **Semicubierta (m²):** Balcones techados, galerías.
  * **Descubierta (m²):** Patios, terrazas al aire libre.
  * **M² Computable / Ponderado:** Varía según la tasación, pero estándar habitual: 100% Cubierta + 50% Semicubierta + 10% a 30% Descubierta.

* **Gastos y Transacción:**
  * **Expensas Ordinarias:** Gastos habituales de mantenimiento del edificio (habitualmente a cargo del inquilino).
  * **Expensas Extraordinarias:** Fondos de reserva o arreglos estructurales del edificio (a cargo del propietario).
  * **Reserva:** Entrega de dinero para congelar la oferta y elevar la propuesta formal al propietario.
  * **Boleto de Compraventa:** Contrato privado previo a la escritura donde se compromete la venta y se suele abonar un porcentaje (ej. 30%-50%).
  * **Escritura Traslativa de Dominio:** Acto formal ante escribano público que otorga la titularidad.

---

## 2. ASPECTOS LEGALES Y CONTRATACIÓN (Post-DNU 70/2023)

* **Alquileres Habitacionales:**
  * **Moneda:** Libre acuerdo entre partes (USD, ARS, etc.).
  * **Plazo de Contrato:** Libre acuerdo. Si no se especifica, el plazo legal supletorio es de 2 años.
  * **Ajuste de Precio:** Libre acuerdo en periodicidad (mensual, cuatrimestral, semestral) e índice (IPC - Índice de Precios al Consumidor, ICL - Índice para Contratos de Alquiler, CAC - Cámara Argentina de la Construcción).
  * **Garantías Habituales:**
    * Garantía propietaria (inmueble de familiar directo, preferentemente en la misma jurisdicción).
    * Seguros de caución (Finaer, Premium Group, GaranteCO, Banco Ciudad).
    * Recibos de sueldo / Demostración de ingresos (habitualmente se pide que el alquiler no supere el 30%-35% del ingreso).

---

## 3. VALORACIÓN Y DINÁMICA DE PRECIOS

* **Moneda de Operación:**
  * **Venta:** Prácticamente 100% dolarizada (USD billete físico en mano o transferencia MEP según acuerdos).
  * **Alquileres:** Mixto (ARS ajustados por inflación o USD en zonas de alta demanda/turísticas).

* **Indicadores de Tasación Promedio (Referenciales CABA - ajustar según zona/barrio):**
  * El valor del m² varía drásticamente según el barrio (ej. Puerto Madero, Palermo, Recoleta vs. Flores, Balvanera, Lugano).
  * Rango de margen de negociación habitual en compraventa: 5% al 10% de contraoferta sobre precio publicado.

---

## 4. ROL Y TONO DEL AGENTE

* **Perfil:** Asesor inmobiliario profesional, empático, conocedor de la realidad económica local, claro y directo.
* **Manejo de Dudas:** Al responder sobre costos, especificar siempre si los valores son en USD o Pesos Argentinos (ARS) y aclarar qué tipo de cotización o ajuste aplica cuando sea relevante.
