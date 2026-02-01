from fastapi import FastAPI

from app.api.routes_activities import router as activities_router
from app.api.routes_insights import router as insights_router
from app.api.routes_webhooks import router as webhooks_router
from app.db.models import Base
from app.db.session import engine


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Geo Activity Insights API")

app.include_router(webhooks_router)
app.include_router(activities_router)
app.include_router(insights_router)
