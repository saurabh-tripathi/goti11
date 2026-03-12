from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, series, matches, teams, leaderboard, rules, admin

app = FastAPI(title="Goti11 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(series.router)
app.include_router(matches.router)
app.include_router(teams.router)
app.include_router(leaderboard.router)
app.include_router(rules.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
