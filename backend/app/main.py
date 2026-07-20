from fastapi import FastAPI

from app.routers import auth, health

app = FastAPI(title="Finance Invoice Approval Platform")

app.include_router(health.router)
app.include_router(auth.router)
