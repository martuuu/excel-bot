from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_kb() -> InlineKeyboardMarkup:
    """Teclado principal del bot"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔔 Mis Alertas", callback_data="menu_my_alerts"))
    builder.row(InlineKeyboardButton(text="➕ Nueva Alerta", callback_data="menu_new_alert"))
    return builder.as_markup()

def new_alert_countries_kb() -> InlineKeyboardMarkup:
    """Selección de países/categorías grandes"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🇦🇷 Argentina", callback_data="alert_country_arg"))
    builder.row(InlineKeyboardButton(text="🏆 La Gran Final", callback_data="alert_save_FINAL"))
    builder.row(InlineKeyboardButton(text="🔙 Volver", callback_data="menu_main"))
    return builder.as_markup()

def arg_phases_kb() -> InlineKeyboardMarkup:
    """Fases para Argentina"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Toda Argentina (Todos sus partidos)", callback_data="alert_save_ARG_ALL"))
    builder.row(InlineKeyboardButton(text="Fase de Grupos (Solo sus 3 primeros)", callback_data="alert_save_ARG_GROUP"))
    builder.row(InlineKeyboardButton(text="Rondas Eliminatorias (Octavos en adelante)", callback_data="alert_save_ARG_KNOCKOUT"))
    builder.row(InlineKeyboardButton(text="🔙 Volver", callback_data="menu_new_alert"))
    return builder.as_markup()

def my_alerts_kb(alerts: list) -> InlineKeyboardMarkup:
    """Muestra las alertas activas del usuario con opción a borrar"""
    builder = InlineKeyboardBuilder()
    
    # Text mapping para hacerlo amigable
    code_names = {
        "ARG_ALL": "🇦🇷 ARG - Todos",
        "ARG_GROUP": "🇦🇷 ARG - Fase de Grupos",
        "ARG_KNOCKOUT": "🇦🇷 ARG - Eliminatorias",
        "FINAL": "🏆 La Gran Final"
    }

    if not alerts:
        builder.row(InlineKeyboardButton(text="No tienes alertas. ¡Crea una!", callback_data="menu_new_alert"))
    else:
        for alert in alerts:
            name = code_names.get(alert.product_code, alert.product_code)
            # Cada botón borra la alerta específica
            builder.row(InlineKeyboardButton(text=f"🗑 Borrar: {name}", callback_data=f"alert_delete_{alert.id}"))
            
    builder.row(InlineKeyboardButton(text="🔙 Volver al Menú", callback_data="menu_main"))
    return builder.as_markup()
