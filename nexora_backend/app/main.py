from fastapi import FastAPI

from app.api.auth.router import router as auth_router
from app.api.ai.router import router as ai_router
from app.products.tutor.api import router as tutor_router
from app.products.tutor.classroom.api import router as classroom_router
from app.products.tutor.live.api import router as live_router


app = FastAPI(
    title="AQLITH AI",
    description="Intelligent AI Operating Platform",
    version="0.1.0"
)


app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(tutor_router)
app.include_router(classroom_router)
app.include_router(live_router)


@app.get("/health")
def health_check():

    return {
        "platform": "AQLITH AI",
        "status": "running",
        "version": "0.1.0"
    }
