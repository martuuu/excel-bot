from curl_cffi.requests import AsyncSession
import os
import json
import logging

logger = logging.getLogger(__name__)

class FifaClient:
    def __init__(self):
        # Configuramos impersonación de navegador para eludir DataDome y bloqueos TLS básicos
        self.session = AsyncSession(impersonate="chrome110")
        
        # Preparamos las cabeceras bases
        self.session.headers.update({
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,es;q=0.8",
            "country-tag": "us",
            "language-tag": "en",
            "origin": "https://fwc26-shop-usd.tickets.fifa.com",
            "referer": "https://fwc26-shop-usd.tickets.fifa.com/secured/selection/event/date?productId=10229225515651",
        })
        self._load_cookies()

    def _load_cookies(self):
        """Intenta leer cookies.json e inyectar las cookies al Client para eludir bloqueos locales"""
        cookies_path = "cookies.json"
        count = 0
        if os.path.exists(cookies_path):
            try:
                with open(cookies_path, "r") as f:
                    cookies_data = json.load(f)
                    for cookie in cookies_data:
                        self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.fifa.com'))
                        count += 1
                logger.info(f"Se cargaron {count} cookies desde cookies.json")
            except Exception as e:
                logger.error(f"Error al leer cookies.json: {e}")
        else:
            logger.warning("No se encontró cookies.json. Scraper puede encontrar problemas antibot DataDome.")

    async def get_catalog(self):
        """Llamada base al endpoint catalog descubierto para obtener matches y availability"""
        url = "https://fwc26-shop-usd.tickets.fifa.com/tnwr/v1/secure/catalog?maxPerformances=50&maxTimeslots=50&maxPerformanceDays=3&maxTimeslotDays=3&includeMetadata=true"
        try:
            response = await self.session.get(url)
            if response.status_code == 200:
                logger.info("Catálogo descargado con StatusCode 200.")
                return response.json()
            elif response.status_code in [403, 401]:
                logger.warning(f"Error de Autorización o Anti-Bot: {response.status_code}. (Verificar Cookies DataDome/Akamai)")
            else:
                logger.error(f"Error HTTP Fetch Catalog: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"FifaClient Exception (Catalog): {e}")
        return None

    async def check_add_to_cart_availability(self, product_code: str):
        """Simula la llamada POST."""
        payload = {
            "ProductType": 2,
            "ProductCode": product_code,
            "OrderId": 0,
            "SelectedQuantity": 1,
            "PartnerId": "",
            "ServiceSelectionData": {
                "AudienceSubCategoryId": 10229206883477, # Hardcoded por ahora según tus API dumps
                "SeatCategoryCode": "FMT_P"
            }
        }
        url = "https://fwc26-shop-usd.tickets.fifa.com/next-api/orders"
        try:
            response = await self.session.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"FifaClient Exception (Orders API): {e}")
            return False

    async def close(self):
        await self.session.close()
