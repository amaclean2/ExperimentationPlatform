from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import init_db

from .routes import experiments_router, segments_router, events_router, users_router, auth_router

from .views import experiment_views

app = FastAPI(title="Experimentation Server", version="1.0.0")

app.mount("/static", StaticFiles(directory="src/static"), name="static")

app.include_router(experiment_views.router, prefix="/ui", tags=["UI"])

app.include_router(auth_router)
app.include_router(experiments_router)
app.include_router(segments_router)
app.include_router(events_router)
app.include_router(users_router)


@app.on_event("startup")
async def startup_event():
    await init_db()


@app.get("/")
async def root():
    return {"message": "Experimentation Server API"}
