CREATE TABLE IF NOT EXISTS guilds (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    prefix TEXT NOT NULL DEFAULT '/',
    language TEXT NOT NULL DEFAULT 'en',
    welcome_channel_id INTEGER,
    welcome_message TEXT,
    welcome_enabled INTEGER NOT NULL DEFAULT 0,
    goodbye_channel_id INTEGER,
    goodbye_message TEXT,
    goodbye_enabled INTEGER NOT NULL DEFAULT 0,
    log_channel_id INTEGER,
    level_enabled INTEGER NOT NULL DEFAULT 1,
    level_channel_id INTEGER,
    level_message TEXT,
    moderation_enabled INTEGER NOT NULL DEFAULT 1,
    mute_role_id INTEGER,
    tickets_enabled INTEGER NOT NULL DEFAULT 0,
    tickets_category_id INTEGER,
    tickets_log_channel_id INTEGER,
    voice_channels_enabled INTEGER NOT NULL DEFAULT 0,
    voice_channels_category_id INTEGER,
    voice_channels_template TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 0,
    messages_count INTEGER NOT NULL DEFAULT 0,
    voice_time INTEGER NOT NULL DEFAULT 0,
    coins INTEGER NOT NULL DEFAULT 0,
    bank INTEGER NOT NULL DEFAULT 0,
    last_daily TEXT,
    last_weekly TEXT,
    last_work TEXT,
    warnings_count INTEGER NOT NULL DEFAULT 0,
    is_banned INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS economy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL UNIQUE,
    inventory TEXT,
    total_earned INTEGER NOT NULL DEFAULT 0,
    total_spent INTEGER NOT NULL DEFAULT 0,
    work_streak INTEGER NOT NULL DEFAULT 0,
    daily_streak INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    prize TEXT NOT NULL,
    winners_count INTEGER NOT NULL DEFAULT 1,
    host_id INTEGER NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    end_time TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS autoroles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, role_id)
);

CREATE TABLE IF NOT EXISTS voice_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL UNIQUE,
    owner_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    closed_by INTEGER,
    closed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS level_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_members_guild_user ON members(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_warnings_guild ON warnings(guild_id);
CREATE INDEX IF NOT EXISTS idx_warnings_user ON warnings(user_id);
CREATE INDEX IF NOT EXISTS idx_autoroles_guild ON autoroles(guild_id);
CREATE INDEX IF NOT EXISTS idx_voice_channels_guild ON voice_channels(guild_id);
CREATE INDEX IF NOT EXISTS idx_tickets_guild ON tickets(guild_id);
CREATE INDEX IF NOT EXISTS idx_level_roles_guild ON level_roles(guild_id);
