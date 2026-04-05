from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy.future import select
from src.db.database import AsyncSessionLocal
from src.db.models import User

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        
        # Saltarse chequeo de BD si es el comando dev /start inicial
        if event.text and event.text.startswith("/start"):
            return await handler(event, data)
        
        # Para el resto de peticiones: chequeo de suscripción Zero-Trust
        telegram_id = event.from_user.id
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalars().first()
            
            if not user or not user.subscription_active:
               # Silenciosamente soltar la petición si no tiene la subscripción activa (anti-spam)
               return
            
            # Pasar usuario al context (data) por si los handlers lo necesitan
            data["user_db"] = user
            
        return await handler(event, data)
