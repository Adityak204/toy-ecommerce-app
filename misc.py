import asyncio
import httpx

PRODUCT_SERVICE_URL = "http://localhost:8000"
async def get_product(product_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
        print(response.status_code)
        print(response.json())
        print(response.status_code == 200)


asyncio.run(get_product(1))