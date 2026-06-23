import asyncio
import httpx

async def test():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # We don't have a token, let's see what happens. We might get 401.
        # But wait, we can just print the route list.
        pass

asyncio.run(test())
