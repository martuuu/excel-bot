import json
import logging
import asyncio
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class SessionManager:
    @staticmethod
    async def renew_session() -> bool:
        """
        Inicia Playwright en modo headless, simula una visita natural a la tienda de FIFA,
        permite que el challenge javascript invisible de DataDome se resuelva y recolecta las cookies limpias.
        """
        logger.info("Iniciando Chromium Headless para auto-renovación de sesión...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1440, "height": 900},
                    java_script_enabled=True
                )
                page = await context.new_page()
                
                # URL Base que invoca la generación de la cookie de DataDome inicial
                url = "https://fwc26-shop-usd.tickets.fifa.com/secured/selection/event/date?productId=10229225515651"
                
                logger.info("Cargando web y esperando resolución de JS/Seguridad...")
                await page.goto(url, wait_until="networkidle", timeout=40000)
                
                # Esperamos un pequeño delay pseudo-aleatorio para que el JS haga sus cálculos (Proof of Work)
                await asyncio.sleep(8)
                
                # Recuperar las cookies
                cookies = await context.cookies()
                
                # Verificar si tenemos la gran "datadome"
                has_datadome = any(c['name'] == 'datadome' for c in cookies)
                
                with open("cookies.json", "w") as f:
                    json.dump(cookies, f, indent=4)
                    
                await browser.close()

                if has_datadome:
                    logger.info("Cookie DataDome encontrada y guardada exitósamente.")
                    return True
                else:
                    logger.warning("No se extrajo una cookie DataDome válida. Es probable que se haya atascado en un Slider/Captcha.")
                    return False
                    
        except Exception as e:
            logger.error(f"Fallo en SessionManager (Playwright): {e}")
            return False
