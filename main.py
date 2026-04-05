import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from src.db.database import init_db
from src.bot.handlers import router
from src.bot.middlewares import AuthMiddleware
from src.core.worker import start_worker

# Configurar Logging Básico
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    # Cargar variables (.env)
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or token == "tu_token_aqui":
        logger.error("Revisa tu .env. TELEGRAM_BOT_TOKEN es inválido o no existe.")
        return

    # Inicializar Base de Datos SQLite
    await init_db()
    logger.info("Base de Datos SQLite inicializada.")

    # Inicializar Telegram
    bot = Bot(token=token)
    dp = Dispatcher()

    # Montar Middlewares (Chequeo Zero-Trust Autorización)
    dp.message.middleware(AuthMiddleware())
    
    # Montar Comandos (Router)
    dp.include_router(router)
    
    # Crear tarea asíncrona para que el Worker de Scrape corra al mismo tiempo que el Bot
    worker_task = asyncio.create_task(start_worker(bot))
    
    logger.info("Iniciando Bot Async Polling...")
    try:
        await dp.start_polling(bot)
    finally:
        worker_task.cancel()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot apagado por el usuario (Ctrl+C)")
