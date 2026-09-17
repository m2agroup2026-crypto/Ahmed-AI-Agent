from fastapi import FastAPI

from app.api.auth.router import router as auth_router


app = FastAPI(
    title="NEXORA AI",
    description="Intelligent AI Operating Platform",
    version="0.1.0"
)


app.include_router(auth_router)


@app.get("/health")
def health_check():

    return {
        "platform": "NEXORA AI",
        "status": "running",
        "version": "0.1.0"
    }
