import asyncio
import logging
from aiogram import Bot
from src.core.fifa_client import FifaClient
from src.core.session_manager import SessionManager
from src.db.database import AsyncSessionLocal
from sqlalchemy.future import select
from src.db.models import FifaAlert, User, AuditLog

logger = logging.getLogger(__name__)

async def notify_admins(bot: Bot, text: str, session):
    """Auxiliar para notificar solo a administradores"""
    admins_res = await session.execute(select(User).where(User.is_admin == True))
    admins = admins_res.scalars().all()
    for admin in admins:
        try:
            await bot.send_message(admin.telegram_id, text)
        except Exception as e:
            logger.error(f"Error notificando al admin {admin.telegram_id}: {e}")

async def start_worker(bot: Bot):
    client = FifaClient()
    logger.info("Fifa Worker iniciado. Comenzando chequeo del catálogo...")
    
    while True:
        try:
            async with AsyncSessionLocal() as session:
                active_users_res = await session.execute(select(User).where(User.subscription_active == True))
                active_users = active_users_res.scalars().all()
                
                if not active_users:
                    logger.info("No hay usuarios activos. Sleep 60s...")
                    await asyncio.sleep(60)
                    continue

                logger.info("Chequeando endpoint Catalog...")
                catalog_data = await client.get_catalog()
                
                if catalog_data is None:
                    # Posible Error 403 / Sesión muerta
                    logger.warning("Fallo en catologo (¿Caducó la sesión?). Iniciando stealth autorefresh...")
                    await notify_admins(bot, "⚠️ Sesión expirada o bloqueada por Akamai. Iniciando Playwright para auto-renovación Headless...", session)
                    
                    success = await SessionManager.renew_session()
                    if success:
                        await notify_admins(bot, "✅ Sesión renovada automáticamnete. Restaurando monitoreo.", session)
                        # Recargar las cookies en memoria desde el nuevo JSON
                        client._load_cookies()
                    else:
                        await notify_admins(bot, "🚨 CRÍTICO: La auto-renovación topó con un Slider Captcha u otro obstáculo. Requiere actualizar cookies.json o loguearse en el server manualmente. Pausando 5 minutos.", session)
                        await asyncio.sleep(300) # Penalidad de 5 minutos evitar loops
                    continue
                
                if isinstance(catalog_data, dict) and "sections" in catalog_data:
                    logger.info("Catálogo obtenido y estructurado correctamente.")
                    available_matches = []
                    
                    try:
                        for section in catalog_data.get("sections", []):
                            for cluster in section.get("clusters", []):
                                for item in cluster.get("items", []):
                                    product = item.get("product", {})
                                    performances = product.get("performances", [])
                                    for perf in performances:
                                        perf_code = perf.get("code")  # ej: m001
                                        num_availability = perf.get("availability", "NONE")
                                        
                                        if num_availability != "NONE":
                                            host_code = perf.get("hostTeam", {}).get("code", "")
                                            opp_code = perf.get("opposingTeam", {}).get("code", "")
                                            round_rank = perf.get("roundRank", 0)

                                            available_matches.append({
                                                "code": perf_code,
                                                "availability": num_availability,
                                                "venue": perf.get("venue", {}).get("es", "Unknown Venue"),
                                                "product_id": product.get("id"),
                                                "host_code": host_code,
                                                "opp_code": opp_code,
                                                "round_rank": round_rank
                                            })
                    except Exception as parse_e:
                        logger.error(f"Error parseando catálogo: {parse_e}")
                        
                    if available_matches:
                        for match in available_matches:
                            logger.info(f"MATCH DISPONIBLE ENCONTRADO: {match['code']} - {match['availability']}")
                            
                            # Generar "Tags" para este partido
                            match_tags = []
                            is_arg = (match['host_code'] == 'ARG' or match['opp_code'] == 'ARG')
                            
                            if is_arg:
                                match_tags.append("ARG_ALL")
                                if isinstance(match['round_rank'], int):
                                    if match['round_rank'] <= 3:
                                        match_tags.append("ARG_GROUP")
                                    else:
                                        match_tags.append("ARG_KNOCKOUT")
                                        
                            if match['round_rank'] == 104 and match_tags.count("FINAL") == 0:
                                match_tags.append("FINAL")

                            for usr in active_users:
                                # Obtener alertas activas de este usuario
                                user_alerts_res = await session.execute(
                                    select(FifaAlert).where(FifaAlert.user_id == usr.id, FifaAlert.is_active == True)
                                )
                                user_alert_codes = [a.product_code for a in user_alerts_res.scalars().all()]
                                
                                # Intersección entre match tags y user alerts
                                has_match = any(tag in user_alert_codes for tag in match_tags)
                                
                                if has_match:
                                    try:
                                        msg = (
                                            f"🚀 ¡TICKETS DISPONIBLES ALERTA!\n\n"
                                            f"Partido: {match['code']} ({match['host_code']} vs {match['opp_code']})\n"
                                            f"Estado: {match['availability']}\n"
                                            f"Sede: {match['venue']}\n"
                                            f"🔗 [Ir a comprar tickets](https://fwc26-shop-usd.tickets.fifa.com/secured/selection/event/date?productId={match['product_id']})"
                                        )
                                        await bot.send_message(usr.telegram_id, msg)
                                        
                                        # Registrar en AuditLog
                                        audit = AuditLog(user_id=usr.id, product_code=match['code'], message_sent=msg)
                                        session.add(audit)
                                    except Exception as e:
                                        logger.error(f"No se pudo notificar al UserID {usr.telegram_id}: {e}")
                            
                        await session.commit()
                    else:
                        logger.info("El catálogo no reportó ningún partido disponible.")
                
            # Delay anti-bot
            await asyncio.sleep(45)
            
        except asyncio.CancelledError:
            logger.info("Worker cancelado.")
            break
        except Exception as e:
            logger.error(f"Exception en worker asincrónico: {e}")
            await asyncio.sleep(60) 
            
    await client.close()
