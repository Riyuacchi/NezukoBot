import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import asyncio
from typing import Optional
import config
import aiohttp
from bot.utils.embeds import success_embed, error_embed, info_embed, music_embed
from bot.utils.checks import in_voice, bot_in_voice


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()

        try:
            node = wavelink.Node(
                uri=f"http://{config.LAVALINK_HOST}:{config.LAVALINK_PORT}",
                password=config.LAVALINK_PASSWORD
            )

            await wavelink.Pool.connect(client=self.bot, nodes=[node])
        except Exception as e:
            print(f"Failed to connect to Lavalink: {e}")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player = payload.player
        if not player:
            return

        if player.queue:
            next_track = await player.queue.get()
            await player.play(next_track)
        else:
            if player.autoplay == wavelink.AutoPlayMode.enabled:
                return

    @commands.hybrid_command(name="play", description="Play a track")
    @in_voice()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice:
            await ctx.send(embed=error_embed("You need to be in a voice channel"))
            return

        player: wavelink.Player = ctx.voice_client

        if not player:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

        tracks = await wavelink.Playable.search(query)
        if not tracks:
            await ctx.send(embed=error_embed("No tracks found"))
            return

        track = tracks[0]
        duration_text = f"{track.length // 60000}:{(track.length // 1000) % 60:02d}"

        if player.playing:
            await player.queue.put(track)
            embed = music_embed("Added to queue", f"**{track.title}** will play after the current track.")
            embed.add_field(name="Duration", value=duration_text, inline=True)
            embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
            if track.artwork:
                embed.set_thumbnail(url=track.artwork)
            await ctx.send(embed=embed)
        else:
            await player.play(track)
            embed = music_embed("Now Playing", f"**{track.title}**")
            embed.add_field(name="Duration", value=duration_text, inline=True)
            embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
            if track.artwork:
                embed.set_thumbnail(url=track.artwork)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="pause", description="Pause the music")
    @bot_in_voice()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def pause(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client

        if not player or not player.playing:
            await ctx.send(embed=error_embed("No music is currently playing"))
            return

        await player.pause(True)
        await ctx.send(embed=success_embed("⏸️ Music paused"))

    @commands.hybrid_command(name="resume", description="Resume playback")
    @bot_in_voice()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def resume(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client

        if not player or not player.paused:
            await ctx.send(embed=error_embed("No track is paused"))
            return

        await player.pause(False)
        await ctx.send(embed=success_embed("▶️ Playback resumed"))

    @commands.hybrid_command(name="stop", description="Stop music and clear the queue")
    @bot_in_voice()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def stop(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client

        if not player:
            await ctx.send(embed=error_embed("The bot is not connected"))
            return

        await player.stop()
        player.queue.clear()
        await player.disconnect()
        await ctx.send(embed=success_embed("⏹️ Playback stopped and disconnected"))

    @commands.hybrid_command(name="skip", description="Skip to the next track")
    @bot_in_voice()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def skip(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client

        if not player or not player.playing:
            await ctx.send(embed=error_embed("No music is currently playing"))
            return

        await player.skip()
        await ctx.send(embed=success_embed("⏭️ Track skipped"))

    @commands.hybrid_command(name="queue", description="Show the queue")
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def queue(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client

        if not player:
            await ctx.send(embed=error_embed("The bot is not connected"))
            return

        if player.queue.is_empty:
            await ctx.send(embed=info_embed("The queue is empty"))
            return

        description = f"Queue contains {len(player.queue)} track(s)."
        embed = music_embed("Queue", description)

        if player.current:
            embed.add_field(
                name="Now playing",
                value=f"**{player.current.title}**\n{player.current.length // 60000}:{(player.current.length // 1000) % 60:02d}",
                inline=False
            )

        entries = []
        for index, track in enumerate(list(player.queue)[:10], start=1):
            entries.append(f"`{index}.` **{track.title}** — {track.length // 60000}:{(track.length // 1000) % 60:02d}")

        embed.add_field(
            name="Up next",
            value="\n".join(entries) if entries else "No tracks",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="nowplaying", description="Show the currently playing track")
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def nowplaying(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client

        if not player or not player.current:
            await ctx.send(embed=error_embed("No music is currently playing"))
            return

        track = player.current
        position = player.position
        duration = track.length
        progress = f"{position // 60000}:{(position // 1000) % 60:02d} / {duration // 60000}:{(duration // 1000) % 60:02d}"

        embed = music_embed("Now Playing", f"**{track.title}**")
        embed.add_field(name="Duration", value=progress, inline=True)
        embed.add_field(name="Volume", value=f"{player.volume}%", inline=True)
        embed.add_field(name="Loop", value="✅" if player.queue.mode == wavelink.QueueMode.loop else "❌", inline=True)
        if track.author:
            embed.add_field(name="Artist", value=track.author, inline=False)
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="volume", description="Adjust the volume")
    @bot_in_voice()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def volume(self, ctx: commands.Context, volume: int):
        player: wavelink.Player = ctx.voice_client

        if not player:
            await ctx.send(embed=error_embed("The bot is not connected"))
            return

        if volume < 0 or volume > 100:
            await ctx.send(embed=error_embed("Volume must be between 0 and 100"))
            return

        await player.set_volume(volume)
        await ctx.send(embed=success_embed(f"🔊 Volume set to {volume}%"))

    @commands.hybrid_command(name="loop", description="Toggle loop")
    @bot_in_voice()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def loop(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client

        if not player:
            await ctx.send(embed=error_embed("The bot is not connected"))
            return

        if player.queue.mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.normal
            await ctx.send(embed=success_embed("🔁 Loop disabled"))
        else:
            player.queue.mode = wavelink.QueueMode.loop
            await ctx.send(embed=success_embed("🔁 Loop enabled"))

    @commands.hybrid_command(name="shuffle", description="Shuffle the queue")
    @bot_in_voice()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def shuffle(self, ctx: commands.Context):
        player: wavelink.Player = ctx.voice_client

        if not player or player.queue.is_empty:
            await ctx.send(embed=error_embed("The queue is empty"))
            return

        player.queue.shuffle()
        await ctx.send(embed=success_embed("🔀 Queue shuffled"))

    @commands.hybrid_command(name="seek", description="Seek within the track")
    @bot_in_voice()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def seek(self, ctx: commands.Context, seconds: int):
        player: wavelink.Player = ctx.voice_client

        if not player or not player.playing:
            await ctx.send(embed=error_embed("No music is currently playing"))
            return

        if seconds < 0 or seconds * 1000 > player.current.length:
            await ctx.send(embed=error_embed("Invalid position"))
            return

        await player.seek(seconds * 1000)
        await ctx.send(embed=success_embed(f"⏩ Position set to {seconds}s"))

    @commands.hybrid_command(name="filter", description="Apply an audio filter")
    @bot_in_voice()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def filter(self, ctx: commands.Context, filter_name: str):
        player: wavelink.Player = ctx.voice_client

        if not player:
            await ctx.send(embed=error_embed("The bot is not connected"))
            return

        filters = {
            "nightcore": wavelink.Timescale(speed=1.3, pitch=1.3, rate=1.0),
            "vaporwave": wavelink.Timescale(speed=0.8, pitch=0.8, rate=1.0),
            "bass": wavelink.Equalizer.boost(),
            "none": None
        }

        if filter_name.lower() not in filters:
            await ctx.send(embed=error_embed(f"Available filters: {', '.join(filters.keys())}"))
            return

        selected_filter = filters[filter_name.lower()]

        if selected_filter is None:
            await player.set_filters()
            await ctx.send(embed=success_embed("🎚️ Filters reset"))
        elif isinstance(selected_filter, wavelink.Timescale):
            await player.set_filters(wavelink.Filters(timescale=selected_filter))
            await ctx.send(embed=success_embed(f"🎚️ Filter **{filter_name}** applied"))
        elif isinstance(selected_filter, wavelink.Equalizer):
            await player.set_filters(wavelink.Filters(equalizer=selected_filter))
            await ctx.send(embed=success_embed(f"🎚️ Filter **{filter_name}** applied"))

    @commands.hybrid_command(name="lyrics", description="Show lyrics for the current track")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def lyrics(self, ctx: commands.Context, *, query: str = None):
        player: wavelink.Player = ctx.voice_client

        if not query:
        if not player or not player.current:
            await ctx.send(embed=error_embed("No music is currently playing"))
                return
            query = player.current.title

        if not config.GENIUS_API_KEY:
            await ctx.send(embed=error_embed("Genius API key not configured"))
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.genius.com/search?q={query}",
                headers={"Authorization": f"Bearer {config.GENIUS_API_KEY}"}
            ) as resp:
                if resp.status != 200:
                    await ctx.send(embed=error_embed("Error while searching for lyrics"))
                    return

                data = await resp.json()
                if not data["response"]["hits"]:
                    await ctx.send(embed=error_embed("No lyrics found"))
                    return

                song_url = data["response"]["hits"][0]["result"]["url"]
                song_title = data["response"]["hits"][0]["result"]["full_title"]

                embed = discord.Embed(
                    title=f"🎤 Lyrics",
                    description=f"[{song_title}]({song_url})",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Link",
                    value=f"[Click here to view full lyrics]({song_url})",
                    inline=False
                )
                await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
