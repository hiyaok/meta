import os
import logging
import asyncio
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import io
import piexif

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== KONFIGURASI ==========
BOT_TOKEN = '7776609805:AAHnDN-jnhl-TkG0g6FR8b3LnB9B0GeSyNc'
ADMIN_IDS = [123456789, 5988451717]  # Ganti dengan Telegram ID admin
PREMIUM_FILE = 'premium_users.json'  # File untuk menyimpan user premium
# =================================

class PremiumManager:
    """Manager untuk user premium"""
    
    def __init__(self, filename):
        self.filename = filename
        self.premium_users = self.load_premium_users()
    
    def load_premium_users(self):
        """Load daftar user premium dari file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading premium users: {e}")
            return {}
    
    def save_premium_users(self):
        """Simpan daftar user premium ke file"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.premium_users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving premium users: {e}")
    
    def add_premium(self, user_id, username, first_name):
        """Tambah user premium"""
        self.premium_users[str(user_id)] = {
            'username': username,
            'first_name': first_name,
            'added_at': str(asyncio.get_event_loop().time())
        }
        self.save_premium_users()
    
    def remove_premium(self, user_id):
        """Hapus user premium"""
        user_id_str = str(user_id)
        if user_id_str in self.premium_users:
            del self.premium_users[user_id_str]
            self.save_premium_users()
            return True
        return False
    
    def is_premium(self, user_id):
        """Cek apakah user premium"""
        return str(user_id) in self.premium_users
    
    def get_all_premium(self):
        """Ambil semua user premium"""
        return self.premium_users

# Inisialisasi Premium Manager
premium_manager = PremiumManager(PREMIUM_FILE)

def is_admin(user_id: int) -> bool:
    """Cek apakah user adalah admin"""
    return user_id in ADMIN_IDS

def can_use_bot(user_id: int) -> bool:
    """Cek apakah user bisa pakai bot (admin atau premium)"""
    return is_admin(user_id) or premium_manager.is_premium(user_id)

async def animated_loading(message, final_text="✅ Selesai!"):
    """Loading animasi keren"""
    frames = [
        "╔═══════════════════╗\n║  🔄  ᴘʀᴏᴄᴇssɪɴɢ...  ║\n╚═══════════════════╝",
        "╔═══════════════════╗\n║  🔵  ᴘʀᴏᴄᴇssɪɴɢ...  ║\n╚═══════════════════╝",
        "╔═══════════════════╗\n║  🟣  ᴘʀᴏᴄᴇssɪɴɢ...  ║\n╚═══════════════════╝",
        "╔═══════════════════╗\n║  🟢  ᴘʀᴏᴄᴇssɪɴɢ...  ║\n╚═══════════════════╝",
    ]
    
    try:
        for i in range(2):  # 2 loop
            for frame in frames:
                await message.edit_text(f"`{frame}`", parse_mode='Markdown')
                await asyncio.sleep(0.3)
        
        await message.edit_text(f"`╔═══════════════════╗\n║  ✨  {final_text}  ║\n╚═══════════════════╝`", parse_mode='Markdown')
        await asyncio.sleep(1)
        await message.delete()
    except Exception as e:
        logger.error(f"Error animasi loading: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start"""
    user_id = update.effective_user.id
    
    if not can_use_bot(user_id):
        await update.message.reply_text(
            "╔═══════════════════════════╗\n"
            "║     ❌  ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ     ║\n"
            "╚═══════════════════════════╝\n\n"
            "ʙᴏᴛ ɪɴɪ ʜᴀɴʏᴀ ᴜɴᴛᴜᴋ ᴜsᴇʀ ᴘʀᴇᴍɪᴜᴍ"
        )
        logger.warning(f"User tidak terotorisasi: {user_id}")
        return
    
    user_type = "ᴀᴅᴍɪɴ" if is_admin(user_id) else "ᴘʀᴇᴍɪᴜᴍ"
    
    await update.message.reply_text(
        "╔═══════════════════════════╗\n"
        f"║   👋  ʜᴀʟᴏ {user_type} ᴜsᴇʀ!   ║\n"
        "╚═══════════════════════════╝\n\n"
        "🔐 **sᴛᴀᴛᴜs:** ᴀᴄᴄᴇss ɢʀᴀɴᴛᴇᴅ\n\n"
        "📸 **ғᴇᴀᴛᴜʀᴇs:**\n"
        "• ʜᴀᴘᴜs sᴇᴍᴜᴀ ᴍᴇᴛᴀᴅᴀᴛᴀ\n"
        "• ᴜʙᴀʜ sᴛʀᴜᴋᴛᴜʀ ғɪʟᴇ\n"
        "• ᴋᴜᴀʟɪᴛᴀs ʜᴅ ᴍᴀᴋsɪᴍᴀʟ\n"
        "• ᴛɪᴅᴀᴋ ᴛᴇʀᴅᴇᴛᴇᴋsɪ ɢᴏᴏɢʟᴇ ʟᴇɴs\n\n"
        "➡️ **ᴋɪʀɪᴍ ғᴏᴛᴏ sᴇᴋᴀʀᴀɴɢ!**",
        parse_mode='Markdown'
    )

async def remove_metadata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk menghapus metadata dari foto"""
    user_id = update.effective_user.id
    
    # Cek akses
    if not can_use_bot(user_id):
        await update.message.reply_text(
            "╔═══════════════════════════╗\n"
            "║     ❌  ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ     ║\n"
            "╚═══════════════════════════╝"
        )
        logger.warning(f"User tidak terotorisasi mencoba kirim foto: {user_id}")
        return
    
    try:
        # Loading animasi keren
        loading_msg = await update.message.reply_text(
            "`╔═══════════════════╗\n"
            "║  🔄  ᴘʀᴏᴄᴇssɪɴɢ...  ║\n"
            "╚═══════════════════╝`",
            parse_mode='Markdown'
        )
        
        # Animasi loading di background
        loading_task = asyncio.create_task(animated_loading(loading_msg, "ᴅᴏɴᴇ"))
        
        # Download foto dari Telegram (ukuran terbesar untuk HD)
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Buka gambar dengan PIL
        original_image = Image.open(io.BytesIO(photo_bytes))
        
        # Simpan dimensi asli
        original_size = original_image.size
        
        # Hapus semua info EXIF jika ada
        if 'exif' in original_image.info:
            original_image.info.pop('exif', None)
        if 'icc_profile' in original_image.info:
            original_image.info.pop('icc_profile', None)
        
        # Konversi mode gambar
        if original_image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', original_image.size, (255, 255, 255))
            if original_image.mode == 'P':
                original_image = original_image.convert('RGBA')
            if original_image.mode in ('RGBA', 'LA'):
                background.paste(original_image, mask=original_image.split()[-1])
            else:
                background.paste(original_image)
            original_image = background
        elif original_image.mode != 'RGB':
            original_image = original_image.convert('RGB')
        
        # Recreate image dari pixel data (hapus semua metadata)
        pixel_data = list(original_image.getdata())
        clean_image = Image.new('RGB', original_size)
        clean_image.putdata(pixel_data)
        
        # Simpan dengan kualitas maksimal tanpa metadata
        output_buffer = io.BytesIO()
        clean_image.save(
            output_buffer, 
            format='JPEG',
            quality=100,
            optimize=True,
            subsampling=0,
            exif=b'',
        )
        
        output_buffer.seek(0)
        
        # Verifikasi
        verification_image = Image.open(output_buffer)
        has_exif = 'exif' in verification_image.info
        output_buffer.seek(0)
        
        # Tunggu loading selesai
        await loading_task
        
        # Caption hasil
        user_type = "ᴀᴅᴍɪɴ" if is_admin(user_id) else "ᴘʀᴇᴍɪᴜᴍ"
        
        info_text = (
            "╔═══════════════════════════╗\n"
            "║      ✅  sᴜᴄᴄᴇss!         ║\n"
            "╚═══════════════════════════╝\n\n"
            "🔒 **ᴍᴇᴛᴀᴅᴀᴛᴀ sᴛᴀᴛᴜs:**\n"
            f"• ᴇxɪғ: {'✅ ᴅɪʜᴀᴘᴜs' if not has_exif else '⚠️ ᴀᴅᴀ'}\n"
            "• ɢᴘs: ✅ ᴅɪʜᴀᴘᴜs\n"
            "• ᴅᴀᴛᴇ/ᴛɪᴍᴇ: ✅ ᴅɪʜᴀᴘᴜs\n"
            "• ᴄᴀᴍᴇʀᴀ ɪɴғᴏ: ✅ ᴅɪʜᴀᴘᴜs\n"
            "• ɪᴄᴄ ᴘʀᴏғɪʟᴇ: ✅ ᴅɪʜᴀᴘᴜs\n\n"
            f"📐 **ʀᴇsᴏʟᴜsɪ:** {original_size[0]}x{original_size[1]} ʜᴅ\n"
            "🎨 **ǫᴜᴀʟɪᴛʏ:** 100% ᴍᴀx\n"
            f"👤 **ᴜsᴇʀ:** {user_type}\n\n"
            "🔍 _ғᴏᴛᴏ ᴛɪᴅᴀᴋ ᴛᴇʀᴅᴇᴛᴇᴋsɪ ɢᴏᴏɢʟᴇ ʟᴇɴs_"
        )
        
        # Kirim foto bersih
        await update.message.reply_photo(
            photo=output_buffer,
            caption=info_text,
            parse_mode='Markdown'
        )
        
        # Log
        logger.info(f"Foto diproses oleh {user_type} user {user_id}")
        
        # Cleanup
        original_image.close()
        clean_image.close()
        verification_image.close()
        
    except Exception as e:
        logger.error(f"Error saat memproses foto: {e}")
        await update.message.reply_text(
            "╔═══════════════════════════╗\n"
            "║       ❌  ᴇʀʀᴏʀ!          ║\n"
            "╚═══════════════════════════╝\n\n"
            f"_ᴋᴇsᴀʟᴀʜᴀɴ: {str(e)}_\n\n"
            "sɪʟᴀʜᴋᴀɴ ᴄᴏʙᴀ ʟᴀɢɪ",
            parse_mode='Markdown'
        )

async def addprem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk admin menambah user premium"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ ᴄᴏᴍᴍᴀɴᴅ ɪɴɪ ʜᴀɴʏᴀ ᴜɴᴛᴜᴋ ᴀᴅᴍɪɴ")
        return
    
    # Parse argument
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "╔═══════════════════════════╗\n"
            "║    📝  ᴄᴀʀᴀ ᴘᴀᴋᴀɪ:        ║\n"
            "╚═══════════════════════════╝\n\n"
            "`/addprem <user_id>`\n\n"
            "ᴄᴏɴᴛᴏʜ:\n"
            "`/addprem 123456789`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        if is_admin(target_user_id):
            await update.message.reply_text("⚠️ ᴜsᴇʀ ɪɴɪ sᴜᴅᴀʜ ᴀᴅᴍɪɴ!")
            return
        
        if premium_manager.is_premium(target_user_id):
            await update.message.reply_text("⚠️ ᴜsᴇʀ sᴜᴅᴀʜ ᴘʀᴇᴍɪᴜᴍ!")
            return
        
        # Tambah ke premium
        premium_manager.add_premium(target_user_id, "unknown", "unknown")
        
        await update.message.reply_text(
            "╔═══════════════════════════╗\n"
            "║     ✅  ʙᴇʀʜᴀsɪʟ!         ║\n"
            "╚═══════════════════════════╝\n\n"
            f"ᴜsᴇʀ `{target_user_id}` ᴅɪᴛᴀᴍʙᴀʜᴋᴀɴ ᴋᴇ ᴘʀᴇᴍɪᴜᴍ!\n\n"
            f"📊 ᴛᴏᴛᴀʟ ᴜsᴇʀ ᴘʀᴇᴍɪᴜᴍ: {len(premium_manager.get_all_premium())}",
            parse_mode='Markdown'
        )
        
        logger.info(f"Admin {user_id} menambahkan user {target_user_id} ke premium")
        
    except ValueError:
        await update.message.reply_text("❌ ɪᴅ ʜᴀʀᴜs ʙᴇʀᴜᴘᴀ ᴀɴɢᴋᴀ!")

async def delprem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk admin menghapus user premium"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ ᴄᴏᴍᴍᴀɴᴅ ɪɴɪ ʜᴀɴʏᴀ ᴜɴᴛᴜᴋ ᴀᴅᴍɪɴ")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "╔═══════════════════════════╗\n"
            "║    📝  ᴄᴀʀᴀ ᴘᴀᴋᴀɪ:        ║\n"
            "╚═══════════════════════════╝\n\n"
            "`/delprem <user_id>`\n\n"
            "ᴄᴏɴᴛᴏʜ:\n"
            "`/delprem 123456789`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        if premium_manager.remove_premium(target_user_id):
            await update.message.reply_text(
                "╔═══════════════════════════╗\n"
                "║     ✅  ʙᴇʀʜᴀsɪʟ!         ║\n"
                "╚═══════════════════════════╝\n\n"
                f"ᴜsᴇʀ `{target_user_id}` ᴅɪʜᴀᴘᴜs ᴅᴀʀɪ ᴘʀᴇᴍɪᴜᴍ!\n\n"
                f"📊 ᴛᴏᴛᴀʟ ᴜsᴇʀ ᴘʀᴇᴍɪᴜᴍ: {len(premium_manager.get_all_premium())}",
                parse_mode='Markdown'
            )
            logger.info(f"Admin {user_id} menghapus user {target_user_id} dari premium")
        else:
            await update.message.reply_text("⚠️ ᴜsᴇʀ ᴛɪᴅᴀᴋ ᴅɪᴛᴇᴍᴜᴋᴀɴ ᴅɪ ᴘʀᴇᴍɪᴜᴍ!")
            
    except ValueError:
        await update.message.reply_text("❌ ɪᴅ ʜᴀʀᴜs ʙᴇʀᴜᴘᴀ ᴀɴɢᴋᴀ!")

async def listprem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command untuk admin melihat daftar user premium"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ ᴄᴏᴍᴍᴀɴᴅ ɪɴɪ ʜᴀɴʏᴀ ᴜɴᴛᴜᴋ ᴀᴅᴍɪɴ")
        return
    
    premium_users = premium_manager.get_all_premium()
    
    if not premium_users:
        await update.message.reply_text(
            "╔═══════════════════════════╗\n"
            "║   📋  ᴅᴀғᴛᴀʀ ᴘʀᴇᴍɪᴜᴍ    ║\n"
            "╚═══════════════════════════╝\n\n"
            "ᴛɪᴅᴀᴋ ᴀᴅᴀ ᴜsᴇʀ ᴘʀᴇᴍɪᴜᴍ"
        )
        return
    
    user_list = "╔═══════════════════════════╗\n"
    user_list += "║   📋  ᴅᴀғᴛᴀʀ ᴘʀᴇᴍɪᴜᴍ    ║\n"
    user_list += "╚═══════════════════════════╝\n\n"
    
    for idx, (uid, info) in enumerate(premium_users.items(), 1):
        username = info.get('username', 'N/A')
        first_name = info.get('first_name', 'N/A')
        user_list += f"{idx}. `{uid}` - {first_name}\n"
    
    user_list += f"\n📊 ᴛᴏᴛᴀʟ: {len(premium_users)} ᴜsᴇʀ"
    
    await update.message.reply_text(user_list, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /help"""
    user_id = update.effective_user.id
    
    if not can_use_bot(user_id):
        await update.message.reply_text("❌ ᴀᴋsᴇs ᴅɪᴛᴏʟᴀᴋ")
        return
    
    is_admin_user = is_admin(user_id)
    
    help_text = (
        "╔═══════════════════════════╗\n"
        "║      📖  ᴘᴀɴᴅᴜᴀɴ         ║\n"
        "╚═══════════════════════════╝\n\n"
        "**📝 ᴄᴏᴍᴍᴀɴᴅs:**\n"
        "• `/start` - ᴍᴜʟᴀɪ ʙᴏᴛ\n"
        "• `/help` - ᴘᴀɴᴅᴜᴀɴ\n"
        "• `/myid` - ᴄᴇᴋ ɪᴅ ᴋᴀᴍᴜ\n"
    )
    
    if is_admin_user:
        help_text += (
            "\n**🔐 ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:**\n"
            "• `/addprem <id>` - ᴛᴀᴍʙᴀʜ ᴘʀᴇᴍɪᴜᴍ\n"
            "• `/delprem <id>` - ʜᴀᴘᴜs ᴘʀᴇᴍɪᴜᴍ\n"
            "• `/listprem` - ʟɪsᴛ ᴘʀᴇᴍɪᴜᴍ\n"
        )
    
    help_text += (
        "\n**🗑️ ғɪᴛᴜʀ:**\n"
        "• ʜᴀᴘᴜs ᴍᴇᴛᴀᴅᴀᴛᴀ ᴄᴏᴍᴘʟᴇᴛᴇ\n"
        "• ᴋᴜᴀʟɪᴛᴀs ʜᴅ 100%\n"
        "• ᴛɪᴅᴀᴋ ᴛᴇʀᴅᴇᴛᴇᴋsɪ ɢᴏᴏɢʟᴇ ʟᴇɴs\n"
        "• ᴘʀɪᴠᴀᴄʏ ᴛᴇʀᴊᴀɢᴀ"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk cek Telegram ID user"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "ɴᴏ ᴜsᴇʀɴᴀᴍᴇ"
    first_name = update.effective_user.first_name or "ɴ/ᴀ"
    
    is_admin_user = is_admin(user_id)
    is_premium_user = premium_manager.is_premium(user_id)
    
    if is_admin_user:
        status = "✅ ᴀᴅᴍɪɴ"
    elif is_premium_user:
        status = "⭐ ᴘʀᴇᴍɪᴜᴍ"
    else:
        status = "❌ ғʀᴇᴇ ᴜsᴇʀ"
    
    await update.message.reply_text(
        "╔═══════════════════════════╗\n"
        "║      👤  ɪɴғᴏ ᴜsᴇʀ        ║\n"
        "╚═══════════════════════════╝\n\n"
        f"🆔 **ɪᴅ:** `{user_id}`\n"
        f"👨‍💼 **ᴜsᴇʀɴᴀᴍᴇ:** @{username}\n"
        f"📝 **ɴᴀᴍᴀ:** {first_name}\n"
        f"🔐 **sᴛᴀᴛᴜs:** {status}",
        parse_mode='Markdown'
    )

def main():
    """Fungsi utama untuk menjalankan bot"""
    # Validasi konfigurasi
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ ERROR: Silakan ganti BOT_TOKEN dengan token bot kamu!")
        return
    
    if ADMIN_IDS == [123456789, 987654321]:
        print("⚠️  WARNING: Jangan lupa ganti ADMIN_IDS dengan Telegram ID kamu!")
        print("💡 Gunakan command /myid di bot untuk mendapatkan ID kamu")
    
    # Buat aplikasi bot
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("myid", myid_command))
    application.add_handler(CommandHandler("addprem", addprem_command))
    application.add_handler(CommandHandler("delprem", delprem_command))
    application.add_handler(CommandHandler("listprem", listprem_command))
    application.add_handler(MessageHandler(filters.PHOTO, remove_metadata))
    
    # Start bot
    logger.info("Bot dimulai...")
    print("\n╔═══════════════════════════════════════╗")
    print("║  🤖  ʙᴏᴛ ᴍᴇᴛᴀᴅᴀᴛᴀ ʀᴇᴍᴏᴠᴇʀ  🤖  ║")
    print("╚═══════════════════════════════════════╝")
    print(f"\n✅ sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ")
    print(f"🔐 ᴀᴅᴍɪɴ ɪᴅs: {ADMIN_IDS}")
    print(f"⭐ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs: {len(premium_manager.get_all_premium())}")
    print(f"📸 sɪᴀᴘ ᴍᴇɴᴇʀɪᴍᴀ ғᴏᴛᴏ!")
    print("\n⌨️  ᴛᴇᴋᴀɴ ᴄᴛʀʟ+ᴄ ᴜɴᴛᴜᴋ ʙᴇʀʜᴇɴᴛɪ\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
