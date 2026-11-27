import asyncio
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import random
from calculate import is_calculable, calculate,UnsafeExpression
from pathlib import Path


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Message content is a privileged intent, required for prefix commands
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents, case_insensitive=True)
DEBUG = False
ASSETS_DIR = Path(__file__).parent / "assets"

'''Discord cannot center text inside a field, so this centers the fields themselves using invisible spacer fields in a 3-column grid.
Source: Random dude on reddit (probably using claude)'''
SPACER = {"name": "\u200b", "value": "\u200b", "inline": True}
def add_spacer(embed: discord.Embed):
    embed.add_field(**SPACER)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.command()
async def hello(ctx: commands.Context, *, name: str = "world"):
    """Say hello. Usage: ?hello [name]"""
    await ctx.send(f"Hello, {name}! Jean Ball sends his regard.")



OUTCOMES = {
    "hope": ("Rolling with Hope", discord.Color.gold()),
    "fear": ("Rolling with Fear", discord.Color.dark_purple()),
    "critical": ("Critical Success!", discord.Color.green()),
}


@bot.command()
async def roll(ctx: commands.Context, *args: str):
    """Usage: ?roll [modifier] [adv]   e.g. ?roll 2 + 3 adv"""
    is_advantage = any(a.lower() == "adv" for a in args)

    # Join everything that is not "adv" so "2 + 3" is evaluated as one expression
    expression = " ".join(a for a in args if a.lower() != "adv")
    modifier = 0
    if expression:
        try:
            modifier = calculate(expression)
        except UnsafeExpression as e:
            await ctx.reply(f"Invalid modifier: {e}", mention_author=False)
            return

    hope_die = random.randint(1, 12)
    fear_die = random.randint(1, 12)
    advantage_die = random.randint(1, 6) if is_advantage else 0
    total = hope_die + fear_die + modifier + advantage_die

    if hope_die > fear_die:
        outcome = "hope"
    elif fear_die > hope_die:
        outcome = "fear"
    else:
        outcome = "critical"

    title, color = OUTCOMES[outcome]
    embed = discord.Embed(title=title, color=color)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

    def spacer():
        embed.add_field(name="\u200b", value="\u200b", inline=True)

    # Row 1: Fear | Total | Hope
    embed.add_field(name="Fear Die", value=f"`{fear_die}`", inline=True)
    embed.add_field(name="Total", value=f"`{total}`", inline=True)
    embed.add_field(name="Hope Die", value=f"`{hope_die}`", inline=True)


    # Row 2: extras, centered according to how many there are
    extras = []
    if is_advantage:
        extras.append(("Advantage", f"`+{advantage_die}`"))
    if modifier:
        extras.append(("Modifier", f"`{modifier:+}`"))

    if len(extras) == 1:
        spacer()
        embed.add_field(name=extras[0][0], value=extras[0][1], inline=True)
        spacer()
    elif len(extras) == 2:
        embed.add_field(name=extras[0][0], value=extras[0][1], inline=True)
        spacer()
        embed.add_field(name=extras[1][0], value=extras[1][1], inline=True)

    if DEBUG:
        embed.set_footer(text=f"Debug: modifier={modifier}, advantage={is_advantage}")

    # Attach the pre-rendered image, e.g. assets/F3H7.png
    filename = f"F{fear_die}H{hope_die}.png"
    image_path = ASSETS_DIR / filename
    if image_path.exists():
        file = discord.File(image_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")
        await ctx.reply(embed=embed, file=file, mention_author=False)
    else:
        await ctx.reply(embed=embed, mention_author=False)

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"Error: {error}")


async def main():
    discord.utils.setup_logging(level=logging.INFO)
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())