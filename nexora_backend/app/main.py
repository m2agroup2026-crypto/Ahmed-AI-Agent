from fastapi import FastAPI


app = FastAPI(
    title="NEXORA AI",
    description="Intelligent AI Operating Platform",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {
        "platform": "NEXORA AI",
        "status": "running",
        "version": "0.1.0"
    }
