from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.future import select
from src.db.database import AsyncSessionLocal
from src.db.models import User, FifaAlert

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Registra al usuario inicialmente en SQLite.
    Se crea con subscription_active=False.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalars().first()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                subscription_active=False,
                is_admin=False
            )
            session.add(user)
            await session.commit()
            await message.answer("¡Bienvenido al sistema FIFA! Tu ID ha sido registrado pero necesita validación. Habla con el administrador o ejecuta el script init_admin.")
        else:
            await message.answer("Ya estás registrado en el sistema.")


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Devuelve el estado del bot"""
    await message.answer("✅ Bot FIFA funcionando y buscando tickets...\n(El worker corre en background de forma asíncrona)")


@router.message(Command("alert"))
async def cmd_alert(message: Message):
    """(Base/Ejemplo) Añadir o listar alertas del usuario"""
    await message.answer("Funcionalidad de configuración de alertas en construcción. Uso futuro: /alert ARG")
