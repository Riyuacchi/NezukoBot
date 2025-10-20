use poise::serenity_prelude as serenity;

fn main() {
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

    println!("Permission bits: {}", permissions.bits());
    println!("\nInvite link template:");
    println!("https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions={}&scope=bot%20applications.commands", permissions.bits());
}
