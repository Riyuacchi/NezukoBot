import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
from typing import Optional
import config
from bot.utils.embeds import success_embed, error_embed, info_embed


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.kawaii_api = "https://kawaii.red/api/gif"
        self.eight_ball_responses = [
            "It is certain.", "Without a doubt.", "Yes, definitely.",
            "You can count on it.", "From what I see, yes.",
            "Very likely.", "Outlook is good.", "Yes.",
            "Signs point to yes.", "Reply hazy, try again.",
            "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My answer is no.", "My sources say no.",
            "Outlook is not so good.", "Very doubtful."
        ]

    async def get_kawaii_gif(self, endpoint: str, session: aiohttp.ClientSession):
        headers = {}
        if config.KAWAII_API_KEY:
            headers["Authorization"] = f"Bearer {config.KAWAII_API_KEY}"

        async with session.get(f"{self.kawaii_api}/{endpoint}", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("response")
            return None

    @commands.hybrid_command(name="hug", description="Give someone a hug")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def hug(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot hug yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("hug", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** gives **{member.mention}** a hug 🤗",
            color=discord.Color.pink()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="kiss", description="Kiss someone")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def kiss(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot kiss yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("kiss", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** kisses **{member.mention}** 💋",
            color=discord.Color.red()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="pat", description="Pat someone's head")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pat(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot pat yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("pat", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** pats **{member.mention}** ✋",
            color=discord.Color.blue()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="poke", description="Poke someone")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def poke(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot poke yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("poke", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** pokes **{member.mention}** 👉",
            color=discord.Color.orange()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="slap", description="Slap someone")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def slap(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot slap yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("slap", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** slaps **{member.mention}** 👋",
            color=discord.Color.red()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="cuddle", description="Cuddle someone")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def cuddle(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot cuddle yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("cuddle", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** cuddles **{member.mention}** 🥰",
            color=discord.Color.pink()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="tickle", description="Tickle someone")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def tickle(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot tickle yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("tickle", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** tickles **{member.mention}** 🤭",
            color=discord.Color.gold()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="bite", description="Bite someone")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bite(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot bite yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("bite", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** bites **{member.mention}** 🦷",
            color=discord.Color.purple()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="lick", description="Lick someone")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def lick(self, ctx: commands.Context, member: discord.Member):
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed("You cannot lick yourself"))
            return

        async with aiohttp.ClientSession() as session:
            gif_url = await self.get_kawaii_gif("lick", session)

        embed = discord.Embed(
            description=f"**{ctx.author.mention}** licks **{member.mention}** 👅",
            color=discord.Color.magenta()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="8ball", description="Ask the magic 8-ball a question")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        response = random.choice(self.eight_ball_responses)

        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.blue()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="joke", description="Get a random joke")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def joke(self, ctx: commands.Context):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything.",
            "Why did the programmer quit his job? Because he didn't get arrays.",
            "Why did the scarecrow win an award? He was outstanding in his field.",
            "What do you call fake spaghetti? An impasta.",
            "Why did the math book look sad? It had too many problems.",
            "What do you call cheese that isn't yours? Nacho cheese.",
            "Why can't your nose be 12 inches long? Because then it would be a foot.",
            "Why did the bicycle fall over? It was two tired.",
            "What do you call a pile of cats? A meowtain.",
            "Why did the golfer bring two pairs of pants? In case he got a hole in one."
        ]

        joke = random.choice(jokes)

        embed = discord.Embed(
            title="😂 Joke",
            description=joke,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="meme", description="Get a random meme")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def meme(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meme-api.com/gimme") as resp:
                if resp.status != 200:
                    await ctx.send(embed=error_embed("Unable to fetch a meme"))
                    return

                data = await resp.json()

                embed = discord.Embed(
                    title=data.get("title", "Meme"),
                    url=data.get("postLink", ""),
                    color=discord.Color.random()
                )
                embed.set_image(url=data.get("url"))
                embed.set_footer(text=f"👍 {data.get('ups', 0)} | r/{data.get('subreddit', 'memes')}")
                await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
