import asyncio
import logging
import sys
from src.core.fifa_client import FifaClient

root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

async def test_scraping():
    client = FifaClient()
    client.session.headers.update({"x-secutix-host": "fwc26-shop-usd.tickets.fifa.com"})
    logging.info("Testeando get_catalog()...")
    catalog = await client.get_catalog()
    if catalog:
        for section in catalog.get("sections", []):
            for cluster in section.get("clusters", []):
                for item in cluster.get("items", []):
                    product = item.get("product", {})
                    logging.info(f"Prod found: {product.get('id')}")
                    for perf in product.get("performances", []):
                        av = perf.get("availability")
                        code = perf.get("code")
                        logging.info(f"Perf: {code} -> {av}")
                        if av != "NONE":
                            logging.info(f"*** HAY LUGAR EN {code} ***")

    await client.close()

if __name__ == "__main__":
    asyncio.run(test_scraping())
