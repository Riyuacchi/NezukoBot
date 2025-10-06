import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
OWNER_ID = int(os.getenv("OWNER_ID", 0))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "elaina")
DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip('"')
DB_NAME = os.getenv("DB_NAME", "elaina_db")

LAVALINK_HOST = os.getenv("LAVALINK_HOST", "localhost")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", 8000))
SESSION_SECRET = os.getenv("SESSION_SECRET")
DOMAIN = os.getenv("DOMAIN", "http://localhost:8000")

JWT_SECRET = os.getenv("JWT_SECRET")

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

GENIUS_API_KEY = os.getenv("GENIUS_API_KEY")
KAWAII_API_KEY = os.getenv("KAWAII_API_KEY")

DEFAULT_PREFIX = "/"
EMBED_COLOR = 0x9B59B6