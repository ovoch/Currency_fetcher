import logging 
import httpx
from fastapi import FastAPI,Request
from api.users import router as users_router
from fastapi.responses import JSONResponse
from jwt.exceptions import PyJWTError
from core.exceptions import CurrencyNotFoundError,ExternalServiceError, UserAlreadyExistsError
from api.currency import router as currency_router
from contextlib import asynccontextmanager
from core.logger import logger_config

logger_config()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient()
    yield {"client" : client}
    await client.aclose()
    
app = FastAPI(lifespan=lifespan)

app.include_router(currency_router)
app.include_router(users_router)

@app.exception_handler(UserAlreadyExistsError)
async def validation_exception_handler(request: Request, exc: UserAlreadyExistsError):
    logger.warning("User exists")
    return JSONResponse(status_code=409, content={"detail": "User already exists"})

@app.exception_handler(PyJWTError)
async def token_validation(request: Request, exc: PyJWTError):
    logger.warning("Validation is failed")
    return JSONResponse(status_code= 401, content={"detail": "Validation is failed"})

@app.exception_handler(CurrencyNotFoundError)
async def not_found_currency(request: Request, exc: CurrencyNotFoundError):
    logger.warning("Currency is nof found")
    return JSONResponse(status_code = 404, content= {"detail": "Currency is not found"})

@app.exception_handler(ExternalServiceError)
async def service_error(request: Request, exc: ExternalServiceError):
    logger.error("Gateway is down")
    return JSONResponse(status_code = 502, content={"detail":"Gateway is broken"})

    
