import os
import sys
import subprocess
import asyncio
import re
from aiohttp import web

# --- অটো-ইনস্টলার ---
def install_requirements():
    requirements = ['pyrogram', 'tgcrypto', 'aiohttp']
    for lib in requirements:
        try:
            __import__(lib)
        except ImportError:
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_requirements()

from pyrogram import Client, filters, idle
from pyrogram.types import Message

# ==========================================
# আপনার তথ্য
# ==========================================
API_ID = 29904834  
API_HASH = "8b4fd9ef578af114502feeafa2d31938" 
BOT_TOKEN = "8061645932:AAGmZUdjfcEFx2Y58EV1FFhoLf5M1RFyv8o" 
SERVER_URL = "https://tgstreem.onrender.com" # আপনার রেন্ডার ইউআরএল

bot = Client("stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- স্ট্রিমিং সার্ভার লজিক ---
routes = web.RouteTableDef()

@routes.get("/")
async def home_handler(request):
    return web.Response(text="🚀 Streaming Bot is Online and Running perfectly!", content_type="text/plain")

@routes.get("/stream/{chat_id}/{message_id}")
async def stream_handler(request):
    try:
        chat_id = int(request.match_info['chat_id'])
        message_id = int(request.match_info['message_id'])
        
        # মেসেজ থেকে ভিডিও তথ্য সংগ্রহ
        msg = await bot.get_messages(chat_id, message_id)
        if not msg or not (msg.video or msg.document):
            return web.Response(text="File not found", status=404)

        file_obj = msg.video or msg.document
        file_size = file_obj.file_size
        mime_type = file_obj.mime_type or "video/mp4"

        # রেঞ্জ রিকোয়েস্ট হ্যান্ডলিং (Seeking Support)
        range_header = request.headers.get("Range", "bytes=0-")
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        
        start_byte = int(range_match.group(1)) if range_match else 0
        end_byte = int(range_match.group(2)) if range_match and range_match.group(2) else file_size - 1
        chunk_length = end_byte - start_byte + 1

        headers = {
            'Content-Type': mime_type,
            'Content-Range': f'bytes {start_byte}-{end_byte}/{file_size}',
            'Content-Length': str(chunk_length),
            'Accept-Ranges': 'bytes',
        }

        # স্ট্রিমিং রেসপন্স
        res = web.StreamResponse(status=206, reason='Partial Content', headers=headers)
        await res.prepare(request)

        async for chunk in bot.stream_media(msg, offset=start_byte):
            await res.write(chunk)
        
        return res

    except Exception as e:
        print(f"Error: {e}")
        return web.Response(text=f"Error: {str(e)}", status=500)

async def start_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000)) 
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ সার্ভার পোর্ট {port}-এ চালু হয়েছে।")

# --- বটের মেসেজ হ্যান্ডলার ---

@bot.on_message(filters.command("start"))
async def start_msg(c, m):
    await m.reply_text("👋 আমাকে ভিডিও ফাইল পাঠান, আমি স্ট্রিমিং লিঙ্ক দেব।\n\nএটি VLC বা MX Player-এ সরাসরি কাজ করবে।")

@bot.on_message(filters.video | filters.document)
async def handle_video(client: Client, message: Message):
    if message.document and "video" not in message.document.mime_type:
        await message.reply_text("❌ এটি ভিডিও ফাইল নয়।")
        return

    # চ্যাট আইডি এবং মেসেজ আইডি দিয়ে ডাইনামিক লিঙ্ক তৈরি
    chat_id = message.chat.id
    msg_id = message.id
    
    stream_link = f"{SERVER_URL}/stream/{chat_id}/{msg_id}"
    
    await message.reply_text(
        f"✅ **লিঙ্ক তৈরি হয়েছে!**\n\n"
        f"🔗 স্ট্রিমিং লিঙ্ক: `{stream_link}`\n\n"
        f"💡 ভিডিওটি সরাসরি দেখতে লিঙ্কটি কপি করে **VLC** বা **MX Player** এ চালান।"
    )

# --- মেইন রানার ---
async def main():
    print("বট এবং সার্ভার চালু হচ্ছে...")
    await bot.start()
    await start_server()
    await idle()
    await bot.stop()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nবট বন্ধ করা হয়েছে।")
