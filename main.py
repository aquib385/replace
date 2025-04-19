from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaDocument, InputMediaPhoto, InputMediaVideo, InputMediaAudio
import re

app = Client("file_replace_bot", bot_token="")

# Handle /start command
@app.on_message(filters.command("start"))
async def start(client, message):
    welcome = """🫧 Welcome to the Advanced File Replace Bot!
This bot can replace your old files with a new file ️and it also has the ability to replace files of private channels⚡️

1. Send the new file you want to replace with the old file.
2. Reply to the new file with the /replace command followed by the old file link.
Example: /replace https://t.me/edgebots/86
3. The bot will replace the old file with the new file.

📝 Note:
• Make Sure the bot and you are admin in the channel.
• You can only send 1 filelink after /replace command"""
    await message.reply_text(welcome)

# Handle /replace command
@app.on_message(filters.command("replace"))
async def replace_file(client, message: Message):
    # Check if message is a reply
    if not message.reply_to_message:
        await message.reply_text("❗ Reply to the new file with /replace command.")
        return

    replied = message.reply_to_message
    if not replied.media:
        await message.reply_text("❗ Replied message has no media.")
        return

    # Extract old URL
    cmd = message.text.split()
    if len(cmd) < 2:
        await message.reply_text("❗ Provide the old file URL.")
        return
    url = cmd[1].strip()

    # Parse URL
    match = re.match(r"https?://t\.me/(?:c/)?(\d+|[a-zA-Z0-9_]+)/(\d+)", url)
    if not match:
        await message.reply_text("❌ Invalid URL format.")
        return

    username_or_id, msg_id = match.groups()
    msg_id = int(msg_id)

    # Get chat ID
    try:
        if username_or_id.isdigit():
            chat_id = int(f"-100{username_or_id}") if not username_or_id.startswith("-100") else int(username_or_id)
        else:
            chat = await client.get_chat(username_or_id)
            chat_id = chat.id
    except Exception as e:
        await message.reply_text(f"❌ Error getting chat: {e}")
        return

    # Check user admin status
    try:
        user = await client.get_chat_member(chat_id, message.from_user.id)
        if user.status not in ("administrator", "creator"):
            await message.reply_text("❗ You're not an admin in this channel.")
            return
    except Exception as e:
        await message.reply_text(f"❌ Admin check failed: {e}")
        return

    # Check bot admin status
    try:
        bot = await client.get_chat_member(chat_id, "me")
        if bot.status not in ("administrator", "creator"):
            await message.reply_text("❗ I'm not an admin here.")
            return
    except Exception as e:
        await message.reply_text(f"❌ Bot admin check failed: {e}")
        return

    # Get old message
    try:
        old_msg = await client.get_messages(chat_id, msg_id)
    except:
        await message.reply_text("❌ Couldn't fetch the old message.")
        return

    if not old_msg.media:
        await message.reply_text("❌ Old message has no media.")
        return

    # Determine media types
    media_mapping = {
        "document": (InputMediaDocument, "document"),
        "video": (InputMediaVideo, "video"),
        "photo": (InputMediaPhoto, "photo"),
        "audio": (InputMediaAudio, "audio")
    }

    old_media_type = next((k for k in media_mapping if getattr(old_msg, k)), None)
    new_media_type = next((k for k in media_mapping if getattr(replied, k)), None)

    if not old_media_type or not new_media_type:
        await message.reply_text("❌ Unsupported media type.")
        return

    if old_media_type != new_media_type:
        await message.reply_text("❗ Media types don't match.")
        return

    # Prepare new media
    media_class, attr = media_mapping[new_media_type]
    new_file = getattr(replied, attr)
    file_id = new_file.file_id if attr != "photo" else replied.photo[-1].file_id

    # For photos, use the largest size
    media = media_class(media=file_id, caption=replied.caption or old_msg.caption)

    # Replace media
    try:
        await client.edit_message_media(
            chat_id=chat_id,
            message_id=msg_id,
            media=media
        )
        await message.reply_text("✅ File replaced successfully!")
    except Exception as e:
        await message.reply_text(f"❌ Replacement failed: {e}")

app.run()
