import os
import sys
import subprocess
import asyncio

# --- অটো-ইনস্টলার: লাইব্রেরি না থাকলে নিজে থেকেই ইনস্টল করবে ---
def install_requirements():
    requirements = ['pyrogram', 'tgcrypto', 'aiohttp']
    for lib in requirements:
        try:
            __import__(lib)
        except ImportError:
            print(f"Installing {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

# লাইব্রেরি ইনস্টল করা শুরু
install_requirements()

# ইনস্টল হওয়ার পর লাইব্রেরিগুলো ইমপোর্ট করা
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

# বট ক্লায়েন্ট সেটআপ
bot = Client("stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ভিডিও স্ট্রিমিং সার্ভার লজিক ---
routes = web.RouteTableDef()

# রেন্ডার যেন বুঝতে পারে সার্ভার সচল আছে (Health Check)
@routes.get("/")
async def home_handler(request):
    return web.Response(text="Streaming Bot is Online!")

@routes.get("/stream/{file_id}")
async def stream_handler(request):
    file_id = request.match_info['file_id']
    
    async def file_generator():
        async for chunk in bot.iter_download(file_id):
            yield chunk

    return web.Response(
        body=file_generator(),
        content_type='video/mp4',
        headers={
            "Content-Disposition": "inline",
            "Accept-Ranges": "bytes"
        }
    )

async def start_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # রেন্ডারের জন্য পোর্ট হ্যান্ডলিং
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"\n🚀 স্ট্রিমিং সার্ভার চালু হয়েছে পোর্ট {port} তে...")

# --- বটের মেসেজ হ্যান্ডলার ---

# স্টার্ট কমান্ড হ্যান্ডলার
@bot.on_message(filters.command("start"))
async def start_msg(c, m):
    await m.reply_text(
        "👋 স্বাগতম!\n\nআমাকে ভিডিও ফাইল পাঠান, আমি আপনাকে সরাসরি স্ট্রিমিং লিঙ্ক দেব।"
    )

# ভিডিও এবং ফাইল হ্যান্ডলার
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
            f"✅ **ভিডিওর স্ট্রিমিং লিঙ্ক তৈরি!**\n\n"
            f"🔗 লিঙ্ক: `{stream_link}`\n\n"
            f"এই লিঙ্কটি আপনার ওয়েবসাইট প্লেয়ারে ব্যবহার করুন।"
        )
    else:
        await message.reply_text("❌ এটি কোনো ভিডিও ফাইল নয়।")

# --- বট এবং সার্ভার একসাথে রান করা ---
async def main():
    print("বট স্টার্ট হচ্ছে...")
    # বট শুরু করা
    await bot.start()
    
    # সার্ভার শুরু করা
    await start_server()
    
    print("বট এখন অনলাইন।")
    
    # বটকে একটিভ রাখা (এটি মেসেজ শোনার জন্য জরুরি)
    await idle()
    
    # বন্ধ করার সময় সেফলি স্টপ করা
    await bot.stop()

if __name__ == "__main__":
    try:
        # ইভেন্ট লুপ চালানো
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print("\nবট বন্ধ করা হয়েছে।")
    except Exception as e:
        print(f"Error: {e}")
