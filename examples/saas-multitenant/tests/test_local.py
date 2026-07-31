# tests/test_local.py — Simulador de chat en terminal (multi-tenant)
# Generado por AgentKit

"""
Igual que en el modo single-tenant, pero primero pide con qué negocio
querés chatear — útil para probar que dos negocios distintos, con
catálogos y prompts distintos, nunca se mezclan.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.db import inicializar_db
from agent.memory import obtener_negocio, guardar_mensaje, obtener_historial, limpiar_historial
from agent.brain import generar_respuesta
from agent.verticals import obtener_vertical

TELEFONO_TEST = "test-local-001"


async def main():
    await inicializar_db()

    negocio_id = input("ID del negocio a probar (ej: vista-real): ").strip()
    negocio = await obtener_negocio(negocio_id)
    if not negocio:
        print(f"No existe un negocio con id '{negocio_id}'. Dalo de alta con scripts/alta_negocio.py primero.")
        return

    vertical = obtener_vertical(negocio.vertical)

    print()
    print("=" * 55)
    print(f"   AgentKit — Test Local ({negocio.nombre})")
    print("=" * 55)
    print()
    print("  Comandos especiales: 'limpiar' (borra historial), 'salir'")
    print("-" * 55)
    print()

    while True:
        try:
            mensaje = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nTest finalizado.")
            break

        if not mensaje:
            continue
        if mensaje.lower() == "salir":
            print("\nTest finalizado.")
            break
        if mensaje.lower() == "limpiar":
            await limpiar_historial(negocio_id, TELEFONO_TEST)
            print("[Historial borrado]\n")
            continue

        historial = await obtener_historial(negocio_id, TELEFONO_TEST)

        print("\nAgente: ", end="", flush=True)
        respuesta = await generar_respuesta(
            mensaje=mensaje,
            historial=historial,
            telefono=TELEFONO_TEST,
            negocio_id=negocio_id,
            system_prompt=negocio.system_prompt,
            tools=vertical.TOOLS,
            ejecutar_tool=vertical.EJECUTAR_TOOL,
            fallback_message=negocio.fallback_message,
            error_message=negocio.error_message,
        )
        print(respuesta)
        print()

        await guardar_mensaje(negocio_id, TELEFONO_TEST, "user", mensaje)
        await guardar_mensaje(negocio_id, TELEFONO_TEST, "assistant", respuesta)


if __name__ == "__main__":
    asyncio.run(main())
