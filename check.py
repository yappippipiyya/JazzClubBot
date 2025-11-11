from const import ADMIN_ROLE_ID


async def is_admin(interaction):
  if await interaction.client.is_owner(interaction.user):
    return True
  if not interaction.user.get_role(ADMIN_ROLE_ID):
    await interaction.response.send_message("このコマンドはadmin専用です。", ephemeral=True)
    return False
  return True
