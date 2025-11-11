import os
from dotenv import load_dotenv

load_dotenv(override=True)


TOKEN = os.environ.get('jazz_club_bot_token')
ADMIN_ROLE_ID = int(os.environ.get('admin_role_id', "0"))
SESSION_CHANNEL_ID = int(os.environ.get('session_channel_id', "0"))