from fastapi import FastAPI

from app.routers import auth, health, requests

app = FastAPI(title="Finance Invoice Approval Platform")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(requests.router)
