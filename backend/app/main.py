from fastapi import FastAPI

from app.routers import health

app = FastAPI(title="Finance Invoice Approval Platform")

app.include_router(health.router)
