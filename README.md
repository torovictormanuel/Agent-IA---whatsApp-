# AgentKit — WhatsApp AI Agent Builder

Construye tu propio agente de WhatsApp con inteligencia artificial en menos de 30 minutos.
No necesitas saber programar. Claude Code construye todo por ti.

<!-- ![AgentKit Demo](demo.gif) -->

---

## Que es AgentKit?

AgentKit es un proyecto que usa **Claude Code** (la herramienta de programacion de Anthropic)
para generar un agente de WhatsApp completo y personalizado para tu negocio.

Tu solo respondes preguntas sobre tu negocio. Claude Code se encarga de:
- Escribir todo el codigo
- Configurar la conexion con WhatsApp
- Crear un "cerebro" con IA que sabe sobre tu negocio
- Dejarlo listo para que tus clientes le escriban

---

## Como funciona? (El flujo completo)

### Paso 1: Tu clonas el repo y corres un comando

```bash
git clone https://github.com/torovictormanuel/Agent-IA---whatsApp-.git
cd Agent-IA---whatsApp-
bash start.sh
```

`start.sh` solo verifica que tengas Python 3.11+ y Claude Code instalados.

### Paso 2: Abres Claude Code y escribes /build-agent

```bash
claude
# Dentro de Claude Code escribe:
/build-agent
```

Esto activa el sistema. Claude Code lee las instrucciones de `CLAUDE.md` y empieza
a guiarte paso a paso.

### Paso 3: Claude Code te entrevista (5 minutos)

Te hace 10 preguntas, una por una:

1. **Nombre de tu negocio** — ej: "Cafeteria El Buen Sabor"
2. **A que se dedica** — ej: "Vendemos cafe de especialidad y postres artesanales"
3. **Para que quieres el agente** — responder preguntas, agendar citas, tomar pedidos, etc.
4. **Nombre del agente** — ej: "Sofia" (el nombre que veran tus clientes)
5. **Tono de comunicacion** — profesional, amigable, vendedor, o empatico
6. **Horario de atencion** — ej: "Lunes a Viernes 9am a 6pm"
7. **Archivos de tu negocio** — menu, precios, FAQ (los pones en la carpeta /knowledge)
8. **API Key de Anthropic** — la llave para usar Claude AI (te guia a obtenerla)
9. **Proveedor de WhatsApp** — eliges entre Meta o Twilio
10. **Credenciales del proveedor** — el token o keys de tu servicio de WhatsApp

### Paso 4: Claude Code construye tu agente (2-5 minutos)

Con tus respuestas, genera automaticamente estos archivos:

```
tu-proyecto/
├── agent/                     ← EL AGENTE COMPLETO
│   ├── main.py                Servidor web que recibe mensajes de WhatsApp
│   ├── brain.py               Conexion con Claude AI (el cerebro)
│   ├── memory.py              Guarda el historial de cada cliente
│   ├── tools.py               Herramientas especificas de tu negocio
│   └── providers/             Conexion con tu servicio de WhatsApp
│       ├── base.py            Interfaz comun
│       ├── __init__.py        Selecciona el proveedor automaticamente
│       └── meta.py            Adaptador (o twilio.py)
│
├── config/                    ← CONFIGURACION
│   ├── business.yaml          Datos de tu negocio
│   └── prompts.yaml           El "prompt" que define la personalidad del agente
│
├── knowledge/                 ← TUS ARCHIVOS
│   └── (menu.pdf, precios.txt, etc.)
│
├── tests/
│   └── test_local.py          Simulador de chat en tu terminal
│
├── requirements.txt           Dependencias de Python
├── Dockerfile                 Para produccion
├── docker-compose.yml         Orquestacion
└── .env                       Tus API keys (seguro, nunca se sube)
```

### Paso 5: Pruebas tu agente en la terminal (5 minutos)

Claude Code ejecuta un simulador de chat donde TU escribes como si fueras un cliente:

```
Tu: Hola, que horarios tienen?
Agente: Hola! Nuestro horario es de Lunes a Viernes de 9am a 6pm.
        Quieres que te ayude con algo mas?

Tu: Cuanto cuesta el cafe americano?
Agente: El cafe americano tiene un precio de $45 pesos.
        Te gustaria ordenar uno?
```

Si algo no te gusta, le dices a Claude Code y lo ajusta al momento.

### Paso 6: Deploy a produccion (opcional, 10 minutos)

Cuando estes satisfecho con tu agente, Claude Code te guia para ponerlo en linea:

1. **Claude Code prepara tu proyecto** para produccion (ajusta configuracion)
2. **Tu lo subes a GitHub** — Claude Code te da los comandos exactos para crear tu repo
3. **Conectas Railway** — entras a [railway.app](https://railway.app), le das tu repo de GitHub y Railway lo deployea automaticamente
4. **Configuras las variables** — Claude Code te dice exactamente cuales poner en Railway (las mismas API keys de tu .env)
5. **Configuras el webhook** — Claude Code te guia para conectar tu proveedor de WhatsApp con la URL de Railway

Despues de esto, cualquier persona que te escriba por WhatsApp sera atendida por tu agente.

**Nota:** No necesitas saber de servidores ni de deploy. Claude Code te dice cada paso, que escribir y donde hacer click.

---

## Como funciona el agente ya en produccion?

```
Un cliente escribe "Hola" por WhatsApp
         |
         v
Tu proveedor de WhatsApp (Meta/Twilio) recibe el mensaje
         |
         v
Envia el mensaje a tu servidor en Railway via webhook
         |
         v
agent/providers/ → Normaliza el mensaje (cada proveedor tiene formato diferente)
         |
         v
agent/memory.py → Busca el historial de ESE cliente (por numero de telefono)
         |
         v
agent/brain.py → Envia a Claude AI:
                 - El system prompt (personalidad + info de tu negocio)
                 - El historial de la conversacion
                 - El mensaje nuevo del cliente
         |
         v
Claude AI genera una respuesta inteligente
         |
         v
agent/providers/ → Envia la respuesta de vuelta por WhatsApp
         |
         v
El cliente recibe la respuesta en segundos
```

**Cosas importantes:**
- Cada cliente tiene su propio historial. Si alguien habla contigo y vuelve al dia siguiente, el agente recuerda la conversacion anterior.
- El agente NUNCA inventa informacion. Solo responde con lo que tu le diste.
- Si no sabe algo, responde: "No tengo esa informacion, dejame conectarte con alguien del equipo."
- El webhook valida la firma de Meta/Twilio antes de procesar cualquier mensaje (nadie mas puede hacerle hablar a tu agente gastando tu credito de Claude), y tiene idempotencia: si el proveedor reintenta la entrega de un mensaje, no lo responde dos veces.
- El agente puede usar herramientas reales (tool-calling): buscar informacion, agendar, registrar datos — no solo generar texto.

---

## Requisitos previos

Necesitas 4 cosas antes de empezar:

### 1. Python 3.11 o superior
- **Mac**: `brew install python` o descarga de [python.org](https://python.org/downloads)
- **Windows**: Descarga de [python.org](https://python.org/downloads) (marca "Add to PATH")
- **Linux**: `sudo apt install python3.11`
- Verifica: `python3 --version`

### 2. Claude Code
```bash
# Primero necesitas Node.js: https://nodejs.org
npm install -g @anthropic-ai/claude-code

# Autenticate (solo la primera vez)
claude
```

### 3. API Key de Anthropic
1. Ve a [platform.anthropic.com](https://platform.anthropic.com/settings/api-keys)
2. Crea una cuenta o inicia sesion
3. Ve a Settings → API Keys → Create Key
4. Copia la key (empieza con `sk-ant-...`)

### 4. Cuenta de WhatsApp API (elige una)

| Proveedor | Dificultad | Costo | Mejor para |
|-----------|-----------|-------|------------|
| [Meta Cloud API](https://developers.facebook.com) | Media | Gratis (ver nota) | Produccion seria, recomendado |
| [Twilio](https://twilio.com) | Media | Sandbox gratis / Pago por mensaje | Probar rapido sin verificar Business |

**Si solo quieres probar rapido**, Twilio tiene sandbox gratis y no requiere verificacion.

**Para produccion, Meta Cloud API directo es mas barato que Twilio:** desde 2025, las conversaciones iniciadas por el cliente (que es el 100% del trafico de un bot que solo responde, nunca manda marketing) son **gratis e ilimitadas** en Meta. Twilio cobra un markup por mensaje encima de eso aunque la conversacion de base sea gratis.

---

## Inicio rapido (3 comandos)

```bash
# 1. Clona el repositorio
git clone https://github.com/torovictormanuel/Agent-IA---whatsApp-.git
cd Agent-IA---whatsApp-

# 2. Verifica tu entorno
bash start.sh

# 3. Abre Claude Code y construye tu agente
claude
# Escribe: /build-agent
```

Claude Code te guia desde ahi. Solo responde las preguntas.

---

## Proveedores de WhatsApp

AgentKit soporta 2 proveedores. Tu eliges cual usar durante el setup.

### Meta Cloud API (recomendado)
- Configura en [developers.facebook.com](https://developers.facebook.com)
- Es la API oficial de WhatsApp (de Meta/Facebook)
- Necesitas: **Access Token** + **Phone Number ID** + **Verify Token** + **App Secret**
- Requiere cuenta de Facebook Business verificada
- Conversaciones iniciadas por el cliente: gratis e ilimitadas — el costo de mensajeria en produccion puede ser $0

### Twilio (mas rapido para probar)
- Registrate en [twilio.com](https://twilio.com)
- Sandbox gratuito sin verificacion (ideal para probar sin verificar un Business de Meta)
- Muy confiable, excelente documentacion
- Necesitas: **Account SID** + **Auth Token** + **Phone Number**
- Pago por mensaje en produccion

---

## Casos de uso

| Tipo de negocio | Que hace el agente | Ejemplo |
|-----------------|-------------------|---------|
| **Restaurante** | Responde sobre menu, horarios, ubicacion | "El platillo del dia es..." |
| **Clinica/Salon** | Agenda citas y reservaciones | "Tu cita quedo para el martes a las 3pm" |
| **Inmobiliaria** ([ejemplo completo](examples/inmobiliaria/)) | Busca propiedades, agenda visitas, califica leads | "Tenemos 3 departamentos en tu rango..." |
| **Tienda online** | Toma pedidos por WhatsApp | "Tu pedido de 2 pasteles quedo confirmado" |
| **SaaS/Software** | Soporte tecnico post-venta | "Para resetear tu contrasena, sigue estos pasos..." |
| **Cualquier negocio** | Responde preguntas frecuentes 24/7 | "Nuestro horario es..." |

---

## Comandos utiles (despues del setup)

```bash
# Probar el agente sin WhatsApp (chat en terminal)
python tests/test_local.py

# Arrancar el servidor localmente
uvicorn agent.main:app --reload --port 8000

# Build Docker para produccion
docker compose up --build

# Ver logs del agente
docker compose logs -f agent
```

---

## Personalizar tu agente despues

No necesitas tocar codigo. Abre Claude Code y pidele cambios en lenguaje natural:

```bash
# Cambiar como responde el agente
claude "El agente esta siendo muy formal. Hazlo mas amigable y casual."

# Agregar informacion nueva
claude "Agregamos un nuevo servicio de delivery. Actualiza el agente."

# Agregar una herramienta
claude "Quiero que el agente pueda consultar disponibilidad de citas."

# Cambiar de proveedor de WhatsApp
claude "Quiero migrar de Meta a Twilio."
```

---

## Stack tecnico

Para los curiosos, esto es lo que se usa por debajo:

| Componente | Tecnologia | Para que sirve |
|-----------|-----------|----------------|
| IA | Claude AI (claude-sonnet-5, configurable via `ANTHROPIC_MODEL`) | Genera las respuestas inteligentes, con tool-calling real |
| Servidor | FastAPI + Uvicorn | Recibe los webhooks de WhatsApp |
| WhatsApp | Meta / Twilio | Conecta con WhatsApp (tu eliges) |
| Base de datos | SQLite (local) / PostgreSQL (prod) | Guarda historial de conversaciones |
| Deploy | Docker + Railway | Pone tu agente en internet |
| Config | python-dotenv + YAML | Maneja API keys y configuracion |

---

## Arquitectura (para desarrolladores)

```
WhatsApp (cliente)
    |
    v
Proveedor (Meta/Twilio) ←→ agent/providers/ (normaliza formato)
    |
    v
FastAPI (agent/main.py) ←→ agent/memory.py (historial SQLite)
    |
    v
Claude API (agent/brain.py) ←→ config/prompts.yaml (personalidad)
    |
    v
Respuesta enviada de vuelta por WhatsApp
```

El sistema usa un **patron adaptador** para proveedores de WhatsApp. Cada proveedor
(Meta, Twilio) implementa la misma interfaz, asi que `main.py` no sabe ni le
importa cual estas usando. Solo llama `proveedor.parsear_webhook()` y
`proveedor.enviar_mensaje()`.

---

## Ejemplos completos, listos para correr

Ademas del flujo `/build-agent` (que genera un agente desde cero segun tus
respuestas), este repo trae dos implementaciones de referencia completas y
probadas — utiles tanto para probar el sistema ya mismo como para usarlas de
plantilla:

### [`examples/inmobiliaria/`](examples/inmobiliaria/) — single-tenant

Un agente completo para el rubro inmobiliario, adaptado al mercado argentino
(terminologia, moneda USD/ARS, aspectos legales). Busca propiedades, agenda
visitas, registra leads. Un deploy = un negocio — el modelo correcto mientras
manejas pocos clientes.

### [`examples/saas-multitenant/`](examples/saas-multitenant/) — multi-tenant

La misma logica de negocio, pero pensada para atender **muchos clientes desde
un solo servidor y una sola base de datos** en vez de un deploy por cliente.
Cada negocio tiene su propia URL de webhook (`/webhook/{negocio_id}`) y sus
datos quedan aislados por fila, no por infraestructura separada. Trae ademas
soporte listo para deployar gratis en Vercel + Neon.

Los dos ejemplos comparten el mismo motor de seguridad: validacion de firma
de webhook (nadie mas puede hacerle hablar a tu agente) e idempotencia
(los reintentos del proveedor no duplican respuestas).

---

## Preguntas frecuentes

**Necesito saber programar?**
No. Claude Code escribe todo el codigo por ti. Tu solo respondes preguntas.

**Cuanto cuesta?**
- AgentKit es gratis y open source
- Claude API: pagas por uso (~$3/millon de tokens, muy barato para un bot). Sin tier gratis de produccion, pero hay $5 de credito de bienvenida y, si el proyecto tiene financiamiento institucional, el [Anthropic Startup Program](https://www.anthropic.com/startup-program-official-terms) da creditos (no toma equity)
- WhatsApp: con Meta Cloud API directo, las conversaciones iniciadas por el cliente son gratis e ilimitadas — puede ser $0. Twilio tiene sandbox gratis para probar, pero cobra por mensaje en produccion
- Hosting: Railway ya no tiene tier gratis real. Alternativas gratis: Vercel (Hobby, solo uso no comercial), Koyeb o Render — ver `examples/saas-multitenant/README.md` para el detalle

**Puedo usar esto con mi negocio real?**
Si. Despues de las pruebas locales, lo subes a Railway y cualquier cliente
que te escriba por WhatsApp sera atendido por tu agente.

**Y si el agente no sabe algo?**
Responde algo como: "No tengo esa informacion, dejame conectarte con alguien
de nuestro equipo." Nunca inventa datos.

**Puedo tener multiples agentes?**
Si, dos formas: clonar el repo varias veces (un negocio por deploy, simple
mientras son pocos clientes), o usar `examples/saas-multitenant/` para
atender a todos desde un solo servidor y una sola base de datos — mejor
cuando el numero de clientes crece y actualizar N deploys deja de ser
manejable.

**Puedo cambiar de proveedor de WhatsApp despues?**
Si. Abre Claude Code y dile: "Quiero cambiar de Meta a Twilio" (o al reves).
El regenerara los archivos necesarios.

---

## Creditos

Proyecto original creado por **Todo de IA** — [@soyenriquerocha](https://instagram.com/soyenriquerocha).

Este fork agrega: validacion de firma de webhooks, idempotencia,
tool-calling real, y las implementaciones completas de referencia en
`examples/` (single-tenant inmobiliaria adaptada a Argentina, y el modo
SaaS multi-tenant).

Construido con [Claude Code](https://claude.ai/claude-code) para builders de LATAM.

---

## Licencia

MIT — Usa este proyecto como quieras, para lo que quieras.
