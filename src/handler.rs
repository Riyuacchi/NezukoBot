use crate::config::Config;
use sqlx::SqlitePool;
use std::sync::Arc;

pub struct Data {
    pub db_pool: SqlitePool,
    pub config: Arc<Config>,
}

pub type Error = Box<dyn std::error::Error + Send + Sync>;
pub type Context<'a> = poise::Context<'a, Data, Error>;
