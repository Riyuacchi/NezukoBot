use poise::serenity_prelude as serenity;

pub const EMBED_COLOR: u32 = 0x9B59B6;

pub fn success_embed(description: &str) -> serenity::CreateEmbed {
    serenity::CreateEmbed::default()
        .description(format!("✅ {}", description))
        .color(serenity::Color::from_rgb(46, 204, 113))
}

pub fn error_embed(description: &str) -> serenity::CreateEmbed {
    serenity::CreateEmbed::default()
        .description(format!("❌ {}", description))
        .color(serenity::Color::from_rgb(231, 76, 60))
}

pub fn info_embed(description: &str) -> serenity::CreateEmbed {
    serenity::CreateEmbed::default()
        .description(description)
        .color(serenity::Color::from_rgb(52, 152, 219))
}

pub fn default_embed() -> serenity::CreateEmbed {
    serenity::CreateEmbed::default()
        .color(EMBED_COLOR)
}
