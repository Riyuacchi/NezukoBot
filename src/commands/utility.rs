use crate::handler::{Context, Error};
use crate::utils::embeds::*;
use crate::utils::format_number;
use poise::serenity_prelude as serenity;
use poise::serenity_prelude::Mentionable;

#[poise::command(slash_command, category = "Utility")]
pub async fn help(ctx: Context<'_>) -> Result<(), Error> {
    let embed = default_embed()
        .title("📚 Nezuko Bot - Help Menu")
        .description("Here are all available command categories")
        .field("🔧 Utility", "`/help`, `/ping`, `/invite`, `/userinfo`, `/serverinfo`, `/avatar`, `/rank`, `/leaderboard`", false)
        .field("🎉 Fun", "`/hug`, `/kiss`, `/pat`, `/slap`, `/cuddle`, `/poke`, `/bite`, `/lick`, `/tickle`, `/8ball`, `/joke`, `/meme`", false)
        .field("💰 Economy", "`/balance`, `/work`, `/daily`, `/shop`, `/buy`, `/inventory`, `/transfer`, `/gamble`", false)
        .field("🛡️ Moderation", "`/ban`, `/unban`, `/kick`, `/warn`, `/warnings`, `/clearwarnings`, `/mute`, `/unmute`, `/timeout`, `/lock`, `/unlock`, `/slowmode`, `/purge`", false)
        .field("⚙️ Admin", "`/setup`, `/automod`, `/autorole`, `/giveaway`", false)
        .footer(serenity::CreateEmbedFooter::new("Made with ❤️ in Rust"));

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Utility")]
pub async fn ping(ctx: Context<'_>) -> Result<(), Error> {
    let latency = ctx.ping().await.as_millis();

    let (color, status) = if latency < 100 {
        (serenity::Color::from_rgb(46, 204, 113), "Excellent")
    } else if latency < 200 {
        (serenity::Color::from_rgb(243, 156, 18), "Good")
    } else {
        (serenity::Color::from_rgb(231, 76, 60), "Slow")
    };

    let embed = serenity::CreateEmbed::default()
        .title("🏓 Pong!")
        .field("Latency", format!("{}ms", latency), true)
        .field("Status", status, true)
        .color(color);

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Utility")]
pub async fn invite(ctx: Context<'_>) -> Result<(), Error> {
    let bot_id = ctx.cache().current_user().id;

    let permissions = serenity::Permissions::VIEW_CHANNEL
        | serenity::Permissions::SEND_MESSAGES
        | serenity::Permissions::MANAGE_MESSAGES
        | serenity::Permissions::EMBED_LINKS
        | serenity::Permissions::ATTACH_FILES
        | serenity::Permissions::READ_MESSAGE_HISTORY
        | serenity::Permissions::ADD_REACTIONS
        | serenity::Permissions::USE_EXTERNAL_EMOJIS
        | serenity::Permissions::MANAGE_CHANNELS
        | serenity::Permissions::MANAGE_ROLES
        | serenity::Permissions::KICK_MEMBERS
        | serenity::Permissions::BAN_MEMBERS
        | serenity::Permissions::MODERATE_MEMBERS
        | serenity::Permissions::CONNECT
        | serenity::Permissions::SPEAK
        | serenity::Permissions::MOVE_MEMBERS
        | serenity::Permissions::MUTE_MEMBERS
        | serenity::Permissions::DEAFEN_MEMBERS
        | serenity::Permissions::USE_VAD;

    let invite_url = format!(
        "https://discord.com/api/oauth2/authorize?client_id={}&permissions={}&scope=bot%20applications.commands",
        bot_id,
        permissions.bits()
    );

    let embed = default_embed()
        .title("📨 Invite Nezuko Bot")
        .description(format!("Use the link below to invite **Nezuko** to your server!"))
        .field("Invite Link", format!("[Click here]({})", invite_url), false);

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Utility")]
pub async fn userinfo(
    ctx: Context<'_>,
    #[description = "User to get info about"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let user = user.as_ref().unwrap_or_else(|| ctx.author());
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let member = guild_id.member(ctx, user.id).await?;

    let mut embed = default_embed()
        .title(format!("👤 Information about {}", user.name))
        .thumbnail(user.face())
        .field("ID", user.id.to_string(), true)
        .field("Display Name", member.display_name().to_string(), true)
        .field("Bot", if user.bot { "✅" } else { "❌" }, true)
        .field(
            "Account Created",
            format!("<t:{}:F>\n<t:{}:R>", user.created_at().unix_timestamp(), user.created_at().unix_timestamp()),
            false,
        );

    if let Some(joined_at) = member.joined_at {
        embed = embed.field(
            "Joined Server",
            format!("<t:{}:F>\n<t:{}:R>", joined_at.unix_timestamp(), joined_at.unix_timestamp()),
            false,
        );
    }

    let roles: Vec<String> = if let Some(guild) = guild_id.to_guild_cached(&ctx.cache()) {
        member
            .roles
            .iter()
            .filter_map(|r| guild.roles.get(r).map(|role| role.mention().to_string()))
            .collect()
    } else {
        Vec::new()
    };

    if !roles.is_empty() {
        embed = embed.field(format!("Roles ({})", roles.len()), roles.join(" "), false);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Utility")]
pub async fn serverinfo(ctx: Context<'_>) -> Result<(), Error> {
    let _guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild = match ctx.partial_guild().await {
        Some(g) => g,
        None => return Err("Could not fetch guild".into()),
    };

    let mut embed = default_embed()
        .title(format!("📊 Information about {}", guild.name))
        .field("ID", guild.id.to_string(), true)
        .field("Owner", format!("<@{}>", guild.owner_id), true)
        .field(
            "Created",
            format!("<t:{}:R>", guild.id.created_at().unix_timestamp()),
            true,
        );

    if let Some(icon) = guild.icon_url() {
        embed = embed.thumbnail(icon);
    }

    if let Some(description) = &guild.description {
        embed = embed.field("Description", description, false);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Utility")]
pub async fn avatar(
    ctx: Context<'_>,
    #[description = "User to get avatar"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let user = user.as_ref().unwrap_or_else(|| ctx.author());

    let embed = default_embed()
        .title(format!("🖼️ Avatar for {}", user.name))
        .image(user.face())
        .field(
            "Links",
            format!(
                "[PNG]({}) | [JPG]({}) | [WEBP]({})",
                user.face().replace("webp", "png"),
                user.face().replace("webp", "jpg"),
                user.face()
            ),
            false,
        );

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Utility")]
pub async fn rank(
    ctx: Context<'_>,
    #[description = "User to get rank"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let user = user.as_ref().unwrap_or_else(|| ctx.author());
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;
    let user_id_db = user.id.get() as i64;

    let member = sqlx::query_as!(
        crate::database::models::Member,
        r#"SELECT id as "id!", guild_id as "guild_id!", user_id as "user_id!", username as "username!",
                  xp as "xp!", level as "level!", messages_count as "messages_count!",
                  voice_time as "voice_time!", coins as "coins!", bank as "bank!",
                  last_daily, last_weekly, last_work,
                  warnings_count as "warnings_count!", is_banned as "is_banned!",
                  created_at as "created_at!", updated_at as "updated_at!"
           FROM members WHERE guild_id = ? AND user_id = ?"#,
        guild_id_db,
        user_id_db
    )
    .fetch_optional(&ctx.data().db_pool)
    .await?;

    let member = member.ok_or("No data found for this member")?;

    let rank = sqlx::query_scalar!(
        "SELECT COUNT(*) + 1 FROM members WHERE guild_id = ? AND xp > ?",
        guild_id_db,
        member.xp
    )
    .fetch_one(&ctx.data().db_pool)
    .await? as i64;

    let xp_for_next = (member.level + 1).pow(2) * 100;
    let xp_progress = member.xp - member.level.pow(2) * 100;
    let xp_needed = xp_for_next - member.level.pow(2) * 100;

    let progress_bar = create_progress_bar(xp_progress, xp_needed, 10);

    let embed = default_embed()
        .title(format!("📊 Rank of {}", user.name))
        .thumbnail(user.face())
        .field("Rank", format!("#{}", rank), true)
        .field("Level", member.level.to_string(), true)
        .field("XP", format_number(member.xp as i64), true)
        .field(
            "Progress",
            format!("{}\n{}/{} XP", progress_bar, xp_progress, xp_needed),
            false,
        )
        .field("Messages", format_number(member.messages_count as i64), true)
        .field(
            "Voice Time",
            format!("{}h {}m", member.voice_time / 60, member.voice_time % 60),
            true,
        );

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Utility")]
pub async fn leaderboard(
    ctx: Context<'_>,
    #[description = "Page number"] page: Option<i32>,
) -> Result<(), Error> {
    let page = page.unwrap_or(1).max(1);
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;

    let per_page = 10;
    let offset = (page - 1) * per_page;

    let members = sqlx::query_as!(
        crate::database::models::Member,
        r#"SELECT id as "id!", guild_id as "guild_id!", user_id as "user_id!", username as "username!",
                  xp as "xp!", level as "level!", messages_count as "messages_count!",
                  voice_time as "voice_time!", coins as "coins!", bank as "bank!",
                  last_daily, last_weekly, last_work,
                  warnings_count as "warnings_count!", is_banned as "is_banned!",
                  created_at as "created_at!", updated_at as "updated_at!"
           FROM members WHERE guild_id = ? ORDER BY xp DESC LIMIT ? OFFSET ?"#,
        guild_id_db,
        per_page,
        offset
    )
    .fetch_all(&ctx.data().db_pool)
    .await?;

    if members.is_empty() {
        ctx.send(poise::CreateReply::default().embed(error_embed("No members in the leaderboard")))
            .await?;
        return Ok(());
    }

    let guild_name = guild_id.name(ctx).unwrap_or_else(|| "Server".to_string());

    let mut embed = serenity::CreateEmbed::default()
        .title(format!("🏆 Leaderboard for {}", guild_name))
        .description(format!("Page {}", page))
        .color(serenity::Color::from_rgb(255, 215, 0));

    for (i, member) in members.iter().enumerate() {
        let rank = offset + i as i32 + 1;
        let medal = match rank {
            1 => "🥇",
            2 => "🥈",
            3 => "🥉",
            _ => "▪️",
        };

        if let Ok(user) = serenity::UserId::new(member.user_id as u64).to_user(ctx).await {
            embed = embed.field(
                format!("{} #{} {}", medal, rank, user.name),
                format!(
                    "Level {} - {} XP\n{} messages",
                    member.level, format_number(member.xp as i64), member.messages_count
                ),
                false,
            );
        }
    }

    let total = sqlx::query_scalar!(
        "SELECT COUNT(*) FROM members WHERE guild_id = ?",
        guild_id_db
    )
    .fetch_one(&ctx.data().db_pool)
    .await? as i64;

    let total_pages = ((total + per_page as i64 - 1) / per_page as i64) as i32;
    embed = embed.footer(serenity::CreateEmbedFooter::new(format!(
        "Page {}/{} - Total: {} members",
        page, total_pages, total
    )));

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

fn create_progress_bar(current: i64, total: i64, length: usize) -> String {
    let percentage = if total == 0 {
        0.0
    } else {
        (current as f32 / total as f32).min(1.0)
    };

    let filled = (length as f32 * percentage) as usize;
    let bar = "█".repeat(filled) + &"░".repeat(length - filled);
    format!("`{}`", bar)
}
