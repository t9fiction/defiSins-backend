import os
import aiohttp
from fastapi import FastAPI, Request
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Update
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio
from telebot import asyncio_helper
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# # Proxy configuration
# asyncio_helper.proxy = 'socks4://129.146.163.153:47060'

# Initialize Telegram bot
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")

# Initialize bot without proxy for production
bot = AsyncTeleBot(TOKEN)

# Create FastAPI application
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure Supabase bucket exists
async def ensure_bucket_exists(bucket_name):
    try:
        existing_bucket = supabase.storage.get_bucket(bucket_name)
        if existing_bucket.id == bucket_name:
            print(f"Bucket '{bucket_name}' already exists.")
        else:
            print(f"Bucket details mismatch for '{bucket_name}' (found {existing_bucket.id}).")
    except Exception as e:
        if "Bucket not found" in str(e):
            supabase.storage.create_bucket(
                bucket_name,
                options={"public": True, "allowed_mime_types": ["image/jpeg", "image/png"], "file_size_limit": 5 * 1024 * 1024},
            )

# Upload profile photo to Supabase
async def upload_profile_photo(user_id):
    try:
        await ensure_bucket_exists("profile_images")
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if not photos.photos:
            return None
        file_id = photos.photos[0][0].file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    return None
                image_data = await response.read()
        filename = f"profile_images/{user_id}.jpg"
        supabase.storage.from_("profile_images").upload(filename, image_data, {"content-type": "image/jpeg"})
        return supabase.storage.from_("profile_images").get_public_url(filename)
    except Exception as e:
        print(f"Error uploading profile photo: {e}")
        return None

# Telegram bot command handlers
@bot.message_handler(commands=["help"])
async def help_command(message):
    await bot.reply_to(message, "Available commands:\n/start - Start the bot\n/help - Show help")

@bot.message_handler(commands=["start"])
async def start_command(message):
    user_id = str(message.from_user.id)
    user_data = {
        "user_id": user_id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "language_code": message.from_user.language_code,
        "is_premium": message.from_user.is_premium,
        "balance": 0,
        "mine_rate": 0.001,
        "is_mining": False,
        "mining_start_time": None,
        "last_daily_claim": None,
        "profile_image": None,
    }
    await bot.reply_to(message, "Hi there, I am EchoBot!")

    try:
        existing_user = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if not existing_user.data:
            user_data["profile_image"] = await upload_profile_photo(user_id)
            supabase.table("users").insert(user_data).execute()
        else:
            user_data["profile_image"] = await upload_profile_photo(user_id)
            supabase.table("users").update(user_data).eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error handling user data: {e}")
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Open App", web_app=WebAppInfo(url="https://defi-sins.netlify.app/")))
    await bot.send_message(message.chat.id, "Welcome to the BeyCoin Bot! Please select an option:", reply_markup=keyboard)

# FastAPI routes
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Webhook route to receive updates from Telegram
@app.post("/webhook/")
async def telegram_webhook(request: Request):
    # Get the JSON data
    json_data = await request.json()
    # Convert dict to Update object
    update = Update.de_json(json_data)
    # Now process the update
    await bot.process_new_updates([update])
    return {"ok": True}

# Startup event to set webhook
@app.on_event("startup")
async def startup_event():
    # Get the RENDER_EXTERNAL_URL from environment variables
    webhook_url = os.getenv("https://defisins-backend.onrender.com")
    if webhook_url:
        webhook_url = f"{webhook_url}/webhook/"
        try:
            await bot.delete_webhook()  # Clear any existing webhook
            result = await bot.set_webhook(webhook_url)
            if result:
                print(f"Webhook successfully set to: {webhook_url}")
            else:
                print("Failed to set webhook.")
        except Exception as e:
            print(f"Error setting webhook: {e}")
    else:
        print("RENDER_EXTERNAL_URL not found in environment variables")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))