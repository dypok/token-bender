from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import tokenize, analyze, translate, config_router, batch


app = FastAPI(title="Token Optimizer API", version="1.0.0")

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
