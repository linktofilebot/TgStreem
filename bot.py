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
from pyrogram import Client, filters
from pyrogram.types import Message
from aiohttp import web

# ==========================================
# আপনার তথ্য এখানে বসান (বড় হাতের অক্ষরের জায়গায়)
# ==========================================
API_ID = 29904834  # my.telegram.org থেকে নিন
API_HASH = "8b4fd9ef578af114502feeafa2d31938" 
BOT_TOKEN = "8061645932:AAGmZUdjfcEFx2Y58EV1FFhoLf5M1RFyv8o" # BotFather থেকে নিন
SERVER_URL = "https://tgstreem.onrender.com" # যদি লাইভ সার্ভার হয় তবে IP দিন

bot = Client("stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ভিডিও স্ট্রিমিং সার্ভার লজিক ---
routes = web.RouteTableDef()

@routes.get("/stream/{file_id}")
async def stream_handler(request):
    file_id = request.match_info['file_id']
    
    # ভিডিও ফাইলের সাইজ এবং নাম পাওয়ার চেষ্টা
    file_info = await bot.get_messages(None, None) # Placeholder

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
    # ০.০.০.০ মানে এটি যেকোনো কানেকশন একসেপ্ট করবে
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("\n🚀 স্ট্রিমিং সার্ভার চালু হয়েছে পোর্ট ৮০৮০ তে...")

# --- বটের মেসেজ হ্যান্ডলার ---
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
            f"✅ ভিডিওর স্ট্রিমিং লিঙ্ক তৈরি!\n\n"
            f"🔗 লিঙ্ক: `{stream_link}`\n\n"
            f"এটি আপনার ওয়েবসাইট প্লেয়ারে ব্যবহার করুন।"
        )
    else:
        await message.reply_text("দয়া করে একটি ভিডিও ফাইল পাঠান।")

@bot.on_message(filters.command("start"))
async def start_msg(c, m):
    await m.reply_text("বট চালু আছে! আমাকে ভিডিও পাঠান।")

# --- বট এবং সার্ভার একসাথে রান করা ---
async def main():
    print("বট স্টার্ট হচ্ছে...")
    await bot.start()
    await start_server()
    print("বট এখন অনলাইন।")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nবট বন্ধ করা হয়েছে।")
