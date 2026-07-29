from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.http_pool import init_pool, close_pool
from app.routers import tokenize, analyze, translate, config_router, batch


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(title="Token Optimizer API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tokenize.router)
app.include_router(analyze.router)
app.include_router(translate.router)
app.include_router(config_router.router)
app.include_router(batch.router)


@app.get("/")
def root():
    return {"status": "ok", "app": "Token Optimizer API"}
