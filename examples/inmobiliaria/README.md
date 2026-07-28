# Ejemplo: Agente de WhatsApp para Inmobiliaria

Implementación de referencia, completa y funcional, generada a partir de
`CLAUDE.md`. Sirve para probar el sistema base sin pasar por la entrevista
completa de `/build-agent`, y como plantilla para adaptar a otro rubro.

## Qué incluye

- Búsqueda de propiedades por zona, tipo, operación, precio y habitaciones
  (`agent/tools.py` + `config/propiedades.yaml`, 6 propiedades de ejemplo)
- Agenda de visitas y consulta de visitas propias
- Registro de leads para el equipo de ventas
- Escalamiento a un asesor humano
- Tool-calling real: el modelo decide cuándo llamar cada herramienta
  (`agent/brain.py`)
- Validación de firma de webhook para Twilio y Meta
- Idempotencia: reintentos del proveedor no duplican respuestas

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
Busco un departamento en renta en Condesa
Cuanto cuesta la P002?
Quiero agendar una visita a P001 el 2026-08-10 a las 16:00
Me interesa, me llamo Ana y ando buscando algo en Polanco hasta 5 millones
Quiero hablar con alguien para negociar el precio
```

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
