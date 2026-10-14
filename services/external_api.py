import httpx
from core.exceptions import CurrencyNotFoundError,ExternalServiceError
from core.currency_config import Currency_Settings

cur = Currency_Settings()

async def currency_api(base, target,client: httpx.AsyncClient):
    try:    
        data = await client.get(cur.URL, params = {"base": base, "symbols" : target})
        data.raise_for_status()
    except httpx.RequestError as exc:
        raise ExternalServiceError
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise CurrencyNotFoundError
        else: raise ExternalServiceError
    currency_data = data.json()
    if not "base" in currency_data or not target in currency_data.get('rates',{}):
        raise CurrencyNotFoundError
    return currency_data