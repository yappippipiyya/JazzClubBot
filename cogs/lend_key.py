from discord.ext import commands
from discord import app_commands
import discord
import asyncio

import check
from datetime import datetime



async def send_lend_key_button(interaction: discord.Interaction):
  embed = discord.Embed(
    description="# 鍵を借りるボタン",
    color=0x000099,
  )

  view = discord.ui.View()
  button_1 = discord.ui.Button(label="鍵借ります", custom_id="lend_key", style=discord.ButtonStyle.blurple)
  button_2 = discord.ui.Button(label="鍵借ります(代理)", custom_id="lend_key_substitute", style=discord.ButtonStyle.green)
  view.add_item(button_1)
  view.add_item(button_2)

  await interaction.channel.send(embed=embed, view=view)

  return


async def send_lend_msg(interaction: discord.Interaction, description: str):
  await interaction.response.defer(ephemeral=True, thinking=True)

  embed = discord.Embed(
    description=description,
    color=0x00ff00
  )
  view = discord.ui.View()
  button = discord.ui.Button(label="鍵返します", custom_id="return_key", style=discord.ButtonStyle.red)
  view.add_item(button)

  await interaction.message.edit(embed=embed, view=view)

  await interaction.delete_original_response()
  return


async def send_return_msg(interaction: discord.Interaction, message: discord.Message, description:str):
  await interaction.response.defer(thinking=True, ephemeral=True)
  embed = discord.Embed(
    description=description,
    color=0xff0000
  )
  await message.edit(embeds=[message.embeds[0], embed])
  await message.edit(view=None)
  await interaction.delete_original_response()
  await asyncio.sleep(0.5)
  await send_lend_key_button(interaction)
  return


class NameModal(discord.ui.Modal):
  def __init__(self) -> None:
    super().__init__(title="誰が鍵を借りましたか？", timeout=None, custom_id="name_modal")

    self.name = discord.ui.TextInput(label="名前")
    self.add_item(self.name)

  async def on_submit(self, interaction: discord.Interaction) -> None:
    now = datetime.now()
    description = (
      f"{self.name.value}（代理：{interaction.user.mention}）が鍵を借りました。\n"
      f"時刻：<t:{int(now.timestamp())}> (<t:{int(now.timestamp())}:R>)"
    )
    await send_lend_msg(interaction, description)
    return


class ReturnButton(discord.ui.View):
  def __init__(self, bot: commands.Bot, original_message: discord.Message, *, timeout: float = 120):
    super().__init__(timeout=timeout)
    self.bot = bot
    self.original_message = original_message

  @discord.ui.button(label="大丈夫", style=discord.ButtonStyle.grey, custom_id="ok")
  async def ok(self, interaction: discord.Interaction, button: discord.ui.Button):
    now = datetime.now()
    description = (
      f"{interaction.user.mention}（代理）が鍵を返しました。\n"
      f"時刻：<t:{int(now.timestamp())}>"
    )
    await send_return_msg(interaction, self.original_message, description)
    await interaction.followup.delete_message(interaction.message.id)
    return

  @discord.ui.button(label="間違えた", style=discord.ButtonStyle.grey, custom_id="no")
  async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
    await interaction.response.defer(ephemeral=True, thinking=True)
    await interaction.delete_original_response()
    await interaction.followup.delete_message(interaction.message.id)
    return



class Managekey(commands.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot

  @app_commands.command(name="send_key_button", description="[admin]鍵借のボタンを設置します")
  async def first_message_link(self, interaction: discord.Interaction):
    if not await check.is_admin(interaction):
      return

    await interaction.response.defer(ephemeral=True, thinking=True)

    await send_lend_key_button(interaction)

    await interaction.delete_original_response()
    return


  @commands.Cog.listener()
  async def on_interaction(self, interaction: discord.Interaction):
    custom_id = interaction.data.get("custom_id", "")
    if not custom_id:
      return


    if custom_id == "lend_key":
      now = datetime.now()
      description = (
        f"{interaction.user.mention}が鍵を借りました\n"
        f"時刻：<t:{int(now.timestamp())}> (<t:{int(now.timestamp())}:R>)"
      )
      await send_lend_msg(interaction, description)
      return

    if custom_id == "lend_key_substitute":
      await interaction.response.send_modal(NameModal())
      return

    if custom_id == "return_key":
      if not interaction.message:
        await interaction.response.send_message("エラー")
        return

      if not str(interaction.user.id) in interaction.message.embeds[0].description:
        view = ReturnButton(self.bot, original_message=interaction.message)
        await interaction.response.send_message("あなた鍵借りた人じゃないけど大丈夫そう？", view=view, ephemeral=True)
        return

      now = datetime.now()
      description=(
        f"{interaction.user.mention}が鍵を返しました\n"
        f"時刻：<t:{int(now.timestamp())}>"
      )
      await send_return_msg(interaction, interaction.message, description)
      return



async def setup(bot):
  await bot.add_cog(Managekey(bot))