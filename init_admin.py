import asyncio
import sys
from sqlalchemy.future import select
from src.db.database import AsyncSessionLocal, init_db
from src.db.models import User

async def set_admin():
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No hay ningún usuario registrado. Por favor, habla con el bot primero dando /start y luego vuelve a ejecutar este script.")
            return
            
        print("Usuarios detectados:")
        for idx, u in enumerate(users):
            print(f"[{idx}] ID Tlg: {u.telegram_id} - Nombre: {u.username} - Activo: {u.subscription_active}")
            
        print("\nTodos han sido ascendidos a subscripción Activa y Admin.")
        
        for u in users:
            u.subscription_active = True
            u.is_admin = True
            
        await session.commit()
        print("¡Listo! Ya puedes utilizar el bot con tu cuenta.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(set_admin())
