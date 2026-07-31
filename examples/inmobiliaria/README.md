# Ejemplo: Agente de WhatsApp para Inmobiliaria

Implementación de referencia, completa y funcional, generada a partir de
`CLAUDE.md`. Sirve para probar el sistema base sin pasar por la entrevista
completa de `/build-agent`, y como plantilla para adaptar a otro rubro.

## Qué incluye

- Adaptado al **mercado inmobiliario argentino**: terminología (PH, ambientes,
  m² cubierta/semicubierta/descubierta), moneda dual USD/ARS, expensas, y
  reglas legales post-DNU 70/2023 — ver `knowledge/contexto_mercado_ar.md`,
  incorporado completo al system prompt en `config/prompts.yaml`
- Búsqueda de propiedades por zona, tipo, operación, moneda, precio y
  ambientes (`agent/tools.py` + `config/propiedades.yaml`, 6 propiedades
  de ejemplo en CABA/GBA: Palermo, Villa Crespo, Puerto Madero, Recoleta,
  Nordelta, Flores)
- Agenda de visitas y consulta de visitas propias
- Registro de leads para el equipo de ventas
- Escalamiento a un asesor humano
- Tool-calling real: el modelo decide cuándo llamar cada herramienta
  (`agent/brain.py`)
- Validación de firma de webhook para Twilio y Meta
- Idempotencia: reintentos del proveedor no duplican respuestas
- Modelo configurable via `ANTHROPIC_MODEL` (Haiku para probar sin quemar
  crédito, Sonnet para producción — ver `.env.example`)

## Probar en 3 pasos (sin WhatsApp)

```bash
cd examples/inmobiliaria
python3 -m venv .venv && source .venv/bin/activate   # o .venv\Scripts\activate en Windows
pip install -r requirements.txt
cp .env.example .env
# Edita .env y pon tu ANTHROPIC_API_KEY
python tests/test_local.py
```

Prueba escribiendo cosas como:

```
Busco un depto en alquiler en Villa Crespo
Cuanto sale la P001?
Quiero agendar una visita a P001 el 2026-08-10 a las 16:00
Me interesa, me llamo Ana y ando buscando algo en Palermo hasta 200 mil dolares
Quiero hablar con alguien para negociar el precio
```

## Probar gratis con AWS Bedrock (en vez de gastar crédito de Anthropic)

Si tu cuenta de AWS es nueva (creada después de julio 2025), AWS te da $200
de crédito que cubren Bedrock — podés probar el agente completo con Claude
real sin tocar tu crédito de la cuenta de Anthropic:

```bash
# En .env:
LLM_PROVIDER=bedrock
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
ANTHROPIC_MODEL=us.anthropic.claude-haiku-4-5-...-v1:0   # copiado de tu consola de Bedrock
```

Pasos: cuenta en [aws.amazon.com/free](https://aws.amazon.com/free) → en la
consola, Bedrock → Model access → habilitar Anthropic → copiar el
"inference profile ID" exacto desde Model catalog (ese ID cambia por
región, no es el mismo string que `claude-sonnet-5`). El resto del código
no cambia — `agent/brain.py` detecta `LLM_PROVIDER` y arma el cliente que
corresponda.

## Conectar a WhatsApp real

1. Completa el resto de `.env` (`WHATSAPP_PROVIDER`, credenciales del
   proveedor elegido, y `META_APP_SECRET` si usas Meta — necesario para
   validar la firma del webhook).
2. Arranca el servidor: `uvicorn agent.main:app --reload --port 8000`
3. Expón el puerto públicamente (ngrok para pruebas, Railway para producción)
   y configura la URL `/webhook` en tu proveedor.

## Adaptar a otro rubro

Solo se reescribe `agent/tools.py` (y, si hace falta persistencia propia, se
agregan tablas a `agent/memory.py`). `agent/brain.py`, `agent/main.py` y
`agent/providers/` no cambian — son el motor genérico. Ver `CLAUDE.md` en la
raíz del repo, sección 3.7, para el contrato `TOOLS` / `EJECUTAR_TOOL`.

## ¿Vas a atender a varios clientes con esto?

Este ejemplo es single-tenant: un deploy, una base de datos, un negocio. Es
lo correcto mientras manejás pocos clientes. Si el plan es vender esto a
varias inmobiliarias/negocios desde una sola infraestructura, mirá
[`examples/saas-multitenant/`](../saas-multitenant/) — la misma lógica de
este ejemplo, pero servida desde un único servidor con `negocio_id` aislando
los datos de cada cliente.
