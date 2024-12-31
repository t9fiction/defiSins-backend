import os
import datetime
import aiohttp
import asyncio
from fastapi import FastAPI, Request
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv
from supabase import create_client, Client
from telebot import asyncio_helper
import uvicorn # Import the Uvicorn module


# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Initialize Telegram bot
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")

# Proxy configuration
asyncio_helper.proxy = 'socks4://129.146.163.153:47060'

bot = AsyncTeleBot(TOKEN)

# Create FastAPI application
app = FastAPI()

async def ensure_bucket_exists(bucket_name):
    """Ensure the specified Supabase bucket exists."""
    try:
        # Check if the bucket already exists
        print("Inside the try-catch for bucket testing...")
        existing_bucket = supabase.storage.get_bucket(bucket_name)
        print(f"Existing bucket details: {existing_bucket}")

        # Directly access attributes of the SyncBucket object
        if existing_bucket.id == bucket_name:
            print(f"Bucket '{bucket_name}' already exists.")
        else:
            print(f"Bucket details mismatch for '{bucket_name}' (found {existing_bucket.id}).")
    except Exception as e:
        # Handle exceptions for missing bucket or other errors
        print(f"Error ensuring bucket exists: {e}")
        if "Bucket not found" in str(e):
            print(f"Bucket '{bucket_name}' not found. Creating bucket...")
            supabase.storage.create_bucket(
                bucket_name,
                options={
                    "public": True,
                    "allowed_mime_types": ["image/jpeg", "image/png"],
                    "file_size_limit": 5 * 1024 * 1024,  # 5 MB limit
                },
            )
            print(f"Bucket '{bucket_name}' created successfully.")
        else:
            print("Unexpected error occurred.")


async def upload_profile_photo(user_id):
    """Fetch and upload the user's profile photo to Supabase."""
    try:
        # Ensure the bucket exists
        await ensure_bucket_exists("profile_images")

        # Fetch the user's profile photos
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if not photos.photos:
            return None  # No profile photo available

        # Get the file ID of the first photo
        file_id = photos.photos[0][0].file_id

        # Get the file path from Telegram
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        # Download the photo asynchronously
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                if response.status != 200:
                    return None
                image_data = await response.read()

        # Upload the photo to Supabase
        filename = f"profile_images/{user_id}.jpg"
        storage_response = supabase.storage.from_("profile_images").upload(
            filename, image_data, {"content-type": "image/jpeg"}
        )
        if "error" in storage_response:
            return None

        # Generate the public URL for the uploaded image
        public_url = supabase.storage.from_("profile_images").get_public_url(filename)
        return public_url
    except Exception as e:
        print(f"Error uploading profile photo: {e}")
        return None

@bot.message_handler(commands=['help'])
async def start(message):
    """
    Handle the /help command by sending a message with a list of available commands.
    """
    await bot.reply_to(message, "Available commands:\n/start - Start the bot\n/help - Show the help message")

@bot.message_handler(commands=['start'])
async def start(message):
    """
    Handle the /start command by welcoming the user, saving their data, and uploading their profile photo.
    """
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
        "profile_image": None,  # Placeholder for profile image URL
    }
    print(f"User data: {user_data}")
    await bot.reply_to(message, "Hi there, I am EchoBot!")

    # Check if the user exists
    try:
        existing_user = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if not existing_user.data:
            # Upload profile photo and save user data
            user_data["profile_image"] = await upload_profile_photo(user_id)
            supabase.table("users").insert(user_data).execute()
        else:
            # Update existing user data
            user_data["profile_image"] = await upload_profile_photo(user_id)
            supabase.table("users").update(user_data).eq("user_id", user_id).execute()
    except Exception as e:
        print(f"Error handling user data: {e}")

    # Send welcome message
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Open App", web_app=WebAppInfo(url="https://defi-sins.netlify.app/")))
    await bot.send_message(message.chat.id, "Welcome to the BeyCoin Bot! Please select an option:", reply_markup=keyboard)

@app.get("/")
async def root():
    """Root endpoint for the FastAPI application."""
    return {"message": "Hello World"}


@app.post("/webhook/")
async def telegram_webhook(request: Request):
    """Endpoint to handle Telegram webhook updates."""
    update = await request.json()
    await bot.process_new_updates([update])  # Process the update with your bot
    return {"ok": True}

# async def set_webhook():
#     """Set the webhook for the bot."""
#     # Use the environment variable for the Vercel URL
#     webhook_url = f"https://{os.environ.get('VERCEL_URL')}/webhook/"
    
#     try:
#         await bot.set_webhook(webhook_url)
#         print(f"Webhook set to: {webhook_url}")
#     except Exception as e:
#         print(f"Error setting webhook: {e}")

async def main():
    """Start the bot's polling loop or set webhook."""
    print("Bot started...")
    # await set_webhook()  # Start or stop the webhook for website
    try:
        await bot.polling(non_stop=True)  # Comment this line if you only want to use webhook
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
    # uvicorn.run(app, host="0.0.0.0", port=8000)
