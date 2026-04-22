from fastapi import FastAPI

from app.web.routes import router


app = FastAPI(title="Review Radar MVP", version="0.1.0")
app.include_router(router)
