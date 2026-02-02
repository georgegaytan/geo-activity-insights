from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
 
from app.api.routes_activities import router as activities_router
from app.api.routes_insights import router as insights_router
from app.api.routes_webhooks import router as webhooks_router
from app.api.routes_oauth import router as oauth_router
 
app = FastAPI(title="Geo Activity Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks_router)
app.include_router(activities_router)
app.include_router(insights_router)
app.include_router(oauth_router)
