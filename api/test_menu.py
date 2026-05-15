import asyncio
from main import get_app_menu
import json

async def run():
    res = await get_app_menu("erp", None)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(run())
