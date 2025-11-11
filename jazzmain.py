from discord.ext import commands
import discord
from const import TOKEN


intents = discord.Intents.none()
intents.guilds = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!!!!!", intents=intents)

@bot.event
async def on_ready():
  for x in ["cogs.lend_key", "cogs.session_notice", "cogs.standard_gacha"]:
    await bot.load_extension(x)
    print(f"ロード完了：{x}")
  await bot.tree.sync()
  print("全ロード完了")


if TOKEN:
  bot.run(TOKEN)