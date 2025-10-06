from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import socketio
import uvicorn
from pathlib import Path
import config
from web.middleware import setup_middlewares
from web.routes import auth, dashboard, api, public
from loguru import logger


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Bot Dashboard", docs_url=None, redoc_url=None)

app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET)
setup_middlewares(app, config)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

oauth = OAuth()
oauth.register(
    name="discord",
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    authorize_url="https://discord.com/api/oauth2/authorize",
    authorize_params={"scope": "identify guilds"},
    access_token_url="https://discord.com/api/oauth2/token",
    access_token_params=None,
    client_kwargs={"scope": "identify guilds"},
)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

socket_app = socketio.ASGIApp(sio, app)


@sio.event
async def connect(sid, environ):
    logger.info(f"Socket.IO client connected: {sid}")


@sio.event
async def disconnect(sid):
    logger.info(f"Socket.IO client disconnected: {sid}")


@sio.event
async def ping(sid, data):
    await sio.emit("pong", {"data": data}, room=sid)


app.include_router(public.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(api.router, prefix="/api", tags=["api"])


@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "404.html",
        {"request": request},
        status_code=404
    )


@app.exception_handler(500)
async def internal_error(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        "500.html",
        {"request": request},
        status_code=500
    )


def run_web():
    logger.info(f"Starting web server on {config.WEB_HOST}:{config.WEB_PORT}")
    uvicorn.run(
        "web.app:socket_app",
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        reload=False,
        access_log=False
    )


if __name__ == "__main__":
    run_web()