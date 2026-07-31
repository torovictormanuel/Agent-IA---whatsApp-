# api/index.py — Entry point para Vercel
#
# Vercel detecta este archivo (o app.py/index.py/server.py/main.py en la
# raíz) y expone la app ASGI que encuentre acá como una Serverless
# Function. No repetimos lógica: solo re-exportamos la app real.
from agent.main import app

__all__ = ["app"]
