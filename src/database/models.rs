use serde::{Deserialize, Serialize};
use sqlx::FromRow;

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct Guild {
    pub id: i64,
    pub name: String,
    pub prefix: String,
    pub language: String,
    pub welcome_channel_id: Option<i64>,
    pub welcome_message: Option<String>,
    pub welcome_enabled: i64,
    pub goodbye_channel_id: Option<i64>,
    pub goodbye_message: Option<String>,
    pub goodbye_enabled: i64,
    pub log_channel_id: Option<i64>,
    pub level_enabled: i64,
    pub level_channel_id: Option<i64>,
    pub level_message: Option<String>,
    pub moderation_enabled: i64,
    pub mute_role_id: Option<i64>,
    pub tickets_enabled: i64,
    pub tickets_category_id: Option<i64>,
    pub tickets_log_channel_id: Option<i64>,
    pub voice_channels_enabled: i64,
    pub voice_channels_category_id: Option<i64>,
    pub voice_channels_template: Option<String>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct Member {
    pub id: i64,
    pub guild_id: i64,
    pub user_id: i64,
    pub username: String,
    pub xp: i64,
    pub level: i64,
    pub messages_count: i64,
    pub voice_time: i64,
    pub coins: i64,
    pub bank: i64,
    pub last_daily: Option<String>,
    pub last_weekly: Option<String>,
    pub last_work: Option<String>,
    pub warnings_count: i64,
    pub is_banned: i64,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct AutoRole {
    pub id: i64,
    pub guild_id: i64,
    pub role_id: i64,
    pub enabled: i64,
    pub created_at: String,
}

#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct VoiceChannel {
    pub id: i64,
    pub guild_id: i64,
    pub channel_id: i64,
    pub owner_id: i64,
    pub name: String,
    pub created_at: String,
}
