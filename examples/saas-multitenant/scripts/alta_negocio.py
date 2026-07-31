# scripts/alta_negocio.py — Onboarding de un cliente nuevo a la plataforma
# Generado por AgentKit (modo multi-tenant)

"""
Da de alta un negocio nuevo en la plataforma SaaS. Reutiliza el MISMO
formato de config/prompts.yaml que ya genera Claude Code en el modo
single-tenant (/build-agent) — así el flujo de entrevista de siempre
sirve para producir el archivo que después cargás acá.

Ejemplo:
    python scripts/alta_negocio.py \\
        --id vista-real \\
        --nombre "Vista Real Inmobiliaria" \\
        --vertical inmobiliaria \\
        --prompt-file ../inmobiliaria/config/prompts.yaml \\
        --propiedades ../inmobiliaria/config/propiedades.yaml \\
        --provider twilio \\
        --twilio-sid ACxxxxxxxx \\
        --twilio-token xxxxxxxx \\
        --twilio-numero "+14155238886"
"""

import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from agent.db import inicializar_db
from agent.memory import obtener_negocio, crear_negocio, cargar_catalogo
from agent.models import Negocio
from agent.verticals import VERTICALES


def parse_args():
    p = argparse.ArgumentParser(description="Da de alta un negocio nuevo en la plataforma")
    p.add_argument("--id", required=True, help="Slug único, ej: vista-real (se usa en la URL del webhook)")
    p.add_argument("--nombre", required=True)
    p.add_argument("--vertical", required=True, choices=list(VERTICALES.keys()))
    p.add_argument("--prompt-file", required=True, help="Ruta a un prompts.yaml (mismo formato del modo single-tenant)")
    p.add_argument("--propiedades", help="Ruta a un propiedades.yaml para precargar el catálogo (opcional)")

    p.add_argument("--provider", required=True, choices=["twilio", "meta"])
    p.add_argument("--twilio-sid")
    p.add_argument("--twilio-token")
    p.add_argument("--twilio-numero")
    p.add_argument("--meta-token")
    p.add_argument("--meta-phone-id")
    p.add_argument("--meta-verify-token", default="agentkit-verify")
    p.add_argument("--meta-app-secret")

    return p.parse_args()


async def main():
    args = parse_args()

    await inicializar_db()

    if await obtener_negocio(args.id):
        print(f"Ya existe un negocio con id '{args.id}'. Elegí otro --id o borralo primero.")
        sys.exit(1)

    with open(args.prompt_file, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f) or {}
    system_prompt = prompts.get("system_prompt")
    if not system_prompt:
        print(f"'{args.prompt_file}' no tiene una clave 'system_prompt'.")
        sys.exit(1)

    negocio = Negocio(
        id=args.id,
        nombre=args.nombre,
        vertical=args.vertical,
        system_prompt=system_prompt,
        fallback_message=prompts.get("fallback_message", "Disculpa, no entendí tu mensaje. ¿Podrías reformularlo?"),
        error_message=prompts.get("error_message", "Lo siento, estoy teniendo problemas técnicos. Por favor intenta de nuevo en unos minutos."),
        whatsapp_provider=args.provider,
        twilio_account_sid=args.twilio_sid,
        twilio_auth_token=args.twilio_token,
        twilio_phone_number=args.twilio_numero,
        meta_access_token=args.meta_token,
        meta_phone_number_id=args.meta_phone_id,
        meta_verify_token=args.meta_verify_token,
        meta_app_secret=args.meta_app_secret,
    )
    await crear_negocio(negocio)
    print(f"Negocio '{args.id}' creado.")

    if args.propiedades:
        with open(args.propiedades, "r", encoding="utf-8") as f:
            catalogo = yaml.safe_load(f) or {}
        propiedades = catalogo.get("propiedades", [])
        await cargar_catalogo(args.id, propiedades)
        print(f"Catálogo cargado: {len(propiedades)} propiedades.")

    print()
    print("Configurá esta URL de webhook en la consola del proveedor:")
    print(f"  https://TU-DOMINIO/webhook/{args.id}")
    if args.provider == "meta":
        print(f"  Verify Token: {args.meta_verify_token}")


if __name__ == "__main__":
    asyncio.run(main())
