import os

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, auth, leaderboard, matches, rules, series, teams

# In production (ECS) set API_PREFIX=/api so ALB can route /api/* → this service.
# In dev the Vite proxy already strips /api, so leave it empty.
_api_prefix = os.getenv("API_PREFIX", "")

app = FastAPI(title="Goti11 API", version="1.0.0", root_path=_api_prefix)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All API routers are grouped under the optional prefix
_router = APIRouter(prefix=_api_prefix)
_router.include_router(auth.router)
_router.include_router(series.router)
_router.include_router(matches.router)
_router.include_router(teams.router)
_router.include_router(leaderboard.router)
_router.include_router(rules.router)
_router.include_router(admin.router)
app.include_router(_router)


# Health check stays at root — used by ALB target group health checks
@app.get("/health")
def health():
    return {"status": "ok"}
