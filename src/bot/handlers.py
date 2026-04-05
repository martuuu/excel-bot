from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.future import select
from src.db.database import AsyncSessionLocal
from src.db.models import User, FifaAlert
import src.bot.keyboards as kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Registra y saluda al usuario con onboarding interactivo"""
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
            
        if not user.subscription_active:
            await message.answer(
                "👋 **¡Bienvenido a FIFA Ticket Radar!**\n\n"
                "Tu cuenta ha sido creada exitosamente, pero se encuentra en estado *Pendiente de Aprobación*.\n"
                "Contacta a Martín (Administrador) para que habilite tu suscripción, o ejecuta `init_admin` si este es tu propio servidor.",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "⚽️ **Panel de Control: FIFA Ticket Radar**\n\n"
                "Tu suscripción está ACTIVA. ¿Qué te gustaría hacer hoy?",
                reply_markup=kb.main_menu_kb(),
                parse_mode="Markdown"
            )

# ==========================================================
# CALLBACKS (NAVEGACIÓN)
# ==========================================================

@router.callback_query(F.data == "menu_main")
async def cb_menu_main(callback: CallbackQuery):
    """Vuelve al menú principal"""
    await callback.message.edit_text("⚽️ **Panel de Control:**\nElige una opción:", reply_markup=kb.main_menu_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "menu_new_alert")
async def cb_menu_new_alert(callback: CallbackQuery):
    """Muestra para elegir país"""
    await callback.message.edit_text("🌎 **Selecciona tu interés:**", reply_markup=kb.new_alert_countries_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "alert_country_arg")
async def cb_alert_country_arg(callback: CallbackQuery):
    """Muestra para elegir fases de ARG"""
    await callback.message.edit_text("🇦🇷 **Selecciona qué partidos de Argentina deseas monitorear:**", reply_markup=kb.arg_phases_kb(), parse_mode="Markdown")

@router.callback_query(F.data == "menu_my_alerts")
async def cb_menu_my_alerts(callback: CallbackQuery):
    """Muestra alertas activas desde la BD"""
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = user_res.scalars().first()
        
        alerts_res = await session.execute(select(FifaAlert).where(FifaAlert.user_id == user.id, FifaAlert.is_active == True))
        alerts = alerts_res.scalars().all()
        
        await callback.message.edit_text("🔔 **Tus Alertas Activas:**\nSelecciona una para borrarla.", reply_markup=kb.my_alerts_kb(alerts), parse_mode="Markdown")


# ==========================================================
# CALLBACKS (CREACIÓN Y BORRADO DE BASE DE DATOS)
# ==========================================================

@router.callback_query(F.data.startswith("alert_save_"))
async def cb_alert_save(callback: CallbackQuery):
    """Guarda una nueva alerta en SQLite"""
    product_code = callback.data.replace("alert_save_", "")
    
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = user_res.scalars().first()
        
        # Try to find if already exists
        exist_res = await session.execute(
            select(FifaAlert).where(FifaAlert.user_id == user.id, FifaAlert.product_code == product_code)
        )
        existing = exist_res.scalars().first()
        
        if existing:
            await callback.answer("Ya estás suscrito a esa alerta.", show_alert=True)
            return
            
        new_alert = FifaAlert(user_id=user.id, product_code=product_code, is_active=True)
        session.add(new_alert)
        await session.commit()
        
        await callback.answer("✅ ¡Alerta Creada con Éxito!", show_alert=True)
        # Refrescar listado
        alerts_res = await session.execute(select(FifaAlert).where(FifaAlert.user_id == user.id, FifaAlert.is_active == True))
        alerts = alerts_res.scalars().all()
        await callback.message.edit_text("🔔 **Tus Alertas Activas:**", reply_markup=kb.my_alerts_kb(alerts), parse_mode="Markdown")


@router.callback_query(F.data.startswith("alert_delete_"))
async def cb_alert_delete(callback: CallbackQuery):
    """Borra una alerta"""
    alert_id = int(callback.data.replace("alert_delete_", ""))
    
    async with AsyncSessionLocal() as session:
        alert_res = await session.execute(select(FifaAlert).where(FifaAlert.id == alert_id))
        alert = alert_res.scalars().first()
        
        if alert:
            await session.delete(alert)
            await session.commit()
            await callback.answer("⚠️ Alerta eliminada.", show_alert=False)
            
        user_res = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = user_res.scalars().first()
        
        # Volver al menu de alertas
        alerts_res = await session.execute(select(FifaAlert).where(FifaAlert.user_id == user.id, FifaAlert.is_active == True))
        alerts = alerts_res.scalars().all()
        await callback.message.edit_text("🔔 **Tus Alertas Activas:**", reply_markup=kb.my_alerts_kb(alerts), parse_mode="Markdown")


# ==========================================================
# ADMIN COMMANDS
# ==========================================================

@router.message(Command("testdrop"))
async def cmd_testdrop(message: Message):
    """(Admin Solo) Simula que el worker encontró un ticket para testear la UI."""
    async with AsyncSessionLocal() as session:
        admin_check = await session.execute(select(User).where(User.telegram_id == message.from_user.id, User.is_admin == True))
        if not admin_check.scalars().first():
            return

        # Para probar la UX nativa, simplemente manda el link hardcodeado a sí mismo
        match_code = "ARG (Test)"
        product_id = "10229225515651"
        fake_url = f"https://fwc26-shop-usd.tickets.fifa.com/secured/selection/event/date?productId={product_id}"
        
        msg_text = (
            f"🚀 [PRUEBA] ¡TICKETS DISPONIBLES ALERTA!\n\n"
            f"Partido: {match_code}\n"
            f"Estado: HIGH\n"
            f"🔗 [Ir a comprar tickets (*TEST*)]({fake_url})"
        )
        await message.answer(msg_text)
