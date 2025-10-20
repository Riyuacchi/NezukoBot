pub mod models;

use anyhow::Result;
use serenity::model::id::GuildId;
use sqlx::{SqlitePool, sqlite::SqlitePoolOptions};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

lazy_static::lazy_static! {
    static ref PREFIX_CACHE: Arc<RwLock<HashMap<u64, String>>> = Arc::new(RwLock::new(HashMap::new()));
}

pub async fn init_database(database_url: &str) -> Result<SqlitePool> {
    let pool = SqlitePoolOptions::new()
        .max_connections(10)
        .connect(database_url)
        .await?;

    Ok(pool)
}

pub async fn get_guild_prefix(guild_id: GuildId) -> Option<String> {
    let cache = PREFIX_CACHE.read().await;
    cache.get(&guild_id.get()).cloned()
}

pub async fn ensure_guild(pool: &SqlitePool, guild_id: i64, guild_name: &str) -> Result<()> {
    sqlx::query!(
        r#"
        INSERT INTO guilds (id, name, prefix, language)
        VALUES (?, ?, '/', 'en')
        ON CONFLICT(id) DO UPDATE SET name = ?
        "#,
        guild_id,
        guild_name,
        guild_name
    )
    .execute(pool)
    .await?;

    Ok(())
}

pub async fn get_or_create_member(
    pool: &SqlitePool,
    guild_id: i64,
    user_id: i64,
    username: &str,
) -> Result<models::Member> {
    let member = sqlx::query_as!(
        models::Member,
        r#"
        SELECT id as "id!", guild_id as "guild_id!", user_id as "user_id!", username as "username!",
               xp as "xp!", level as "level!", messages_count as "messages_count!",
               voice_time as "voice_time!", coins as "coins!", bank as "bank!",
               last_daily, last_weekly, last_work,
               warnings_count as "warnings_count!", is_banned as "is_banned!",
               created_at as "created_at!", updated_at as "updated_at!"
        FROM members
        WHERE guild_id = ? AND user_id = ?
        "#,
        guild_id,
        user_id
    )
    .fetch_optional(pool)
    .await?;

    if let Some(member) = member {
        return Ok(member);
    }

    sqlx::query!(
        r#"
        INSERT INTO members (guild_id, user_id, username)
        VALUES (?, ?, ?)
        "#,
        guild_id,
        user_id,
        username
    )
    .execute(pool)
    .await?;

    let member = sqlx::query_as!(
        models::Member,
        r#"
        SELECT id as "id!", guild_id as "guild_id!", user_id as "user_id!", username as "username!",
               xp as "xp!", level as "level!", messages_count as "messages_count!",
               voice_time as "voice_time!", coins as "coins!", bank as "bank!",
               last_daily, last_weekly, last_work,
               warnings_count as "warnings_count!", is_banned as "is_banned!",
               created_at as "created_at!", updated_at as "updated_at!"
        FROM members
        WHERE guild_id = ? AND user_id = ?
        "#,
        guild_id,
        user_id
    )
    .fetch_one(pool)
    .await?;

    Ok(member)
}
