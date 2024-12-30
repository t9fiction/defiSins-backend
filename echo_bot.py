import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_helper

# Your bot token
BOT_TOKEN = '7866254923:AAGQXf1cxomGPJ2xCgVXLfRaE7I3lcMco5g'

# Proxy configuration
asyncio_helper.proxy = 'socks4://129.146.163.153:47060'

# Create bot instance
bot = AsyncTeleBot(BOT_TOKEN)

@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await bot.reply_to(message, "Hi there, I am EchoBot!")

@bot.message_handler(func=lambda message: True)
async def echo_all(message):
    await bot.reply_to(message, message.text)

async def main():
    print("Bot started...")
    try:
        await bot.polling(non_stop=True)
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
