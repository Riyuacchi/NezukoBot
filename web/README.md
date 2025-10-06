# Elaina Web Dashboard

Complete FastAPI dashboard for managing the Elaina Discord bot.

## Structure

- `app.py` - FastAPI application with Socket.IO integration
- `middleware.py` - Custom security, logging, and rate-limit middlewares
- `routes/` - Route modules (auth, dashboard, api, public)
- `templates/` - Jinja2 HTML templates
- `static/` - CSS and JavaScript assets

## Run

```bash
python run_web.py
```

Then open http://localhost:8000 in your browser.

## Documentation

Helpful references at the project root:
- `WEB_DASHBOARD.md` - Full documentation
- `WEB_SETUP.md` - Installation guide
- `QUICK_START_WEB.md` - Quick start notes

## Features

- Discord OAuth2 authentication
- Secure session handling
- Complete REST API
- Realtime Socket.IO updates
- Responsive interface
- Six layered security middlewares
- Discord server configuration tools

## Technologies

FastAPI • Socket.IO • OAuth2 • Jinja2 • SQLAlchemy
