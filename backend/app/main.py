from contextlib import asynccontextmanager
from app.db.database import init_db
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
  init_db()
  yield


app = FastAPI(title="docpilot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(metrics_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
  return JSONResponse(
      status_code=exc.status_code,
      content={"detail": exc.detail},
  )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
  return JSONResponse(
      status_code=500,
      content={"detail": "an internal server error occurred"},
  )
