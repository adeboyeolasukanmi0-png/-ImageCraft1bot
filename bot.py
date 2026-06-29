import os
import logging
import random
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import requests

# ============= LOGGING SETUP =============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= ENVIRONMENT VARIABLES =============
BOT_TOKEN = os.environ.get('BOT_TOKEN')
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'ImageCraft1Bot')
BOT_NAME = os.environ.get('BOT_NAME', 'ImageCraft1Bot')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable is not set!")
    raise ValueError("BOT_TOKEN is required. Add it to Railway variables.")

logger.info(f"✅ Starting {BOT_NAME} (@{BOT_USERNAME})")

# ============= IMAGE GENERATION FUNCTIONS =============

def generate_random_image(width=500, height=500):
    """Generate a random abstract image"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw random shapes
    for _ in range(15):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(x1, width)
        y2 = random.randint(y1, height)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        shape_type = random.choice(['rectangle', 'ellipse', 'triangle'])
        
        if shape_type == 'rectangle':
            draw.rectangle([x1, y1, x2, y2], fill=color)
        elif shape_type == 'ellipse':
            draw.ellipse([x1, y1, x2, y2], fill=color)
        else:
            draw.polygon([(x1, y1), (x2, y2), (random.randint(0, width), random.randint(0, height))], fill=color)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def generate_pattern_image(width=500, height=500):
    """Generate a pattern image"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Create grid pattern
    spacing = 50
    for x in range(0, width, spacing):
        draw.line([(x, 0), (x, height)], fill='gray', width=1)
    for y in range(0, height, spacing):
        draw.line([(0, y), (width, y)], fill='gray', width=1)
    
    # Add random colored circles at intersections
    for x in range(spacing, width, spacing):
        for y in range(spacing, height, spacing):
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            draw.ellipse([x-8, y-8, x+8, y+8], fill=color)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def generate_gradient_image(width=500, height=500, color1="#FF0000", color2="#0000FF"):
    """Generate a gradient image between two colors"""
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)
    
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    for x in range(width):
        ratio = x / width
        r = int(c1[0] + (c2[0] - c1[0]) * ratio)
        g = int(c1[1] + (c2[1] - c1[1]) * ratio)
        b = int(c1[2] + (c2[2] - c1[2]) * ratio)
        for y in range(height):
            pixels[x, y] = (r, g, b)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def generate_meme_image(width=500, height=500, top_text="Top Text", bottom_text="Bottom Text"):
    """Generate a meme-style image with text"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    draw.text((width//2, 50), top_text, fill='black', font=font, anchor='mt')
    draw.text((width//2, height-50), bottom_text, fill='black', font=font, anchor='mb')
    
    # Add a border
    draw.rectangle([0, 0, width-1, height-1], outline='black', width=3)
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def generate_avatar_image(width=500, height=500, initials="AB"):
    """Generate an avatar with initials"""
    img = Image.new('RGB', (width, height), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    draw = ImageDraw.Draw(img)
    
    # Draw a circle
    draw.ellipse([50, 50, width-50, height-50], fill='white', outline='black', width=3)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 150)
    except:
        font = ImageFont.load_default()
    
    # Draw initials
    draw.text((width//2, height//2), initials, fill='black', font=font, anchor='mm')
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def generate_qr_code(data="https://t.me/ImageCraft1Bot"):
    """Generate a QR code"""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
    except ImportError:
        # Fallback if qrcode not installed
        return generate_random_image()

# ============= USER DATA =============
user_data = {}

# ============= COMMAND HANDLERS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    first_name = user.first_name or "User"
    
    welcome_text = (
        f"🎨 *Welcome to {BOT_NAME}, {first_name}!*\n\n"
        f"I'm @{BOT_USERNAME}, your image crafting bot!\n\n"
        "🖼️ *What I can do:*\n"
        "• Generate random abstract images\n"
        "• Create pattern images\n"
        "• Generate gradient images\n"
        "• Make meme images with text\n"
        "• Create avatars with initials\n"
        "• Generate QR codes\n\n"
        "👇 *How to use:*\n"
        "• Click a button below\n"
        "• Send me text for memes/avatars\n\n"
        "📤 *Commands:*\n"
        "/random - Random image\n"
        "/pattern - Pattern image\n"
        "/gradient - Gradient image\n"
        "/meme - Meme image\n"
        "/avatar - Avatar image\n"
        "/qr - QR code\n"
        "/about - About this bot"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 Random Image", callback_data="random"),
            InlineKeyboardButton("🔲 Pattern", callback_data="pattern"),
        ],
        [
            InlineKeyboardButton("🌊 Gradient", callback_data="gradient"),
            InlineKeyboardButton("😂 Meme", callback_data="meme"),
        ],
        [
            InlineKeyboardButton("👤 Avatar", callback_data="avatar"),
            InlineKeyboardButton("📱 QR Code", callback_data="qr"),
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command."""
    about_text = (
        "ℹ️ *About ImageCraftBot*\n\n"
        "🎨 Image Generation Bot\n\n"
        "🖼️ *Features:*\n"
        "• Random abstract images\n"
        "• Pattern images\n"
        "• Gradient images\n"
        "• Meme images with text\n"
        "• Avatar with initials\n"
        "• QR code generation\n\n"
        "Made with ❤️ using Python"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        about_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def random_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /random command."""
    await update.message.reply_text("🎨 Generating random image...")
    img = generate_random_image()
    
    keyboard = [
        [
            InlineKeyboardButton("🎲 Another", callback_data="random"),
            InlineKeyboardButton("🔲 Pattern", callback_data="pattern"),
        ],
        [
            InlineKeyboardButton("🔙 Menu", callback_data="menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=img,
        caption="🎲 *Random Abstract Image*\n\nA unique random image just for you!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def pattern_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pattern command."""
    await update.message.reply_text("🔲 Generating pattern image...")
    img = generate_pattern_image()
    
    keyboard = [
        [
            InlineKeyboardButton("🔲 Another", callback_data="pattern"),
            InlineKeyboardButton("🎲 Random", callback_data="random"),
        ],
        [
            InlineKeyboardButton("🔙 Menu", callback_data="menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=img,
        caption="🔲 *Pattern Image*\n\nA beautiful geometric pattern!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def gradient_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /gradient command."""
    await update.message.reply_text("🌊 Generating gradient image...")
    img = generate_gradient_image()
    
    keyboard = [
        [
            InlineKeyboardButton("🌊 Another", callback_data="gradient"),
            InlineKeyboardButton("🎲 Random", callback_data="random"),
        ],
        [
            InlineKeyboardButton("🔙 Menu", callback_data="menu"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=img,
        caption="🌊 *Gradient Image*\n\nSmooth color transition!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def meme_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /meme command."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': None}
    
    user_data[user_id]['action'] = 'meme'
    
    await update.message.reply_text(
        "😂 *Meme Generator*\n\n"
        "Send me text in this format:\n"
        "`Top text | Bottom text`\n\n"
        "Example: `Hello | World`\n\n"
        "Or just send any text!",
        parse_mode='Markdown'
    )


async def avatar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /avatar command."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': None}
    
    user_data[user_id]['action'] = 'avatar'
    
    await update.message.reply_text(
        "👤 *Avatar Generator*\n\n"
        "Send me your initials (2 letters)!\n"
        "Example: `AB` for Alice Bob\n\n"
        "Or just send any text!",
        parse_mode='Markdown'
    )


async def qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /qr command."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': None}
    
    user_data[user_id]['action'] = 'qr'
    
    await update.message.reply_text(
        "📱 *QR Code Generator*\n\n"
        "Send me text or a URL to generate a QR code!\n"
        "Example: `https://t.me/ImageCraft1Bot`\n\n"
        "Or use: `/qr text`",
        parse_mode='Markdown'
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    if user_id not in user_data:
        user_data[user_id] = {'action': None}
    
    action = user_data[user_id].get('action', None)
    
    if action == 'meme':
        await update.message.reply_text("😂 Generating your meme...")
        
        # Split text for top and bottom
        if '|' in text:
            parts = text.split('|')
            top_text = parts[0].strip()
            bottom_text = parts[1].strip() if len(parts) > 1 else ""
        else:
            top_text = text
            bottom_text = ""
        
        img = generate_meme_image(top_text=top_text, bottom_text=bottom_text)
        
        keyboard = [
            [
                InlineKeyboardButton("😂 Another Meme", callback_data="meme"),
                InlineKeyboardButton("🎲 Random", callback_data="random"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=img,
            caption=f"😂 *Your Meme*\n\nTop: {top_text}\nBottom: {bottom_text}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        user_data[user_id]['action'] = None
        
    elif action == 'avatar':
        await update.message.reply_text("👤 Generating your avatar...")
        
        # Get initials (max 2 characters)
        initials = text[:2].upper()
        img = generate_avatar_image(initials=initials)
        
        keyboard = [
            [
                InlineKeyboardButton("👤 Another", callback_data="avatar"),
                InlineKeyboardButton("🎲 Random", callback_data="random"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=img,
            caption=f"👤 *Your Avatar*\n\nInitials: {initials}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        user_data[user_id]['action'] = None
        
    elif action == 'qr':
        await update.message.reply_text("📱 Generating QR code...")
        
        img = generate_qr_code(text)
        
        keyboard = [
            [
                InlineKeyboardButton("📱 Another", callback_data="qr"),
                InlineKeyboardButton("🎲 Random", callback_data="random"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=img,
            caption=f"📱 *QR Code*\n\nData: {text[:50]}{'...' if len(text) > 50 else ''}",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        user_data[user_id]['action'] = None
        
    else:
        # Default response
        await update.message.reply_text(
            "❓ I didn't understand that.\n\n"
            "Use /start to see what I can do!\n"
            "Or use /help for commands."
        )


# ============= CALLBACK QUERY HANDLERS =============

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = str(query.from_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {'action': None}
    
    # ===== MENU =====
    if data == "menu":
        keyboard = [
            [
                InlineKeyboardButton("🎲 Random Image", callback_data="random"),
                InlineKeyboardButton("🔲 Pattern", callback_data="pattern"),
            ],
            [
                InlineKeyboardButton("🌊 Gradient", callback_data="gradient"),
                InlineKeyboardButton("😂 Meme", callback_data="meme"),
            ],
            [
                InlineKeyboardButton("👤 Avatar", callback_data="avatar"),
                InlineKeyboardButton("📱 QR Code", callback_data="qr"),
            ],
            [
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🎨 *Welcome to ImageCraftBot!*\n\nWhat would you like to create?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== RANDOM =====
    elif data == "random":
        await query.delete_message()
        img = generate_random_image()
        
        keyboard = [
            [
                InlineKeyboardButton("🎲 Another", callback_data="random"),
                InlineKeyboardButton("🔲 Pattern", callback_data="pattern"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_photo(
            photo=img,
            caption="🎲 *Random Abstract Image*\n\nA unique random image just for you!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== PATTERN =====
    elif data == "pattern":
        await query.delete_message()
        img = generate_pattern_image()
        
        keyboard = [
            [
                InlineKeyboardButton("🔲 Another", callback_data="pattern"),
                InlineKeyboardButton("🎲 Random", callback_data="random"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_photo(
            photo=img,
            caption="🔲 *Pattern Image*\n\nA beautiful geometric pattern!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== GRADIENT =====
    elif data == "gradient":
        await query.delete_message()
        img = generate_gradient_image()
        
        keyboard = [
            [
                InlineKeyboardButton("🌊 Another", callback_data="gradient"),
                InlineKeyboardButton("🎲 Random", callback_data="random"),
            ],
            [
                InlineKeyboardButton("🔙 Menu", callback_data="menu"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_photo(
            photo=img,
            caption="🌊 *Gradient Image*\n\nSmooth color transition!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # ===== MEME =====
    elif data == "meme":
        user_data[user_id]['action'] = 'meme'
        await query.edit_message_text(
            "😂 *Meme Generator*\n\n"
            "Send me text in this format:\n"
            "`Top text | Bottom text`\n\n"
            "Example: `Hello | World`\n\n"
            "Or just send any text!",
            parse_mode='Markdown'
        )
    
    # ===== AVATAR =====
    elif data == "avatar":
        user_data[user_id]['action'] = 'avatar'
        await query.edit_message_text(
            "👤 *Avatar Generator*\n\n"
            "Send me your initials (2 letters)!\n"
            "Example: `AB` for Alice Bob",
            parse_mode='Markdown'
        )
    
    # ===== QR =====
    elif data == "qr":
        user_data[user_id]['action'] = 'qr'
        await query.edit_message_text(
            "📱 *QR Code Generator*\n\n"
            "Send me text or a URL to generate a QR code!\n"
            "Example: `https://t.me/ImageCraft1Bot`",
            parse_mode='Markdown'
        )
    
    # ===== ABOUT =====
    elif data == "about":
        about_text = (
            "ℹ️ *About ImageCraftBot*\n\n"
            "🎨 Image Generation Bot\n\n"
            "🖼️ *Features:*\n"
            "• Random abstract images\n"
            "• Pattern images\n"
            "• Gradient images\n"
            "• Meme images with text\n"
            "• Avatar with initials\n"
            "• QR code generation\n\n"
            "Made with ❤️ using Python"
        )
        keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            about_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )


def main():
    """Start the bot."""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("about", about))
        application.add_handler(CommandHandler("random", random_image))
        application.add_handler(CommandHandler("pattern", pattern_image))
        application.add_handler(CommandHandler("gradient", gradient_image))
        application.add_handler(CommandHandler("meme", meme_command))
        application.add_handler(CommandHandler("avatar", avatar_command))
        application.add_handler(CommandHandler("qr", qr_command))
        
        # Callback handler
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Message handler for text
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        logger.info("🚀 Bot started successfully!")
        logger.info(f"📱 Bot username: @{BOT_USERNAME}")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()
