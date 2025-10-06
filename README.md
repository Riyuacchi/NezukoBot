# NezukoBot

A fully-featured, adaptive Discord bot with music, moderation, economy, and more. The bot automatically uses its own name from Discord - no hardcoded names!

## Features

- **Moderation**: Kick, ban, warn, mute, and more
- **Music**: Play music from YouTube, Spotify, and more with Lavalink
- **Economy**: Virtual currency system with shops and gambling
- **Leveling**: XP and leveling system with role rewards
- **Tickets**: Support ticket system
- **Temporary Voice Channels**: Dynamic voice channel creation
- **Giveaways**: Create and manage giveaways
- **Welcome/Goodbye**: Customizable welcome and goodbye messages
- **Logging**: Comprehensive event logging
- **Web Dashboard**: Manage your server settings via web interface

## Installation

### Prerequisites

- Python 3.10 or higher
- MySQL/MariaDB database
- Lavalink server (for music functionality)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Riyuacchi/NezukoBot.git
cd NezukoBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the `.env` file with your credentials:
```env
BOT_TOKEN=your_bot_token_here
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
OWNER_ID=your_discord_user_id_here

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_database_password_here
DB_NAME=discord_bot_db

LAVALINK_HOST=localhost
LAVALINK_PORT=2333
LAVALINK_PASSWORD=youshallnotpass

WEB_HOST=0.0.0.0
WEB_PORT=8000
SESSION_SECRET=your_session_secret_here
DOMAIN=http://localhost:8000

JWT_SECRET=your_jwt_secret_here

SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

GENIUS_API_KEY=your_genius_api_key_here
KAWAII_API_KEY=your_kawaii_api_key_here
```

4. Start the bot:
```bash
python main.py
```

## Quick Setup Commands

All setup commands are fully automated and require no additional input:

- `/setup voice` - Creates temporary voice channels system with category and lobby channel
- `/setup welcome` - Creates welcome channel with default message
- `/setup goodbye` - Creates goodbye channel with default message
- `/setup tickets` - Creates ticket system with category and log channel
- `/setup logs` - Creates bot logs channel for event logging

## Commands

### Admin Commands
- `/setup` - View current server configuration
- `/setup general` - Configure prefix and language
- `/setup voice` - Set up temporary voice channels
- `/setup welcome` - Configure welcome messages
- `/setup goodbye` - Configure goodbye messages
- `/setup tickets` - Set up ticket system
- `/setup logs` - Configure logging
- `/automod` - Toggle automatic moderation
- `/autorole` - Manage auto-assigned roles
- `/giveaway` - Create giveaways

### Moderation Commands
- `/ban` - Ban a user
- `/kick` - Kick a user
- `/warn` - Warn a user
- `/mute` - Mute a user
- `/unmute` - Unmute a user
- `/clear` - Clear messages
- `/slowmode` - Set slowmode

### Music Commands
- `/play` - Play a song
- `/pause` - Pause playback
- `/resume` - Resume playback
- `/skip` - Skip current song
- `/queue` - View queue
- `/nowplaying` - Current song info
- `/volume` - Adjust volume

### Economy Commands
- `/balance` - Check balance
- `/daily` - Daily rewards
- `/work` - Earn money
- `/pay` - Transfer money
- `/shop` - View shop
- `/buy` - Purchase items
- `/inventory` - View inventory

### Fun Commands
- `/meme` - Random meme
- `/joke` - Random joke
- `/8ball` - Magic 8-ball
- `/coinflip` - Flip a coin
- `/dice` - Roll dice

### Utility Commands
- `/help` - Show help
- `/userinfo` - User information
- `/serverinfo` - Server information
- `/avatar` - Get user avatar
- `/ping` - Bot latency

## Database

The bot uses MySQL/MariaDB for data persistence. The database schema is automatically created on first run.

## Web Dashboard

Access the web dashboard at `http://localhost:8000` (or your configured domain) to manage server settings via a web interface.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions, please open an issue on GitHub.
