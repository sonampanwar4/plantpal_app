import os
import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import user, plant, ai_bot, dashboard, photo, rag
from utils.logging_config import setup_logging

# ---------------------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------------------

ENV = os.getenv("ENV", "dev")
IS_DEV = ENV == "dev"

setup_logging()

# ---------------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------------

app = FastAPI(
    title="PlantPal AI Assistant",
    description="A smart, plant-only assistant for plant care, Q&A, and management.",
    version="1.0.0",
    debug=IS_DEV,
)

# ---------------------------------------------------------------------
# STATIC FILES (NO CACHE IN DEV)
# ---------------------------------------------------------------------

class DevStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if IS_DEV:
            response.headers["Cache-Control"] = "no-store"
        return response

app.mount("/static", DevStaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------------------

templates = Jinja2Templates(directory="templates")
if IS_DEV:
    templates.env.auto_reload = True
    templates.env.cache = {}

# ---------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------

@app.middleware("http")
async def cache_busting(request: Request, call_next):
    request.state.ts = int(time.time()) if IS_DEV else ""
    return await call_next(request)

# ---------------------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------------------

app.include_router(user.router)
app.include_router(plant.router)
app.include_router(ai_bot.router)
app.include_router(dashboard.router)
app.include_router(photo.router)
app.include_router(rag.health_router)

# ---------------------------------------------------------------------
# PAGES
# ---------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("home_page.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

# ---------------------------------------------------------------------
# RUN FUNCTION (IMPORTANT PART)
# ---------------------------------------------------------------------

def run():
    """
    Run the FastAPI app using Uvicorn.
    Use: python main.py
    """
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=IS_DEV,
        log_level="debug" if IS_DEV else "info",
    )

# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    run()
