from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import config as app_config
from loguru import logger
import aiohttp


router = APIRouter()

oauth = OAuth()
oauth.register(
    name="discord",
    client_id=app_config.CLIENT_ID,
    client_secret=app_config.CLIENT_SECRET,
    authorize_url="https://discord.com/api/oauth2/authorize",
    authorize_params=None,
    access_token_url="https://discord.com/api/oauth2/token",
    access_token_params=None,
    client_kwargs={"scope": "identify guilds"},
)


async def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_optional_user(request: Request):
    return request.session.get("user")


@router.get("/login")
async def login(request: Request):
    redirect_uri = f"{app_config.DOMAIN}/auth/callback"
    return await oauth.discord.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def callback(request: Request):
    try:
        token = await oauth.discord.authorize_access_token(request)

        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {token['access_token']}"}

            async with session.get("https://discord.com/api/v10/users/@me", headers=headers) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=400, detail="Failed to fetch user data")
                user_data = await resp.json()

            async with session.get("https://discord.com/api/v10/users/@me/guilds", headers=headers) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=400, detail="Failed to fetch guilds")
                guilds_data = await resp.json()

        user_info = {
            "id": user_data["id"],
            "username": user_data["username"],
            "discriminator": user_data.get("discriminator", "0"),
            "avatar": user_data.get("avatar"),
            "guilds": guilds_data,
            "access_token": token["access_token"]
        }

        request.session["user"] = user_info

        logger.info(f"User logged in: {user_info['username']} ({user_info['id']})")

        return RedirectResponse(url="/dashboard")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


@router.get("/me")
async def get_me(request: Request, user: dict = Depends(get_current_user)):
    return JSONResponse(content={
        "id": user["id"],
        "username": user["username"],
        "discriminator": user["discriminator"],
        "avatar": user.get("avatar"),
        "guilds": user.get("guilds", [])
    })