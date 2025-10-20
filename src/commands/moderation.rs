use crate::handler::{Context, Error};
use crate::utils::embeds::*;
use chrono::Utc;
use poise::serenity_prelude as serenity;
use poise::serenity_prelude::Mentionable;

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "BAN_MEMBERS",
    required_bot_permissions = "BAN_MEMBERS"
)]
pub async fn ban(
    ctx: Context<'_>,
    #[description = "Member to ban"] member: serenity::Member,
    #[description = "Reason"] reason: Option<String>,
) -> Result<(), Error> {
    let reason = reason.unwrap_or_else(|| "No reason provided".to_string());

    member.ban_with_reason(&ctx.http(), 0, &reason).await?;

    let embed = success_embed(&format!("{} was banned\n**Reason:** {}", member.user.name, reason));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "BAN_MEMBERS",
    required_bot_permissions = "BAN_MEMBERS"
)]
pub async fn unban(
    ctx: Context<'_>,
    #[description = "User ID to unban"] user_id: String,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let user_id: u64 = user_id.parse()?;

    guild_id.unban(&ctx.http(), user_id).await?;

    let embed = success_embed(&format!("<@{}> was unbanned", user_id));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "KICK_MEMBERS",
    required_bot_permissions = "KICK_MEMBERS"
)]
pub async fn kick(
    ctx: Context<'_>,
    #[description = "Member to kick"] member: serenity::Member,
    #[description = "Reason"] reason: Option<String>,
) -> Result<(), Error> {
    let reason = reason.unwrap_or_else(|| "No reason provided".to_string());

    member.kick_with_reason(&ctx.http(), &reason).await?;

    let embed = success_embed(&format!("{} was kicked\n**Reason:** {}", member.user.name, reason));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MODERATE_MEMBERS"
)]
pub async fn warn(
    ctx: Context<'_>,
    #[description = "Member to warn"] member: serenity::Member,
    #[description = "Reason"] reason: String,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;
    let user_id_db = member.user.id.get() as i64;
    let moderator_id_db = ctx.author().id.get() as i64;

    sqlx::query!(
        "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, active) VALUES (?, ?, ?, ?, TRUE)",
        guild_id_db,
        user_id_db,
        moderator_id_db,
        reason
    )
    .execute(&ctx.data().db_pool)
    .await?;

    sqlx::query!(
        "UPDATE members SET warnings_count = warnings_count + 1 WHERE guild_id = ? AND user_id = ?",
        guild_id_db,
        user_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let warnings_count = sqlx::query_scalar!(
        "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ? AND active = TRUE",
        guild_id_db,
        user_id_db
    )
    .fetch_one(&ctx.data().db_pool)
    .await? as i64;

    let embed = success_embed(&format!("{} has been warned", member.user.name))
        .field("Reason", reason, false)
        .field("Warning count", warnings_count.to_string(), false);

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Moderation")]
pub async fn warnings(
    ctx: Context<'_>,
    #[description = "Member to check warnings"] member: Option<serenity::Member>,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let target = member.as_ref().map(|m| &m.user).unwrap_or_else(|| ctx.author());

    let guild_id_db = guild_id.get() as i64;
    let target_id_db = target.id.get() as i64;

    let warnings = sqlx::query!(
        "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? AND active = TRUE ORDER BY created_at DESC LIMIT 10",
        guild_id_db,
        target_id_db
    )
    .fetch_all(&ctx.data().db_pool)
    .await?;

    if warnings.is_empty() {
        ctx.send(poise::CreateReply::default().embed(info_embed(&format!("{} has no warnings", target.name))))
            .await?;
        return Ok(());
    }

    let mut embed = serenity::CreateEmbed::default()
        .title(format!("⚠️ Warnings for {}", target.name))
        .color(serenity::Color::from_rgb(243, 156, 18));

    for (i, warn) in warnings.iter().enumerate() {
        embed = embed.field(
            format!("Warning #{}", i + 1),
            format!(
                "**Moderator:** <@{}>\n**Reason:** {}",
                warn.moderator_id,
                warn.reason
            ),
            false,
        );
    }

    embed = embed.footer(serenity::CreateEmbedFooter::new(format!("Total: {} warning(s)", warnings.len())));

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MODERATE_MEMBERS"
)]
pub async fn clearwarnings(
    ctx: Context<'_>,
    #[description = "Member to clear warnings"] member: serenity::Member,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;
    let user_id_db = member.user.id.get() as i64;

    sqlx::query!(
        "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
        guild_id_db,
        user_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    sqlx::query!(
        "UPDATE members SET warnings_count = 0 WHERE guild_id = ? AND user_id = ?",
        guild_id_db,
        user_id_db
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed(&format!("All warnings for {} have been cleared", member.user.name));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MODERATE_MEMBERS",
    required_bot_permissions = "MODERATE_MEMBERS"
)]
pub async fn mute(
    ctx: Context<'_>,
    #[description = "Member to mute"] mut member: serenity::Member,
    #[description = "Duration in minutes"] duration: i64,
    #[description = "Reason"] reason: Option<String>,
) -> Result<(), Error> {
    let reason = reason.unwrap_or_else(|| "No reason provided".to_string());
    let duration_time = serenity::Timestamp::from_unix_timestamp(Utc::now().timestamp() + (duration * 60))?;

    member.disable_communication_until_datetime(&ctx.http(), duration_time).await?;

    let embed = success_embed(&format!("{} was muted for {} minutes\n**Reason:** {}", member.user.name, duration, reason));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MODERATE_MEMBERS",
    required_bot_permissions = "MODERATE_MEMBERS"
)]
pub async fn unmute(
    ctx: Context<'_>,
    #[description = "Member to unmute"] mut member: serenity::Member,
) -> Result<(), Error> {
    member.enable_communication(&ctx.http()).await?;

    let embed = success_embed(&format!("{} is no longer muted", member.user.name));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MODERATE_MEMBERS",
    required_bot_permissions = "MODERATE_MEMBERS"
)]
pub async fn timeout(
    ctx: Context<'_>,
    #[description = "Member to timeout"] mut member: serenity::Member,
    #[description = "Duration in hours"] hours: i64,
    #[description = "Reason"] reason: Option<String>,
) -> Result<(), Error> {
    let reason = reason.unwrap_or_else(|| "No reason provided".to_string());
    let duration_time = serenity::Timestamp::from_unix_timestamp(Utc::now().timestamp() + (hours * 3600))?;

    member.disable_communication_until_datetime(&ctx.http(), duration_time).await?;

    let embed = success_embed(&format!("{} was timed out for {} hour(s)\n**Reason:** {}", member.user.name, hours, reason));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MANAGE_CHANNELS",
    required_bot_permissions = "MANAGE_CHANNELS"
)]
pub async fn lock(
    ctx: Context<'_>,
    #[description = "Channel to lock"] channel: Option<serenity::GuildChannel>,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let channel_id = channel.map(|c| c.id).unwrap_or_else(|| ctx.channel_id());

    let target_channel = channel_id.to_channel(&ctx.http()).await?.guild().ok_or("Not a guild channel")?;

    let everyone_role = guild_id;
    target_channel.create_permission(&ctx.http(), serenity::PermissionOverwrite {
        allow: serenity::Permissions::empty(),
        deny: serenity::Permissions::SEND_MESSAGES,
        kind: serenity::PermissionOverwriteType::Role(serenity::RoleId::from(everyone_role.get())),
    }).await?;

    let embed = success_embed(&format!("{} has been locked 🔒", target_channel.mention()));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MANAGE_CHANNELS",
    required_bot_permissions = "MANAGE_CHANNELS"
)]
pub async fn unlock(
    ctx: Context<'_>,
    #[description = "Channel to unlock"] channel: Option<serenity::GuildChannel>,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let channel_id = channel.map(|c| c.id).unwrap_or_else(|| ctx.channel_id());

    let target_channel = channel_id.to_channel(&ctx.http()).await?.guild().ok_or("Not a guild channel")?;

    let everyone_role = guild_id;
    target_channel.create_permission(&ctx.http(), serenity::PermissionOverwrite {
        allow: serenity::Permissions::SEND_MESSAGES,
        deny: serenity::Permissions::empty(),
        kind: serenity::PermissionOverwriteType::Role(serenity::RoleId::from(everyone_role.get())),
    }).await?;

    let embed = success_embed(&format!("{} has been unlocked 🔓", target_channel.mention()));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MANAGE_CHANNELS",
    required_bot_permissions = "MANAGE_CHANNELS"
)]
pub async fn slowmode(
    ctx: Context<'_>,
    #[description = "Delay in seconds"] seconds: u16,
    #[description = "Channel"] channel: Option<serenity::GuildChannel>,
) -> Result<(), Error> {
    if seconds > 21600 {
        ctx.send(poise::CreateReply::default().embed(error_embed("Delay must be between 0 and 21600 seconds")))
            .await?;
        return Ok(());
    }

    let channel_id = channel.map(|c| c.id).unwrap_or_else(|| ctx.channel_id());
    let mut target_channel = channel_id.to_channel(&ctx.http()).await?.guild().ok_or("Not a guild channel")?;

    target_channel.edit(&ctx.http(), serenity::EditChannel::new().rate_limit_per_user(seconds)).await?;

    let embed = if seconds == 0 {
        success_embed(&format!("Slowmode disabled for {}", target_channel.mention()))
    } else {
        success_embed(&format!("Slowmode set to {}s for {}", seconds, target_channel.mention()))
    };

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(
    slash_command,
    category = "Moderation",
    required_permissions = "MANAGE_MESSAGES",
    required_bot_permissions = "MANAGE_MESSAGES"
)]
pub async fn purge(
    ctx: Context<'_>,
    #[description = "Number of messages to delete"] amount: u8,
) -> Result<(), Error> {
    if amount == 0 || amount > 100 {
        ctx.send(poise::CreateReply::default().embed(error_embed("You must provide a number between 1 and 100")).ephemeral(true))
            .await?;
        return Ok(());
    }

    let messages = ctx.channel_id().messages(&ctx.http(), serenity::GetMessages::new().limit(amount)).await?;
    ctx.channel_id().delete_messages(&ctx.http(), messages).await?;

    let reply = ctx.send(poise::CreateReply::default().embed(success_embed(&format!("{} message(s) deleted", amount))))
        .await?;

    tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
    reply.delete(ctx).await?;

    Ok(())
}
