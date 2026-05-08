from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import admin_engine, AdminBase
from .routers import auth, users, bandwidth, static_ips, nas, group_mgmt, accounting, auth_logs

AdminBase.metadata.create_all(bind=admin_engine)

app = FastAPI(title="FreeRADIUS Admin API", version="0.2.0",
              description="Comprehensive FreeRADIUS management API — users, bandwidth profiles, static IPs, NAS devices, "
                          "groups, accounting, and authentication logs.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(bandwidth.router)
app.include_router(static_ips.router)
app.include_router(nas.router)
app.include_router(group_mgmt.router)
app.include_router(accounting.router)
app.include_router(auth_logs.router)


@app.get("/health")
def health():
    return {"status": "ok"}
