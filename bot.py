import os
import sys
import subprocess
import asyncio

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
from aiohttp import web

# ==========================================
# আপনার তথ্য (সংরক্ষিত রাখা হয়েছে)
# ==========================================
API_ID = 29904834  
API_HASH = "8b4fd9ef578af114502feeafa2d31938" 
BOT_TOKEN = "8061645932:AAGmZUdjfcEFx2Y58EV1FFhoLf5M1RFyv8o" 
SERVER_URL = "https://tgstreem.onrender.com" 

bot = Client("stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ভিডিও স্ট্রিমিং সার্ভার লজিক ---
routes = web.RouteTableDef()

@routes.get("/")
async def home_handler(request):
    return web.Response(text="🚀 Streaming Bot is Online and Ready!", content_type="text/plain")

@routes.get("/stream/{file_id}")
async def stream_handler(request):
    file_id = request.match_info['file_id']
    
    # ভিডিও স্ট্রিমিং জেনারেটর
    async def file_generator():
        try:
            async for chunk in bot.iter_download(file_id):
                yield chunk
        except Exception as e:
            print(f"Error while streaming: {e}")

    # ভিডিও ফাইল স্ট্রিমিং রেসপন্স (Chunked Transfer Encoding)
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'video/mp4',
            'Content-Disposition': 'inline',
            'Accept-Ranges': 'bytes',
        }
    )
    
    await response.prepare(request)
    try:
        async for chunk in file_generator():
            await response.write(chunk)
    except Exception:
        pass
    return response

async def start_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # রেন্ডার বা অন্যান্য হোস্টিংয়ের জন্য পোর্ট সেটিংস
    # রেন্ডার সাধারণত ১০০০০ পোর্টে সার্ভিস খুঁজে থাকে যদি PORT সেট না থাকে
    port = int(os.environ.get("PORT", 10000)) 
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ স্ট্রিমিং সার্ভার সচল হয়েছে পোর্ট: {port}")

# --- বটের মেসেজ হ্যান্ডলার ---

@bot.on_message(filters.command("start"))
async def start_msg(c, m):
    await m.reply_text(
        "👋 স্বাগতম!\n\nআমাকে ভিডিও ফাইল পাঠান, আমি আপনাকে সরাসরি স্ট্রিমিং লিঙ্ক দেব।"
    )

@bot.on_message(filters.video | filters.document)
async def handle_video(client: Client, message: Message):
    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document and "video" in message.document.mime_type:
        file_id = message.document.file_id
    
    if file_id:
        stream_link = f"{SERVER_URL}/stream/{file_id}"
        await message.reply_text(
            f"✅ **লিঙ্ক তৈরি হয়েছে!**\n\n"
            f"🔗 স্ট্রিমিং লিঙ্ক: `{stream_link}`\n\n"
            f"এই লিঙ্কটি যেকোনো প্লেয়ারে ব্যবহার করুন।"
        )
    else:
        await message.reply_text("❌ এটি কোনো ভিডিও ফাইল নয়।")

# --- মেইন রানার ---
async def main():
    print("বট এবং সার্ভার চালু হচ্ছে...")
    await bot.start()
    await start_server()
    await idle() # বটকে সারাক্ষণ মেসেজ শোনার জন্য সচল রাখবে
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nবট বন্ধ করা হয়েছে।")
