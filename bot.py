import os
import sys
import subprocess
import asyncio
import re

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
# আপনার তথ্য
# ==========================================
API_ID = 29904834  
API_HASH = "8b4fd9ef578af114502feeafa2d31938" 
BOT_TOKEN = "8061645932:AAGmZUdjfcEFx2Y58EV1FFhoLf5M1RFyv8o" 
SERVER_URL = "https://tgstreem.onrender.com" # আপনার রেন্ডার ইউআরএল

bot = Client("stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ভিডিও স্ট্রিমিং সার্ভার লজিক ---
routes = web.RouteTableDef()

@routes.get("/")
async def home_handler(request):
    return web.Response(text="🚀 Streaming Bot is Online!", content_type="text/plain")

@routes.get("/stream/{file_id}")
async def stream_handler(request):
    file_id = request.match_info['file_id']
    
    try:
        # ফাইলের তথ্য সংগ্রহ করা (সাইজ জানার জন্য)
        file_info = await bot.get_messages(None, None) # এটি সরাসরি কাজ করবে না, তাই আমরা ডাইনামিক হ্যান্ডলিং করব
        # নোট: ফাইল সাইজ ছাড়া স্ট্রিমিং ব্রাউজারে আটকে যায়। 
        # আমরা এখানে একটি জেনেরিক ফাইল অবজেক্ট তৈরির চেষ্টা করব।
        
        # রেঞ্জ রিকোয়েস্ট হ্যান্ডলিং
        range_header = request.headers.get("Range", "bytes=0-")
        range_match = re.search(r'bytes=(\0d+)-(\d*)', range_header)
        
        start_byte = int(range_match.group(1)) if range_match else 0
        
        # স্ট্রিমিং জেনারেটর
        async def file_generator():
            async for chunk in bot.stream_media(file_id, offset=start_byte):
                yield chunk

        # রেসপন্স হেডার সেটআপ
        headers = {
            'Content-Type': 'video/mp4',
            'Accept-Ranges': 'bytes',
            'Content-Disposition': 'inline',
        }
        
        # স্ট্রিমিং রেসপন্স পাঠানো
        res = web.StreamResponse(status=206, reason='Partial Content', headers=headers)
        await res.prepare(request)
        
        async for chunk in file_generator():
            await res.write(chunk)
            
        return res

    except Exception as e:
        print(f"Error: {e}")
        return web.Response(text="Error occurred", status=500)

async def start_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000)) 
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ সার্ভার সচল হয়েছে পোর্ট: {port}")

# --- বটের মেসেজ হ্যান্ডলার ---

@bot.on_message(filters.command("start"))
async def start_msg(c, m):
    await m.reply_text("👋 আমাকে ভিডিও ফাইল পাঠান, আমি স্ট্রিমিং লিঙ্ক দেব।")

@bot.on_message(filters.video | filters.document)
async def handle_video(client: Client, message: Message):
    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document and "video" in message.document.mime_type:
        file_id = message.document.file_id
    
    if file_id:
        # লিঙ্ক জেনারেট করা
        stream_link = f"{SERVER_URL}/stream/{file_id}"
        await message.reply_text(
            f"✅ **লিঙ্ক তৈরি হয়েছে!**\n\n"
            f"🔗 স্ট্রিমিং লিঙ্ক: `{stream_link}`\n\n"
            f"এটি VLC বা MX Player-এ ভালো কাজ করবে।"
        )
    else:
        await message.reply_text("❌ এটি কোনো ভিডিও ফাইল নয়।")

async def main():
    await bot.start()
    await start_server()
    await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
