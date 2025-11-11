import discord
from discord import app_commands
from discord.ext import commands, tasks

from datetime import datetime, date, time, timezone, timedelta
import json
from pathlib import Path
from typing import Literal

from const import SESSION_CHANNEL_ID


JST = timezone(timedelta(hours=+9), "JST")
DATA_FILE = Path("db/irregular_sessions.json")


class NoticeSession(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    DATA_FILE.parent.mkdir(exist_ok=True)
    self.today_notice.start()
    self.tomorrow_notice.start()

  def cog_unload(self):
    self.today_notice.cancel()
    self.tomorrow_notice.cancel()

  def _manage_irregular_dates(self, mode: Literal["read", "add", "remove"], date_str: str | None = None) -> dict:
    """
    date_str: "YYYY-MM-DD"形式の日付文字列
    """
    if not DATA_FILE.exists():
      DATA_FILE.write_text(json.dumps({"add": [], "remove": []}, indent=2))

    with DATA_FILE.open("r", encoding="UTF-8") as f:
      data = json.load(f)

    match mode:
      case "read":
        return data

      case "add":
        if not date_str in data["add"]:
          data["add"].append(date_str)
        if date_str in data["remove"]:
          data["remove"].remove(date_str)

      case "remove":
        if not date_str in data["remove"]:
          data["remove"].append(date_str)
        if date_str in data["add"]:
          data["add"].remove(date_str)

    with DATA_FILE.open("w", encoding="UTF-8") as f:
      json.dump(data, f, indent=2)

    return data


  async def get_session_schedule(self, count: int) -> list[tuple[date, bool]]:
    irregular_dates = self._manage_irregular_dates("read")
    added_dates = {datetime.strptime(d, '%Y-%m-%d').date() for d in irregular_dates["add"]}
    removed_dates = {datetime.strptime(d, '%Y-%m-%d').date() for d in irregular_dates["remove"]}

    schedule_list = []
    today = datetime.now(JST).date()
    check_date = today

    while len(schedule_list) < count + 365:
      is_regular = (
        check_date.weekday() == 2 or # 水曜日
        (check_date.weekday() == 5 and 1 <= check_date.day <= 7) or # 第1土曜日
        (check_date.weekday() == 5 and 15 <= check_date.day <= 21) # 第3土曜日
      )
      is_added = check_date in added_dates

      # 定期開催日か追加日であれば、スケジュール候補とする
      if is_regular or is_added:
        is_removed = check_date in removed_dates
        schedule_list.append((check_date, is_removed))

      check_date += timedelta(days=1)

    # 日付でソートして指定された件数だけ返す
    schedule_list.sort(key=lambda x: x[0])
    return schedule_list[:count]


  @tasks.loop(time=[time(hour=21, minute=12, tzinfo=JST)])
  async def today_notice(self):
    await self.notice("today")

  @tasks.loop(time=[time(hour=21, minute=18, tzinfo=JST)])
  async def tomorrow_notice(self):
    await self.notice("tomorrow")

  async def notice(self, day_option: Literal["today", "tomorrow"]):
    today = datetime.now(JST).date()
    tomorrow = datetime.now(JST).date() + timedelta(days=1)

    full_schedule = await self.get_session_schedule(50)
    for day, is_removed in full_schedule:
      if is_removed:
        continue

      if day_option == "today" and today == day:
        msg = "今日"
        color = discord.Color.green()
        break
      elif day_option == "tomorrow" and tomorrow == day:
        msg = "明日"
        color = discord.Color.blue()
        break
      else:
        return

    channel = self.bot.get_channel(SESSION_CHANNEL_ID)
    if not channel:
      try:
        channel = await self.bot.fetch_channel(SESSION_CHANNEL_ID)
      except (discord.NotFound, discord.Forbidden):
        print(f"Error: Channel {SESSION_CHANNEL_ID} not found or no permission.")
        return

    embed = discord.Embed(
      title="セッションのお知らせ",
      description=f"{msg}はセッションがあります！",
      color=color
    )
    await channel.send(embed=embed) #type: ignore


  @app_commands.command(name="session", description="直近のセッション予定日を出力します")
  async def output_session_days(self, interaction: discord.Interaction, limit: int = 6, ephemeral: bool = True):
    await interaction.response.defer(ephemeral=ephemeral)

    session_schedule = await self.get_session_schedule(limit)

    if not session_schedule:
      await interaction.followup.send("直近のセッション予定はありません。", ephemeral=True)
      return

    description=f"### 直近{limit}回分のセッション予定日です。\n"

    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    for day, is_removed in session_schedule:
      # 休日 -> 17時から
      if day.weekday() >= 5:
        start_time = 17
      else:
        start_time = 15

      session_datetime = datetime.combine(day, time(start_time, 0, tzinfo=JST))
      timestamp = int(session_datetime.timestamp())

      date_str = f"{day.strftime('%Y年%m月%d日')} ({weekdays[day.weekday()]}) <t:{timestamp}:R>"

      # 削除された日なら打ち消し線を付ける
      if is_removed:
        date_str = f"~~{date_str}~~(なし)"

      description += f"{date_str}\n"

    embed = discord.Embed(
      title="今後のセッション予定",
      description=description,
      color=discord.Color.purple()
    )

    await interaction.followup.send(embed=embed, ephemeral=ephemeral)


  @app_commands.command(name="resist_session", description="イレギュラーなセッション日を登録/削除します")
  @app_commands.describe(
    mode="追加または削除を選択してください",
    day="日付をYYYYMMDD形式で入力 (例: 20250810)"
  )
  @app_commands.choices(mode=[
    app_commands.Choice(name="追加", value="add"),
    app_commands.Choice(name="削除", value="remove")
  ])
  async def resist_session_days(self, interaction: discord.Interaction, mode: app_commands.Choice[str], day: int):
    await interaction.response.defer(ephemeral=True)

    try:
      date_obj = datetime.strptime(str(day), '%Y%m%d').date()
      date_str = date_obj.strftime('%Y-%m-%d')
    except ValueError:
      await interaction.followup.send("日付の形式が正しくありません。`YYYYMMDD`形式で入力してください。", ephemeral=True)
      return

    self._manage_irregular_dates(mode.value, date_str) # type: ignore

    action_text = "追加" if mode.value == "add" else "削除"
    await interaction.followup.send(f"セッション日 `{date_str}` をイレギュラー日程として **{action_text}** しました。", ephemeral=True)



async def setup(bot: commands.Bot):
  await bot.add_cog(NoticeSession(bot))