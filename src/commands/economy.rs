use crate::database;
use crate::handler::{Context, Error};
use crate::utils::embeds::*;
use crate::utils::format_number;
use poise::serenity_prelude as serenity;
use rand::Rng;
use serde_json::json;

#[poise::command(slash_command, category = "Economy")]
pub async fn balance(
    ctx: Context<'_>,
    #[description = "User to check balance"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let user = user.as_ref().unwrap_or_else(|| ctx.author());
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;
    let user_id_db = user.id.get() as i64;

    let member = database::get_or_create_member(&ctx.data().db_pool, guild_id_db, user_id_db, &user.name).await?;

    let embed = serenity::CreateEmbed::default()
        .title(format!("💰 Balance for {}", user.name))
        .thumbnail(user.face())
        .field("💵 Wallet", format_number(member.coins as i64), true)
        .field("🏦 Bank", format_number(member.bank as i64), true)
        .field("💎 Total", format_number((member.coins + member.bank) as i64), true)
        .color(serenity::Color::from_rgb(255, 215, 0));

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Economy")]
pub async fn work(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild_id_db = guild_id.get() as i64;
    let user_id_db = ctx.author().id.get() as i64;

    let member = database::get_or_create_member(&ctx.data().db_pool, guild_id_db, user_id_db, &ctx.author().name).await?;

    let jobs = ["developer", "doctor", "lawyer", "teacher", "engineer", "artist", "musician", "chef", "architect", "scientist"];
    let (job, earned) = {
        let mut rng = rand::thread_rng();
        let job = jobs[rng.gen_range(0..jobs.len())];
        let earned = rng.gen_range(100..=500);
        (job, earned)
    };

    sqlx::query!(
        "UPDATE members SET coins = coins + ?, last_work = CURRENT_TIMESTAMP WHERE id = ?",
        earned,
        member.id
    )
    .execute(&ctx.data().db_pool)
    .await?;

    sqlx::query!(
        "UPDATE economy SET total_earned = total_earned + ?, work_streak = work_streak + 1 WHERE member_id = ?",
        earned,
        member.id
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed(&format!("You worked as **{}** and earned **{}** coins", job, earned));
    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Economy")]
pub async fn daily(ctx: Context<'_>) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild_id_db = guild_id.get() as i64;
    let user_id_db = ctx.author().id.get() as i64;

    let member = database::get_or_create_member(&ctx.data().db_pool, guild_id_db, user_id_db, &ctx.author().name).await?;

    let base_reward = 500;
    let mut streak_bonus = 0;

    let economy = sqlx::query!("SELECT daily_streak FROM economy WHERE member_id = ?", member.id)
        .fetch_optional(&ctx.data().db_pool)
        .await?;

    if let Some(eco) = economy {
        streak_bonus = (eco.daily_streak * 50).min(500);
    }

    let total_reward = base_reward + streak_bonus;

    sqlx::query!(
        "UPDATE members SET coins = coins + ?, last_daily = CURRENT_TIMESTAMP WHERE id = ?",
        total_reward,
        member.id
    )
    .execute(&ctx.data().db_pool)
    .await?;

    sqlx::query!(
        "UPDATE economy SET total_earned = total_earned + ?, daily_streak = daily_streak + 1 WHERE member_id = ?",
        total_reward,
        member.id
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let mut embed = success_embed(&format!("You received your daily reward of **{}** coins", total_reward));
    if streak_bonus > 0 {
        embed = embed.field("🔥 Streak Bonus", format!("{} coins", streak_bonus), false);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Economy")]
pub async fn shop(ctx: Context<'_>) -> Result<(), Error> {
    let embed = serenity::CreateEmbed::default()
        .title("🛒 Shop")
        .description("Use `/buy <item>` to purchase an item")
        .field("⭐ VIP Pass", "VIP role for 30 days\n**Price:** 10,000 💰\n**ID:** `vip`", false)
        .field("🎨 Custom Color", "Role with a custom color\n**Price:** 5,000 💰\n**ID:** `color`", false)
        .field("⚡ XP Boost x2", "Double XP for 24 hours\n**Price:** 3,000 💰\n**ID:** `boost`", false)
        .field("💰 Coin Pack", "Bonus 1,000 coins\n**Price:** 1,000 💰\n**ID:** `coins`", false)
        .color(serenity::Color::from_rgb(52, 152, 219));

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Economy")]
pub async fn buy(
    ctx: Context<'_>,
    #[description = "Item ID to buy"] item: String,
) -> Result<(), Error> {
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild_id_db = guild_id.get() as i64;
    let user_id_db = ctx.author().id.get() as i64;

    let member = database::get_or_create_member(&ctx.data().db_pool, guild_id_db, user_id_db, &ctx.author().name).await?;

    let (item_name, price) = match item.as_str() {
        "vip" => ("VIP Pass", 10000),
        "color" => ("Custom Color", 5000),
        "boost" => ("XP Boost x2", 3000),
        "coins" => ("Coin Pack", 1000),
        _ => {
            ctx.send(poise::CreateReply::default().embed(error_embed("Item not found in the shop")))
                .await?;
            return Ok(());
        }
    };

    if member.coins < price {
        ctx.send(poise::CreateReply::default().embed(error_embed(&format!(
            "You do not have enough coins. Cost: {} 💰",
            format_number(price as i64)
        )))).await?;
        return Ok(());
    }

    sqlx::query!(
        "UPDATE members SET coins = coins - ? WHERE id = ?",
        price,
        member.id
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let economy = sqlx::query!("SELECT inventory FROM economy WHERE member_id = ?", member.id)
        .fetch_optional(&ctx.data().db_pool)
        .await?;

    if let Some(eco) = economy {
        let inventory_str = eco.inventory.unwrap_or_else(|| "{}".to_string());
        let mut inventory: serde_json::Value = serde_json::from_str(&inventory_str).unwrap_or(json!({}));

        if let Some(obj) = inventory.as_object_mut() {
            let count = obj.get(&item).and_then(|v| v.as_i64()).unwrap_or(0);
            obj.insert(item.clone(), json!(count + 1));
        }

        let inventory_str = inventory.to_string();

        sqlx::query!(
            "UPDATE economy SET inventory = ?, total_spent = total_spent + ? WHERE member_id = ?",
            inventory_str,
            price,
            member.id
        )
        .execute(&ctx.data().db_pool)
        .await?;
    }

    let embed = success_embed(&format!("You purchased **{}**", item_name))
        .field("Price", format!("{} 💰", format_number(price as i64)), true)
        .field("Remaining balance", format!("{} 💰", format_number((member.coins - price) as i64)), true);

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Economy")]
pub async fn inventory(
    ctx: Context<'_>,
    #[description = "User to check inventory"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let user = user.as_ref().unwrap_or_else(|| ctx.author());
    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;

    let guild_id_db = guild_id.get() as i64;
    let user_id_db = user.id.get() as i64;

    let member = database::get_or_create_member(&ctx.data().db_pool, guild_id_db, user_id_db, &user.name).await?;

    let economy = sqlx::query!("SELECT inventory FROM economy WHERE member_id = ?", member.id)
        .fetch_optional(&ctx.data().db_pool)
        .await?;

    let mut embed = serenity::CreateEmbed::default()
        .title(format!("🎒 Inventory for {}", user.name))
        .thumbnail(user.face())
        .color(serenity::Color::from_rgb(155, 89, 182));

    if let Some(eco) = economy {
        if let Some(inv_str) = eco.inventory {
            if let Ok(inventory) = serde_json::from_str::<serde_json::Value>(&inv_str) {
                if let Some(obj) = inventory.as_object() {
                    if obj.is_empty() {
                        embed = embed.description("Inventory empty");
                    } else {
                        for (item_id, quantity) in obj {
                            let item_name = match item_id.as_str() {
                                "vip" => "⭐ VIP Pass",
                                "color" => "🎨 Custom Color",
                                "boost" => "⚡ XP Boost x2",
                                "coins" => "💰 Coin Pack",
                                _ => item_id,
                            };
                            embed = embed.field(item_name, format!("Quantity: {}", quantity), true);
                        }
                    }
                } else {
                    embed = embed.description("Inventory empty");
                }
            } else {
                embed = embed.description("Inventory empty");
            }
        } else {
            embed = embed.description("Inventory empty");
        }
    } else {
        embed = embed.description("Inventory empty");
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Economy")]
pub async fn transfer(
    ctx: Context<'_>,
    #[description = "User to transfer to"] user: serenity::User,
    #[description = "Amount to transfer"] amount: i64,
) -> Result<(), Error> {
    if user.bot {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot transfer coins to a bot")))
            .await?;
        return Ok(());
    }

    if user.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot transfer coins to yourself")))
            .await?;
        return Ok(());
    }

    if amount <= 0 {
        ctx.send(poise::CreateReply::default().embed(error_embed("Amount must be greater than 0")))
            .await?;
        return Ok(());
    }

    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild_id_db = guild_id.get() as i64;
    let author_id_db = ctx.author().id.get() as i64;
    let user_id_db = user.id.get() as i64;

    let sender = database::get_or_create_member(&ctx.data().db_pool, guild_id_db, author_id_db, &ctx.author().name).await?;

    if sender.coins < amount {
        ctx.send(poise::CreateReply::default().embed(error_embed(&format!(
            "You do not have enough coins. Balance: {} 💰",
            format_number(sender.coins as i64)
        )))).await?;
        return Ok(());
    }

    let receiver = database::get_or_create_member(&ctx.data().db_pool, guild_id_db, user_id_db, &user.name).await?;

    sqlx::query!(
        "UPDATE members SET coins = coins - ? WHERE id = ?",
        amount,
        sender.id
    )
    .execute(&ctx.data().db_pool)
    .await?;

    sqlx::query!(
        "UPDATE members SET coins = coins + ? WHERE id = ?",
        amount,
        receiver.id
    )
    .execute(&ctx.data().db_pool)
    .await?;

    let embed = success_embed(&format!("You transferred {} 💰 to {}", format_number(amount), user.name))
        .field("Your new balance", format!("{} 💰", format_number(sender.coins - amount)), true);

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Economy")]
pub async fn gamble(
    ctx: Context<'_>,
    #[description = "Amount to gamble"] amount: i64,
) -> Result<(), Error> {
    if amount <= 0 {
        ctx.send(poise::CreateReply::default().embed(error_embed("Amount must be greater than 0")))
            .await?;
        return Ok(());
    }

    let guild_id = ctx.guild_id().ok_or("This command can only be used in a guild")?;
    let guild_id_db = guild_id.get() as i64;
    let user_id_db = ctx.author().id.get() as i64;

    let member = database::get_or_create_member(&ctx.data().db_pool, guild_id_db, user_id_db, &ctx.author().name).await?;

    if member.coins < amount {
        ctx.send(poise::CreateReply::default().embed(error_embed(&format!(
            "You do not have enough coins. Balance: {} 💰",
            format_number(member.coins as i64)
        )))).await?;
        return Ok(());
    }

    let win = rand::random::<bool>();

    let embed = if win {
        sqlx::query!(
            "UPDATE members SET coins = coins + ? WHERE id = ?",
            amount,
            member.id
        )
        .execute(&ctx.data().db_pool)
        .await?;

        serenity::CreateEmbed::default()
            .title("🎰 You won!")
            .description(format!("You gambled **{}** coins and won **{}** coins", format_number(amount), format_number(amount)))
            .field("New balance", format!("{} 💰", format_number(member.coins + amount)), true)
            .color(serenity::Color::from_rgb(46, 204, 113))
    } else {
        sqlx::query!(
            "UPDATE members SET coins = coins - ? WHERE id = ?",
            amount,
            member.id
        )
        .execute(&ctx.data().db_pool)
        .await?;

        serenity::CreateEmbed::default()
            .title("🎰 You lost!")
            .description(format!("You gambled **{}** coins and lost everything", format_number(amount)))
            .field("New balance", format!("{} 💰", format_number(member.coins - amount)), true)
            .color(serenity::Color::from_rgb(231, 76, 60))
    };

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}
