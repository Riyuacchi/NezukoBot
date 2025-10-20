use crate::handler::{Context, Error};
use crate::utils::embeds::*;
use chrono::{Duration, Utc};
use poise::serenity_prelude as serenity;
use poise::serenity_prelude::Mentionable;

#[poise::command(
    slash_command,
    category = "Admin",
    required_permissions = "ADMINISTRATOR",
    subcommands("setup_welcome", "setup_goodbye", "setup_voice", "setup_logs")
)]
pub async fn setup(ctx: Context<'_>) -> Result<(), Error> {
    let embed = info_embed("Use the subcommands to configure the bot:\n`/setup welcome`, `/setup goodbye`, `/setup voice`, `/setup logs`");
    ctx.send(poise::CreateReply::default().embed(embed).ephemeral(true)).await?;
    Ok(())
}

#[poise::command(slash_command, rename = "welcome")]
async fn setup_welcome(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild = guild_id.to_partial_guild(&ctx.http()).await?;

    let channel = guild.create_channel(&ctx.http(), serenity::CreateChannel::new("welcome")
        .kind(serenity::ChannelType::Text)
        .permissions(vec![
            serenity::PermissionOverwrite {
                allow: serenity::Permissions::VIEW_CHANNEL,
                deny: serenity::Permissions::SEND_MESSAGES,
                kind: serenity::PermissionOverwriteType::Role(serenity::RoleId::from(guild_id.get())),
            }
        ])
    ).await?;

    let channel_id = channel.id.get() as i64;
    let guild_id_db = guild_id.get() as i64;

    sqlx::query!(
        "UPDATE guilds SET welcome_enabled = TRUE, welcome_channel_id = ?, welcome_message = ? WHERE id = ?",
        channel_id,
        "Welcome {user} to {server}!",
        guild_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed(&format!("Welcome system configured. Channel: {}", channel.mention()));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, rename = "goodbye")]
async fn setup_goodbye(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild = guild_id.to_partial_guild(&ctx.http()).await?;

    let channel = guild.create_channel(&ctx.http(), serenity::CreateChannel::new("goodbye")
        .kind(serenity::ChannelType::Text)
        .permissions(vec![
            serenity::PermissionOverwrite {
                allow: serenity::Permissions::VIEW_CHANNEL,
                deny: serenity::Permissions::SEND_MESSAGES,
                kind: serenity::PermissionOverwriteType::Role(serenity::RoleId::from(guild_id.get())),
            }
        ])
    ).await?;

    let channel_id = channel.id.get() as i64;
    let guild_id_db = guild_id.get() as i64;

    sqlx::query!(
        "UPDATE guilds SET goodbye_enabled = TRUE, goodbye_channel_id = ?, goodbye_message = ? WHERE id = ?",
        channel_id,
        "Goodbye {user}!",
        guild_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed(&format!("Goodbye system configured. Channel: {}", channel.mention()));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, rename = "voice")]
async fn setup_voice(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild = guild_id.to_partial_guild(&ctx.http()).await?;

    let category = guild.create_channel(&ctx.http(), serenity::CreateChannel::new("🎙️ Temporary Voice")
        .kind(serenity::ChannelType::Category)
    ).await?;

    let lobby_channel = guild.create_channel(&ctx.http(), serenity::CreateChannel::new("➕ Create a channel")
        .kind(serenity::ChannelType::Voice)
        .category(category.id)
    ).await?;

    let guild_id_db = guild_id.get() as i64;
    let lobby_channel_id = lobby_channel.id.get() as i64;

    sqlx::query!(
        "INSERT INTO voice_channels (guild_id, channel_id, owner_id, name) VALUES (?, ?, 0, ?)",
        guild_id_db,
        lobby_channel_id,
        lobby_channel.name
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let category_id = category.id.get() as i64;
    let guild_id_db2 = guild_id.get() as i64;

    sqlx::query!(
        "UPDATE guilds SET voice_channels_enabled = TRUE, voice_channels_category_id = ?, voice_channels_template = ? WHERE id = ?",
        category_id,
        "Voice room - {username}",
        guild_id_db2
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed("Temporary voice channels configured automatically.")
        .field("Category", category.mention().to_string(), true)
        .field("Lobby channel", lobby_channel.mention().to_string(), true);

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, rename = "logs")]
async fn setup_logs(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild = guild_id.to_partial_guild(&ctx.http()).await?;

    let channel = guild.create_channel(&ctx.http(), serenity::CreateChannel::new("bot-logs")
        .kind(serenity::ChannelType::Text)
        .permissions(vec![
            serenity::PermissionOverwrite {
                allow: serenity::Permissions::empty(),
                deny: serenity::Permissions::VIEW_CHANNEL | serenity::Permissions::SEND_MESSAGES,
                kind: serenity::PermissionOverwriteType::Role(serenity::RoleId::from(guild_id.get())),
            }
        ])
    ).await?;

    let channel_id = channel.id.get() as i64;
    let guild_id_db = guild_id.get() as i64;

    sqlx::query!(
        "UPDATE guilds SET log_channel_id = ? WHERE id = ?",
        channel_id,
        guild_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed(&format!("Logging enabled in {}", channel.mention()));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Admin",
    required_permissions = "ADMINISTRATOR"
)]
pub async fn automod(
    ctx: Context<'_>,
    #[description = "Enable or disable"] enabled: bool,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;

    sqlx::query!(
        "UPDATE guilds SET moderation_enabled = ? WHERE id = ?",
        enabled,
        guild_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let status = if enabled { "enabled" } else { "disabled" };
    let embed = success_embed(&format!("Auto moderation {}", status));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Admin",
    required_permissions = "ADMINISTRATOR",
    subcommands("autorole_add", "autorole_remove", "autorole_list")
)]
pub async fn autorole(ctx: Context<'_>) -> Result<(), Error> {
    let embed = info_embed("Use the subcommands:\n`/autorole add`, `/autorole remove`, `/autorole list`");
    ctx.send(poise::CreateReply::default().embed(embed).ephemeral(true)).await?;
    Ok(())
}

#[poise::command(slash_command, rename = "add")]
async fn autorole_add(
    ctx: Context<'_>,
    #[description = "Role to add"] role: serenity::Role,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;
    let role_id_db = role.id.get() as i64;

    let existing = sqlx::query!(
        "SELECT id FROM autoroles WHERE guild_id = ? AND role_id = ?",
        guild_id_db,
        role_id_db
    )
    .fetch_optional(&ctx.data().db_pool)
    .await?;

    if existing.is_some() {
        ctx.send(poise::CreateReply::default().embed(error_embed("This role is already configured")).ephemeral(true))
            .await?;
        return Ok(());
    }

    sqlx::query!(
        "INSERT INTO autoroles (guild_id, role_id) VALUES (?, ?)",
        guild_id_db,
        role_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed(&format!("{} added to autoroles", role.mention()));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, rename = "remove")]
async fn autorole_remove(
    ctx: Context<'_>,
    #[description = "Role to remove"] role: serenity::Role,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;
    let role_id_db = role.id.get() as i64;

    sqlx::query!(
        "DELETE FROM autoroles WHERE guild_id = ? AND role_id = ?",
        guild_id_db,
        role_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed(&format!("{} removed from autoroles", role.mention()));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, rename = "list")]
async fn autorole_list(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;

    let autoroles = sqlx::query!(
        "SELECT role_id FROM autoroles WHERE guild_id = ? AND enabled = TRUE",
        guild_id_db
    )
    .fetch_all(&ctx.data().db_pool)
    .await?;

    if autoroles.is_empty() {
        ctx.send(poise::CreateReply::default().embed(info_embed("No roles configured")))
            .await?;
        return Ok(());
    }

    let roles: Vec<String> = autoroles
        .iter()
        .map(|r| format!("<@&{}>", r.role_id))
        .collect();

    let embed = info_embed(&roles.join("\n")).title("Autoroles");
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Admin",
    required_permissions = "ADMINISTRATOR"
)]
pub async fn giveaway(
    ctx: Context<'_>,
    #[description = "Duration in minutes"] duration_minutes: i64,
    #[description = "Number of winners"] winners: i32,
    #[description = "Prize"] prize: String,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let end_time = Utc::now() + Duration::minutes(duration_minutes);

    let embed = serenity::CreateEmbed::default()
        .title("🎉 Giveaway")
        .description(format!(
            "**Prize:** {}\n**Winners:** {}\n**Ends:** <t:{}:R>",
            prize,
            winners,
            end_time.timestamp()
        ))
        .footer(serenity::CreateEmbedFooter::new("React with 🎉 to join"))
        .color(serenity::Color::from_rgb(255, 215, 0))
        .timestamp(serenity::Timestamp::from_unix_timestamp(end_time.timestamp())?);

    let message = ctx.send(poise::CreateReply::default().embed(embed)).await?.into_message().await?;
    message.react(&ctx.http(), '🎉').await?;

    let guild_id_db = guild_id.get() as i64;
    let channel_id_db = ctx.channel_id().get() as i64;
    let message_id_db = message.id.get() as i64;
    let host_id_db = ctx.author().id.get() as i64;
    let end_time_str = end_time.to_rfc3339();

    sqlx::query!(
        "INSERT INTO giveaways (guild_id, channel_id, message_id, prize, winners_count, host_id, active, end_time) VALUES (?, ?, ?, ?, ?, ?, TRUE, ?)",
        guild_id_db,
        channel_id_db,
        message_id_db,
        prize,
        winners,
        host_id_db,
        end_time_str
    )
    .execute(&ctx.data().db_pool)
    .await?;

    Ok(())
}
