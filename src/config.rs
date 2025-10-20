use anyhow::{Context, Result};
use serde::Deserialize;
use std::env;

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    pub bot_token: String,

    pub database_url: String,

    pub web_host: String,
    pub web_port: u16,

    pub kawaii_api_key: Option<String>,

    pub default_prefix: String,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        Ok(Self {
            bot_token: env::var("BOT_TOKEN")
                .context("BOT_TOKEN must be set")?,

            database_url: env::var("DATABASE_URL")
                .unwrap_or_else(|_| "sqlite:./nezuko.db".to_string()),

            web_host: env::var("WEB_HOST")
                .unwrap_or_else(|_| "0.0.0.0".to_string()),
            web_port: env::var("WEB_PORT")
                .unwrap_or_else(|_| "8000".to_string())
                .parse()
                .unwrap_or(8000),

            kawaii_api_key: env::var("KAWAII_API_KEY").ok(),

            default_prefix: env::var("DEFAULT_PREFIX")
                .unwrap_or_else(|_| "/".to_string()),
        })
    }
}
