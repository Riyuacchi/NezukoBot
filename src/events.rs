use crate::database;
use crate::handler::{Data, Error};
use crate::utils::to_db_id;
use poise::serenity_prelude as serenity;
use poise::serenity_prelude::Mentionable;
use tracing::{error, info, warn};

pub async fn event_handler(
    ctx: &serenity::Context,
    event: &serenity::FullEvent,
    _framework: poise::FrameworkContext<'_, Data, Error>,
    data: &Data,
) -> Result<(), Error> {
    match event {
        serenity::FullEvent::Ready { data_about_bot } => {
            info!("Bot logged in as: {}", data_about_bot.user.name);
            info!("Bot ID: {}", data_about_bot.user.id);
            info!("Connected to {} guilds", data_about_bot.guilds.len());

            ctx.set_activity(Some(serenity::ActivityData::watching(
                format!("{} servers", data_about_bot.guilds.len()),
            )));
        }

        serenity::FullEvent::GuildCreate { guild, .. } => {
            info!("Joined guild: {} (ID: {})", guild.name, guild.id);

            if let Err(e) = database::ensure_guild(&data.db_pool, to_db_id(guild.id.get()), &guild.name).await {
                error!("Failed to ensure guild in database: {}", e);
            }
        }

        serenity::FullEvent::GuildDelete { incomplete, .. } => {
            info!("Left guild with ID: {}", incomplete.id);
        }

        serenity::FullEvent::GuildMemberAddition { new_member } => {
            handle_member_join(ctx, new_member, data).await?;
        }

        serenity::FullEvent::GuildMemberRemoval { user, guild_id, .. } => {
            handle_member_leave(ctx, user, *guild_id, data).await?;
        }

        serenity::FullEvent::Message { new_message } => {
            handle_message(ctx, new_message, data).await?;
        }

        serenity::FullEvent::VoiceStateUpdate { old, new } => {
            handle_voice_state_update(ctx, old.as_ref(), new, data).await?;
        }

        _ => {}
    }

    Ok(())
}

async fn handle_member_join(
    ctx: &serenity::Context,
    member: &serenity::Member,
    data: &Data,
) -> Result<(), Error> {
    let guild_id_db = member.guild_id.get() as i64;

    let guild = sqlx::query_as!(
        database::models::Guild,
        "SELECT * FROM guilds WHERE id = ?",
        guild_id_db
    )
    .fetch_optional(&data.db_pool)
    .await?;

    if let Some(guild) = guild {
        if guild.welcome_enabled != 0 {
            if let Some(channel_id) = guild.welcome_channel_id {
                if let Ok(ch) = serenity::ChannelId::new(channel_id as u64).to_channel(&ctx.http).await {
                    if let Some(channel) = ch.guild() {
                    let server_name = member.guild_id.to_guild_cached(&ctx.cache)
                        .map(|g| g.name.clone())
                        .unwrap_or_default();

                    let message = guild
                        .welcome_message
                        .unwrap_or_else(|| "Welcome {user} to {server}!".to_string())
                        .replace("{user}", &member.mention().to_string())
                        .replace("{server}", &server_name);

                    let _ = channel.send_message(
                        &ctx.http,
                        serenity::CreateMessage::new().content(message),
                    ).await;
                    }
                }
            }
        }

        let autoroles = sqlx::query_as!(
            database::models::AutoRole,
            r#"SELECT id as "id!", guild_id as "guild_id!", role_id as "role_id!",
                      enabled as "enabled!", created_at as "created_at!"
               FROM autoroles WHERE guild_id = ? AND enabled = 1"#,
            guild_id_db
        )
        .fetch_all(&data.db_pool)
        .await?;

        for autorole in autoroles {
            if let Err(e) = member.add_role(&ctx.http, autorole.role_id as u64).await {
                error!("Failed to add autorole: {}", e);
            }
        }
    }

    Ok(())
}

async fn handle_member_leave(
    ctx: &serenity::Context,
    user: &serenity::User,
    guild_id: serenity::GuildId,
    data: &Data,
) -> Result<(), Error> {
    let guild_id_db = guild_id.get() as i64;

    let guild = sqlx::query_as!(
        database::models::Guild,
        "SELECT * FROM guilds WHERE id = ?",
        guild_id_db
    )
    .fetch_optional(&data.db_pool)
    .await?;

    if let Some(guild) = guild {
        if guild.goodbye_enabled != 0 {
            if let Some(channel_id) = guild.goodbye_channel_id {
                if let Ok(ch) = serenity::ChannelId::new(channel_id as u64).to_channel(&ctx.http).await {
                    if let Some(channel) = ch.guild() {
                    let message = guild
                        .goodbye_message
                        .unwrap_or_else(|| "Goodbye {user}!".to_string())
                        .replace("{user}", &user.name);

                    let _ = channel.send_message(
                        &ctx.http,
                        serenity::CreateMessage::new().content(message),
                    ).await;
                    }
                }
            }
        }
    }

    Ok(())
}

async fn handle_message(
    _ctx: &serenity::Context,
    message: &serenity::Message,
    data: &Data,
) -> Result<(), Error> {
    if message.author.bot {
        return Ok(());
    }

    if let Some(guild_id) = message.guild_id {
        let guild_id_db = guild_id.get() as i64;
        let user_id_db = message.author.id.get() as i64;

        let member = database::get_or_create_member(
            &data.db_pool,
            guild_id_db,
            user_id_db,
            &message.author.name,
        )
        .await?;

        let new_xp = member.xp + (rand::random::<i32>().abs() % 15 + 10) as i64;
        let new_level = (new_xp as f64).sqrt() as i64 / 10;

        sqlx::query!(
            "UPDATE members SET messages_count = messages_count + 1, xp = ?, level = ? WHERE id = ?",
            new_xp,
            new_level,
            member.id
        )
        .execute(&data.db_pool)
        .await?;

        if new_level > member.level {
            let guild = sqlx::query_as!(
                database::models::Guild,
                "SELECT * FROM guilds WHERE id = ?",
                guild_id_db
            )
            .fetch_optional(&data.db_pool)
            .await?;

            if let Some(guild) = guild {
                if guild.level_enabled != 0 {
                    if let Some(channel_id) = guild.level_channel_id {
                        if let Ok(ch) = serenity::ChannelId::new(channel_id as u64).to_channel(&_ctx.http).await {
                            if let Some(channel) = ch.guild() {
                            let msg = guild
                                .level_message
                                .unwrap_or_else(|| "Congratulations {user}! You reached level {level}!".to_string())
                                .replace("{user}", &message.author.mention().to_string())
                                .replace("{level}", &new_level.to_string());

                            let _ = channel.send_message(
                                &_ctx.http,
                                serenity::CreateMessage::new().content(msg),
                            ).await;
                            }
                        }
                    }
                }
            }
        }
    }

    Ok(())
}

async fn handle_voice_state_update(
    ctx: &serenity::Context,
    old: Option<&serenity::VoiceState>,
    new: &serenity::VoiceState,
    data: &Data,
) -> Result<(), Error> {
    let guild_id = match new.guild_id {
        Some(id) => id,
        None => return Ok(()),
    };

    let guild_id_db = guild_id.get() as i64;

    let guild_settings = sqlx::query_as!(
        database::models::Guild,
        "SELECT * FROM guilds WHERE id = ?",
        guild_id_db
    )
    .fetch_optional(&data.db_pool)
    .await?;

    if let Some(settings) = guild_settings {
        if settings.voice_channels_enabled != 0 {
            if let Some(channel_id) = new.channel_id {
                let voice_channels = sqlx::query_as!(
                    database::models::VoiceChannel,
                    r#"SELECT id as "id!", guild_id as "guild_id!", channel_id as "channel_id!",
                              owner_id as "owner_id!", name as "name!", created_at as "created_at!"
                       FROM voice_channels WHERE guild_id = ? AND owner_id = 0"#,
                    guild_id_db
                )
                .fetch_all(&data.db_pool)
                .await?;

                for vc in voice_channels {
                    let channel_id_db = channel_id.get() as i64;
                    if vc.channel_id == channel_id_db {
                        let category_id = settings.voice_channels_category_id.map(|id| serenity::ChannelId::new(id as u64));

                        let template = settings.voice_channels_template.clone()
                            .unwrap_or_else(|| "Voice room - {username}".to_string());
                        let user_name = new.user_id.to_user(&ctx.http).await?.name;
                        let channel_name = template.replace("{username}", &user_name);

                        let mut create_channel = serenity::CreateChannel::new(&channel_name)
                            .kind(serenity::ChannelType::Voice);

                        if let Some(cat_id) = category_id {
                            create_channel = create_channel.category(cat_id);
                        }

                        if let Ok(new_channel) = guild_id.create_channel(&ctx.http, create_channel).await {
                            let user_id = new.user_id;

                            if let Err(e) = guild_id.move_member(&ctx.http, user_id, new_channel.id).await {
                                warn!("Failed to move member to voice channel: {}", e);
                            }

                            let new_channel_id = new_channel.id.get() as i64;
                            let owner_id = user_id.get() as i64;

                            sqlx::query!(
                                "INSERT INTO voice_channels (guild_id, channel_id, owner_id, name) VALUES (?, ?, ?, ?)",
                                guild_id_db,
                                new_channel_id,
                                owner_id,
                                channel_name
                            )
                            .execute(&data.db_pool)
                            .await?;
                        }
                    }
                }
            }

            if let Some(old_state) = old {
                if let Some(old_channel_id) = old_state.channel_id {
                    let old_channel_id_db = old_channel_id.get() as i64;

                    let vc = sqlx::query_as!(
                        database::models::VoiceChannel,
                        r#"SELECT id as "id!", guild_id as "guild_id!", channel_id as "channel_id!",
                                  owner_id as "owner_id!", name as "name!", created_at as "created_at!"
                           FROM voice_channels WHERE channel_id = ? AND owner_id != 0"#,
                        old_channel_id_db
                    )
                    .fetch_optional(&data.db_pool)
                    .await?;

                    if let Some(_vc) = vc {
                        if let Ok(channel) = old_channel_id.to_channel(&ctx.http).await {
                            if let Some(_guild_channel) = channel.guild() {
                                let member_count = ctx.cache.guild(guild_id)
                                    .and_then(|g| g.voice_states.values()
                                        .filter(|vs| vs.channel_id == Some(old_channel_id))
                                        .count()
                                        .into())
                                    .unwrap_or(0);

                                if member_count == 0 {
                                    if let Err(e) = old_channel_id.delete(&ctx.http).await {
                                        warn!("Failed to delete voice channel: {}", e);
                                    } else {
                                        sqlx::query!(
                                            "DELETE FROM voice_channels WHERE channel_id = ?",
                                            old_channel_id_db
                                        )
                                        .execute(&data.db_pool)
                                        .await?;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Ok(())
}
