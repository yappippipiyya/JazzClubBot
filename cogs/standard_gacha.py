from discord.ext import commands
from discord import app_commands, ui
import discord

import check
from db.database import get_choices, get_songs



class StandardGacha(commands.Cog):
  def __init__(self, bot:commands.Bot):
    self.bot = bot
    self.default_conditions = {
      "book_num": ["全て"],
      "M_m": ["全て"],
      "key": ["全て"],
      "beat": ["全て"],
      "type": ["全て"]
    }
    self.conditions = self.default_conditions.copy()


  @app_commands.command(name="send_gacha_button", description="[admin]スタンダードガチャのボタンを設置します")
  async def send_gacha_button(self, interaction: discord.Interaction):
    if not await check.is_admin(interaction):
      return

    await interaction.response.defer(ephemeral=True, thinking=True)

    view = await self.get_view()

    await interaction.channel.send(view=view) #type: ignore

    await interaction.delete_original_response()
    return


  @commands.Cog.listener()
  async def on_interaction(self, interaction: discord.Interaction):
    if not interaction.data:
      return

    custom_id = interaction.data.get("custom_id")
    if not custom_id:
      return

    if not custom_id.startswith("gacha_"):
      return

    if "start" in custom_id:
      await self.gacha_start(interaction)
      return

    elif "reset" in custom_id:
      self.conditions = self.default_conditions.copy()

      view = await self.get_view()
      await interaction.response.edit_message(view=view)
      return

    else:
      values = interaction.data.get("values")
      if not values:
        return

      custom = custom_id.replace("gacha_", "")

      if (self.conditions[custom] == ["全て"]) and ("全て" in values):
        values.remove("全て")

      self.conditions[custom] = values


      view = await self.get_view()
      await interaction.response.edit_message(view=view)
      return


  async def get_view(self):
    choices = get_choices()

    container = ui.Container(accent_color=0x402426)

    container.add_item(ui.TextDisplay("# スタ本ガチャ\nスタ本1, 2から条件を満たす曲をランダムで表示します。"))

    container.add_item(ui.Separator())

    for key in choices:
      container.add_item(ui.TextDisplay(f"### {key}"))

      actionrow = ui.ActionRow()

      if (count := len(self.conditions[key])) == 1:
        placeholder = self.conditions[key][0]
      else:
        placeholder = f"{count}件選択中"

      actionrow.add_item(ui.Select(
        placeholder=placeholder,
        options=[discord.SelectOption(
          label=choice,
          default=str(choice) in str(self.conditions[key]),
          ) for choice in choices[key]
        ],
        custom_id=f"gacha_{key}",
        max_values=1 if len(choices[key]) == 3 else len(choices[key]),
      ))
      container.add_item(actionrow)

    actionrow2 = ui.ActionRow()
    actionrow2.add_item(ui.Button(label="ガチャを回す", custom_id="gacha_start", style=discord.ButtonStyle.green))
    actionrow2.add_item(ui.Button(label="リセット", custom_id="gacha_reset", style=discord.ButtonStyle.gray))
    container.add_item(actionrow2)

    view = ui.LayoutView()
    view.add_item(container)

    return view


  async def gacha_start(self, interaction: discord.Interaction):
    await interaction.response.defer()

    songs = get_songs(self.conditions)

    if not songs:
      description = "## 該当なし！"

    else:
      description = f"## こんなのとか！\n"
      for song in songs:
        description += f"- **[{song.book_num}]{song.song_name} / {song.composer}**\n"

    embed = discord.Embed(
      description=description,
      color=discord.Color.random()
    )

    value = ""
    for key, conditions in self.conditions.items():
      value += f"{key} : {'・'.join(conditions)}\n"
    embed.add_field(name="条件", value=value)

    await interaction.followup.send(embed=embed, ephemeral=True)



async def setup(bot):
  await bot.add_cog(StandardGacha(bot))