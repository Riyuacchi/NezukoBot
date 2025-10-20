use crate::handler::{Context, Error};
use crate::utils::embeds::*;
use poise::serenity_prelude as serenity;
use rand::Rng;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct KawaiiResponse {
    response: String,
}

#[derive(Debug, Deserialize)]
struct MemeResponse {
    title: String,
    url: String,
    #[serde(rename = "postLink")]
    post_link: String,
    subreddit: String,
    ups: i32,
}

async fn get_kawaii_gif(endpoint: &str, api_key: Option<&String>) -> Result<Option<String>, Error> {
    let client = reqwest::Client::new();
    let mut request = client.get(format!("https://kawaii.red/api/gif/{}", endpoint));

    if let Some(key) = api_key {
        request = request.header("Authorization", format!("Bearer {}", key));
    }

    let response = request.send().await?;
    if response.status().is_success() {
        let data: KawaiiResponse = response.json().await?;
        Ok(Some(data.response))
    } else {
        Ok(None)
    }
}

#[poise::command(slash_command, category = "Fun")]
pub async fn hug(
    ctx: Context<'_>,
    #[description = "User to hug"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot hug yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("hug", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** gives **{}** a hug 🤗", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(255, 192, 203));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn kiss(
    ctx: Context<'_>,
    #[description = "User to kiss"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot kiss yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("kiss", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** kisses **{}** 💋", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(231, 76, 60));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn pat(
    ctx: Context<'_>,
    #[description = "User to pat"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot pat yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("pat", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** pats **{}** ✋", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(52, 152, 219));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn slap(
    ctx: Context<'_>,
    #[description = "User to slap"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot slap yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("slap", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** slaps **{}** 👋", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(231, 76, 60));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn cuddle(
    ctx: Context<'_>,
    #[description = "User to cuddle"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot cuddle yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("cuddle", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** cuddles **{}** 🥰", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(255, 192, 203));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn poke(
    ctx: Context<'_>,
    #[description = "User to poke"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot poke yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("poke", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** pokes **{}** 👉", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(243, 156, 18));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn bite(
    ctx: Context<'_>,
    #[description = "User to bite"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot bite yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("bite", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** bites **{}** 🦷", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(155, 89, 182));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn lick(
    ctx: Context<'_>,
    #[description = "User to lick"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot lick yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("lick", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** licks **{}** 👅", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(233, 30, 99));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn tickle(
    ctx: Context<'_>,
    #[description = "User to tickle"] member: serenity::User,
) -> Result<(), Error> {
    if member.id == ctx.author().id {
        ctx.send(poise::CreateReply::default().embed(error_embed("You cannot tickle yourself")))
            .await?;
        return Ok(());
    }

    let gif_url = get_kawaii_gif("tickle", ctx.data().config.kawaii_api_key.as_ref()).await?;

    let mut embed = serenity::CreateEmbed::default()
        .description(format!("**{}** tickles **{}** 🤭", ctx.author().name, member.name))
        .color(serenity::Color::from_rgb(255, 215, 0));

    if let Some(url) = gif_url {
        embed = embed.image(url);
    }

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, rename = "8ball", category = "Fun")]
pub async fn eightball(
    ctx: Context<'_>,
    #[description = "Your question"] question: String,
) -> Result<(), Error> {
    let responses = [
        "It is certain.",
        "Without a doubt.",
        "Yes, definitely.",
        "You can count on it.",
        "From what I see, yes.",
        "Very likely.",
        "Outlook is good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My answer is no.",
        "My sources say no.",
        "Outlook is not so good.",
        "Very doubtful.",
    ];

    let response = {
        let mut rng = rand::thread_rng();
        responses[rng.gen_range(0..responses.len())]
    };

    let embed = serenity::CreateEmbed::default()
        .title("🎱 Magic 8-Ball")
        .field("Question", question, false)
        .field("Answer", response, false)
        .color(serenity::Color::from_rgb(52, 152, 219))
        .footer(serenity::CreateEmbedFooter::new(format!("Requested by {}", ctx.author().name))
            .icon_url(ctx.author().face()));

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn joke(ctx: Context<'_>) -> Result<(), Error> {
    let jokes = [
        "Why don't scientists trust atoms? Because they make up everything.",
        "Why did the programmer quit his job? Because he didn't get arrays.",
        "Why did the scarecrow win an award? He was outstanding in his field.",
        "What do you call fake spaghetti? An impasta.",
        "Why did the math book look sad? It had too many problems.",
        "What do you call cheese that isn't yours? Nacho cheese.",
        "Why can't your nose be 12 inches long? Because then it would be a foot.",
        "Why did the bicycle fall over? It was two tired.",
        "What do you call a pile of cats? A meowtain.",
        "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
    ];

    let joke = {
        let mut rng = rand::thread_rng();
        jokes[rng.gen_range(0..jokes.len())]
    };

    let embed = serenity::CreateEmbed::default()
        .title("😂 Joke")
        .description(joke)
        .color(serenity::Color::from_rgb(255, 215, 0))
        .footer(serenity::CreateEmbedFooter::new(format!("Requested by {}", ctx.author().name))
            .icon_url(ctx.author().face()));

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}

#[poise::command(slash_command, category = "Fun")]
pub async fn meme(ctx: Context<'_>) -> Result<(), Error> {
    let client = reqwest::Client::new();
    let response = client
        .get("https://meme-api.com/gimme")
        .send()
        .await?;

    if !response.status().is_success() {
        ctx.send(poise::CreateReply::default().embed(error_embed("Unable to fetch a meme")))
            .await?;
        return Ok(());
    }

    let data: MemeResponse = response.json().await?;

    let color = {
        let mut rng = rand::thread_rng();
        serenity::Color::from_rgb(rng.gen(), rng.gen(), rng.gen())
    };

    let embed = serenity::CreateEmbed::default()
        .title(data.title)
        .url(data.post_link)
        .image(data.url)
        .footer(serenity::CreateEmbedFooter::new(format!("👍 {} | r/{}", data.ups, data.subreddit)))
        .color(color);

    ctx.send(poise::CreateReply::default().embed(embed)).await?;
    Ok(())
}
