pub mod admin;
pub mod economy;
pub mod fun;
pub mod moderation;
pub mod utility;

use crate::handler::Error;

pub fn get_all_commands() -> Vec<poise::Command<crate::handler::Data, Error>> {
    vec![
        utility::help(),
        utility::ping(),
        utility::invite(),
        utility::userinfo(),
        utility::serverinfo(),
        utility::avatar(),
        utility::rank(),
        utility::leaderboard(),

        fun::hug(),
        fun::kiss(),
        fun::pat(),
        fun::slap(),
        fun::cuddle(),
        fun::poke(),
        fun::bite(),
        fun::lick(),
        fun::tickle(),
        fun::eightball(),
        fun::joke(),
        fun::meme(),

        economy::balance(),
        economy::work(),
        economy::daily(),
        economy::shop(),
        economy::buy(),
        economy::inventory(),
        economy::transfer(),
        economy::gamble(),

        moderation::ban(),
        moderation::unban(),
        moderation::kick(),
        moderation::warn(),
        moderation::warnings(),
        moderation::clearwarnings(),
        moderation::mute(),
        moderation::unmute(),
        moderation::timeout(),
        moderation::lock(),
        moderation::unlock(),
        moderation::slowmode(),
        moderation::purge(),

        admin::setup(),
        admin::automod(),
        admin::autorole(),
        admin::giveaway(),
    ]
}
