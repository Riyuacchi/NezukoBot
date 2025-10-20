mod commands;
mod config;
mod database;
mod events;
mod handler;
mod utils;

use anyhow::Result;
use serenity::prelude::*;
use std::sync::Arc;
use tracing::{error, info};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "nezuko_bot=debug,serenity=info".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    info!("Starting Nezuko Bot");

    dotenv::dotenv().ok();
    let config = config::Config::from_env()?;

    let db_pool = database::init_database(&config.database_url).await?;
    info!("Database initialized successfully");

    info!("Running database migrations...");
    sqlx::migrate!("./migrations")
        .run(&db_pool)
        .await?;
    info!("Database migrations completed successfully");

    let bot_token = config.bot_token.clone();
    let default_prefix = config.default_prefix.clone();
    let config_arc = Arc::new(config.clone());

    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: commands::get_all_commands(),
            event_handler: |ctx, event, framework, data| {
                Box::pin(events::event_handler(ctx, event, framework, data))
            },
            prefix_options: poise::PrefixFrameworkOptions {
                prefix: Some(default_prefix),
                dynamic_prefix: Some(|ctx| {
                    Box::pin(async move {
                        Ok(match ctx.guild_id {
                            Some(gid) => database::get_guild_prefix(gid).await.or(Some(String::from("/"))),
                            None => Some(String::from("/")),
                        })
                    })
                }),
                ..Default::default()
            },
            ..Default::default()
        })
        .setup(move |ctx, _ready, framework| {
            let db_pool = db_pool.clone();
            let config_arc = config_arc.clone();
            Box::pin(async move {
                poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                Ok(handler::Data {
                    db_pool,
                    config: config_arc,
                })
            })
        })
        .build();

    let intents = GatewayIntents::GUILDS
        | GatewayIntents::GUILD_MEMBERS
        | GatewayIntents::GUILD_MESSAGES
        | GatewayIntents::GUILD_VOICE_STATES
        | GatewayIntents::MESSAGE_CONTENT
        | GatewayIntents::GUILD_PRESENCES;

    let mut client = Client::builder(&bot_token, intents)
        .framework(framework)
        .await?;

    let web_config = config;
    tokio::spawn(async move {
        if let Err(e) = start_web_server(web_config).await {
            error!("Web server error: {}", e);
        }
    });

    info!("Starting Discord client");
    client.start().await?;

    Ok(())
}

async fn start_web_server(config: config::Config) -> Result<()> {
    use axum::{routing::get, Router};
    use tower_http::cors::CorsLayer;

    let app = Router::new()
        .route("/", get(|| async { "Nezuko Bot Dashboard" }))
        .route("/health", get(|| async { "OK" }))
        .layer(CorsLayer::permissive());

    let addr = format!("{}:{}", config.web_host, config.web_port);
    info!("Web server starting on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
