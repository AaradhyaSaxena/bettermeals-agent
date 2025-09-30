import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
async def post_json(url: str, json: dict, headers: dict = None, timeout: float = 15):
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=json, headers=headers)
        r.raise_for_status()
        return r.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=2))
async def get_json(url: str, params: dict = None, headers: dict = None, timeout: float = 15):
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()
