from fastapi import FastAPI
from equeue.api.routes.jobs import router as jobs_router

def create_app() -> FastAPI:
    app = FastAPI(title="eQueue")
    app.include_router(jobs_router)
    return app

app = create_app()