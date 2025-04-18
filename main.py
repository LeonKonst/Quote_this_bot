import os
import discord
from discord.ext import commands
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap
from dotenv import load_dotenv

# Have a .env file inside the same folder as main.py with a variable named TOKEN
# dont add "" around the string (token value)
load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Colors pallete
background = "#423E37"
circular_frame_color = "#E3B23C"
text_color = "#EDEBD7"

# Using ! as a command prefix. The command is !quote_this and is only used when you reply to a message.
bot = commands.Bot(command_prefix='!', intents=intents)

# Function that generates the image using data from the reference message.
async def generate_quote_image(message):

    # Get user avatar
    avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
    response = requests.get(avatar_url)
    avatar = Image.open(BytesIO(response.content)).convert("RGBA")
    
    # Creating the frame of the produced quote image. 
    img = Image.new('RGB', (800, 300), color=background)
    draw = ImageDraw.Draw(img)
    
    # Resize and paste avatar
    avatar = avatar.resize((200, 200))

    # Create circular frame for avatar image.
    mask = Image.new('L', (200, 200), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, 200, 200), fill=255)  

    # Creating circular frame
    frame = Image.new('RGBA', (210, 210), (0, 0, 0, 0))  
    draw_frame = ImageDraw.Draw(frame)
    draw_frame.ellipse((0, 0, 210, 210), fill=circular_frame_color) 
    draw_frame.ellipse((5, 5, 205, 205), fill=(0, 0, 0, 0))  

    # Place avatar then mask on top.
    img.paste(avatar, (45, 50), mask)  
    img.paste(frame, (40, 45), frame)  
    
    # Load fonts
    try:
        quote_font = ImageFont.truetype("arial.ttf", 24)
        author_font = ImageFont.truetype("arial.ttf", 20)
    except:
        quote_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
    
    # Format and wrap text
    wrapped_text = textwrap.fill(f"{message.content}", width = 30)
    date_str = message.created_at.strftime("%d-%m-%Y")  
    author_name = f"- {message.author.display_name}, {date_str}"
    
    # Draw text
    draw.text((300, 50), wrapped_text, fill=text_color, font=quote_font)
    draw.text((500, 250), author_name, fill=text_color, font=author_font)
    
    # Save to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # and then return it
    return img_bytes

@bot.command(name='quote_this')
async def quote_this(ctx):

    # The bot quotes only when a person replies to a message
    if not ctx.message.reference:
        await ctx.send("❌ Please reply to a message with `!quote_this` to quote it.")
        return

    try:
        # Fetch message
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        
        # Check if message is link-only or attachment-only
        if not replied_message.content.strip() and (replied_message.attachments or replied_message.embeds):
            await ctx.send("⚠️ Cannot quote messages that contain only links or files.")
            return
            
        # Check if message is empty (edge case)
        if not replied_message.content and not replied_message.attachments:
            await ctx.send("⚠️ The message you're trying to quote is empty.")
            return
            
        # Generate the quote image
        async with ctx.typing():
            image_bytes = await generate_quote_image(replied_message)
            await ctx.send(file=discord.File(image_bytes, filename='quote.png'))
            
    # Except error cases (bot doesn't have acces to a message or the message was removed etc.)        
    except discord.NotFound:
        await ctx.send("🔍 Couldn't find the original message. Was it deleted?")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {str(e)}")

bot.run(TOKEN)