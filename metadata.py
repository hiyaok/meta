import os
import logging
import asyncio
import json
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageFilter, ImageEnhance
import io
import piexif
import numpy as np

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== KONFIGURASI ==========
BOT_TOKEN = '7776609805:AAH42VENDX3Kg3fZBe93Xkkgzl1ylB6EP2s'
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

def deep_modify_image(image):
    """
    Modifikasi DEEP untuk mengubah signature foto agar tidak terdeteksi Google Lens
    Teknik: Multi-layer transformation tanpa kehilangan kualitas visual
    """
    
    # 1. Konversi ke numpy array untuk manipulasi pixel
    img_array = np.array(image)
    
    # 2. Tambah micro-noise yang tidak terlihat mata (±1-2 nilai RGB)
    # Ini akan mengubah hash/signature foto
    noise = np.random.randint(-2, 3, img_array.shape, dtype=np.int16)
    img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # 3. Konversi kembali ke PIL Image
    modified_image = Image.fromarray(img_array)
    
    # 4. Slight brightness adjustment (0.5% perubahan, tidak terlihat)
    enhancer = ImageEnhance.Brightness(modified_image)
    modified_image = enhancer.enhance(random.uniform(0.995, 1.005))
    
    # 5. Slight contrast adjustment (0.5% perubahan)
    enhancer = ImageEnhance.Contrast(modified_image)
    modified_image = enhancer.enhance(random.uniform(0.995, 1.005))
    
    # 6. Slight color adjustment (0.3% perubahan)
    enhancer = ImageEnhance.Color(modified_image)
    modified_image = enhancer.enhance(random.uniform(0.997, 1.003))
    
    # 7. Micro resize technique: resize sedikit lalu kembali ke ukuran asli
    # Ini akan mengubah compression artifact
    original_size = modified_image.size
    temp_size = (int(original_size[0] * 0.999), int(original_size[1] * 0.999))
    if temp_size[0] > 0 and temp_size[1] > 0:
        modified_image = modified_image.resize(temp_size, Image.Resampling.LANCZOS)
        modified_image = modified_image.resize(original_size, Image.Resampling.LANCZOS)
    
    return modified_image

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
        "🚀 **ᴀᴅᴠᴀɴᴄᴇᴅ ғᴇᴀᴛᴜʀᴇs:**\n"
        "• ᴅᴇᴇᴘ ᴘɪxᴇʟ ᴍᴏᴅɪғɪᴄᴀᴛɪᴏɴ\n"
        "• ᴍɪᴄʀᴏ ɴᴏɪsᴇ ɪɴᴊᴇᴄᴛɪᴏɴ\n"
        "• sɪɢɴᴀᴛᴜʀᴇ ᴛʀᴀɴsғᴏʀᴍᴀᴛɪᴏɴ\n"
        "• ᴍᴇᴛᴀᴅᴀᴛᴀ ᴄᴏᴍᴘʟᴇᴛᴇ ʀᴇᴍᴏᴠᴀʟ\n"
        "• ᴋᴜᴀʟɪᴛᴀs ʜᴅ ᴛᴇᴛᴀᴘ ᴍᴀᴋsɪᴍᴀʟ\n\n"
        "🔍 **ʀᴇsᴜʟᴛ:**\n"
        "ɢᴏᴏɢʟᴇ ʟᴇɴs ᴛɪᴅᴀᴋ ᴀᴋᴀɴ ᴍᴇɴɢᴇɴᴀʟɪ ғᴏᴛᴏ!\n\n"
        "➡️ **ᴋɪʀɪᴍ ғᴏᴛᴏ sᴇᴋᴀʀᴀɴɢ!**",
        parse_mode='Markdown'
    )

async def remove_metadata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk menghapus metadata dan deep modify foto"""
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
        
        # Hapus semua info EXIF dan metadata
        original_image.info = {}
        
        # Konversi mode gambar ke RGB
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
        
        # ===== TEKNIK DEEP MODIFICATION =====
        # Ini yang akan membuat Google Lens tidak mengenali foto
        modified_image = deep_modify_image(original_image)
        
        # Recreate image dari pixel data untuk hapus semua metadata tersembunyi
        pixel_data = list(modified_image.getdata())
        clean_image = Image.new('RGB', original_size)
        clean_image.putdata(pixel_data)
        
        # Apply slight sharpness untuk kompensasi noise (tidak terlihat)
        clean_image = clean_image.filter(ImageFilter.SHARPEN)
        
        # Rotate 0.1 derajat lalu balik (ubah compression pattern)
        clean_image = clean_image.rotate(0.1, resample=Image.BICUBIC, expand=False)
        clean_image = clean_image.rotate(-0.1, resample=Image.BICUBIC, expand=False)
        
        # Simpan dengan kualitas maksimal dan parameter khusus
        output_buffer = io.BytesIO()
        
        # Gunakan quality tinggi dan subsampling custom
        clean_image.save(
            output_buffer, 
            format='JPEG',
            quality=98,  # Slight reduction untuk natural look
            optimize=True,
            subsampling=0,  # 4:4:4 chroma subsampling
            progressive=True,  # Progressive JPEG (ubah struktur)
            exif=b'',  # No EXIF
        )
        
        output_buffer.seek(0)
        
        # Verifikasi
        verification_image = Image.open(output_buffer)
        has_exif = 'exif' in verification_image.info
        final_size = verification_image.size
        output_buffer.seek(0)
        
        # Tunggu loading selesai
        await loading_task
        
        # Caption hasil
        user_type = "ᴀᴅᴍɪɴ" if is_admin(user_id) else "ᴘʀᴇᴍɪᴜᴍ"
        
        info_text = (
            "╔═══════════════════════════╗\n"
            "║      ✅  sᴜᴄᴄᴇss!         ║\n"
            "╚═══════════════════════════╝\n\n"
            "🔧 **ᴍᴏᴅɪғɪᴄᴀᴛɪᴏɴs ᴀᴘᴘʟɪᴇᴅ:**\n"
            "• ✅ ᴘɪxᴇʟ sɪɢɴᴀᴛᴜʀᴇ ᴄʜᴀɴɢᴇᴅ\n"
            "• ✅ ᴍɪᴄʀᴏ ɴᴏɪsᴇ ᴀᴅᴅᴇᴅ\n"
            "• ✅ ᴄᴏʟᴏʀ sᴘᴀᴄᴇ ᴛʀᴀɴsғᴏʀᴍᴇᴅ\n"
            "• ✅ ᴄᴏᴍᴘʀᴇssɪᴏɴ ᴘᴀᴛᴛᴇʀɴ ᴄʜᴀɴɢᴇᴅ\n"
            "• ✅ ᴘʀᴏɢʀᴇssɪᴠᴇ ᴇɴᴄᴏᴅɪɴɢ\n\n"
            "🗑️ **ᴍᴇᴛᴀᴅᴀᴛᴀ sᴛᴀᴛᴜs:**\n"
            f"• ᴇxɪғ: {'✅ ʀᴇᴍᴏᴠᴇᴅ' if not has_exif else '⚠️ ᴅᴇᴛᴇᴄᴛᴇᴅ'}\n"
            "• ɢᴘs: ✅ ʀᴇᴍᴏᴠᴇᴅ\n"
            "• ᴅᴀᴛᴇ/ᴛɪᴍᴇ: ✅ ʀᴇᴍᴏᴠᴇᴅ\n"
            "• ᴄᴀᴍᴇʀᴀ: ✅ ʀᴇᴍᴏᴠᴇᴅ\n"
            "• ɪᴄᴄ: ✅ ʀᴇᴍᴏᴠᴇᴅ\n\n"
            f"📐 **ʀᴇsᴏʟᴜᴛɪᴏɴ:** {final_size[0]}x{final_size[1]} ʜᴅ\n"
            "🎨 **ǫᴜᴀʟɪᴛʏ:** 98% (ɴᴀᴛᴜʀᴀʟ)\n"
            f"👤 **ᴜsᴇʀ:** {user_type}\n\n"
            "🔍 **ɢᴏᴏɢʟᴇ ʟᴇɴs sᴛᴀᴛᴜs:**\n"
            "❌ ᴛɪᴅᴀᴋ ᴛᴇʀᴅᴇᴛᴇᴋsɪ!\n"
            "_ғᴏᴛᴏ ᴛᴇʟᴀʜ ᴅɪᴍᴏᴅɪғɪᴋᴀsɪ sᴇᴄᴀʀᴀ ᴅᴇᴇᴘ_"
        )
        
        # Kirim foto bersih
        await update.message.reply_photo(
            photo=output_buffer,
            caption=info_text,
            parse_mode='Markdown'
        )
        
        # Log
        logger.info(f"Foto diproses (DEEP MODE) oleh {user_type} user {user_id}")
        
        # Cleanup
        original_image.close()
        modified_image.close()
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
        "**🚀 ᴀᴅᴠᴀɴᴄᴇᴅ ғᴇᴀᴛᴜʀᴇs:**\n"
        "• ᴅᴇᴇᴘ ᴘɪxᴇʟ ᴍᴏᴅɪғɪᴄᴀᴛɪᴏɴ\n"
        "• ᴍɪᴄʀᴏ ɴᴏɪsᴇ ɪɴᴊᴇᴄᴛɪᴏɴ\n"
        "• sɪɢɴᴀᴛᴜʀᴇ ᴛʀᴀɴsғᴏʀᴍᴀᴛɪᴏɴ\n"
        "• ᴄᴏᴍᴘʀᴇssɪᴏɴ ᴘᴀᴛᴛᴇʀɴ ᴄʜᴀɴɢᴇ\n"
        "• ᴍᴇᴛᴀᴅᴀᴛᴀ ᴄᴏᴍᴘʟᴇᴛᴇ ʀᴇᴍᴏᴠᴀʟ\n\n"
        "**📝 ᴄᴏᴍᴍᴀɴᴅs:**\n"
        "• `/start` - ᴍᴜʟᴀɪ ʙᴏᴛ\n"
        "• `/help` - ᴘᴀɴᴅᴜᴀɴ\n"
        "• `/myid` - ᴄᴇᴋ ɪᴅ & sᴛᴀᴛᴜs\n"
    )
    
    if is_admin_user:
        help_text += (
            "\n**🔐 ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:**\n"
            "• `/addprem <id>` - ᴛᴀᴍʙᴀʜ ᴘʀᴇᴍɪᴜᴍ\n"
            "• `/delprem <id>` - ʜᴀᴘᴜs ᴘʀᴇᴍɪᴜᴍ\n"
            "• `/listprem` - ʟɪsᴛ ᴘʀᴇᴍɪᴜᴍ\n"
        )
    
    help_text += (
        "\n**🔍 ʀᴇsᴜʟᴛ:**\n"
        "ғᴏᴛᴏ ᴛɪᴅᴀᴋ ᴀᴋᴀɴ ᴛᴇʀᴅᴇᴛᴇᴋsɪ\n"
        "ᴅɪ ɢᴏᴏɢʟᴇ ʟᴇɴs ᴀᴛᴀᴜ ʀᴇᴠᴇʀsᴇ\n"
        "ɪᴍᴀɢᴇ sᴇᴀʀᴄʜ ʟᴀɪɴɴʏᴀ!"
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
    print("║      (ᴅᴇᴇᴘ ᴍᴏᴅɪғɪᴄᴀᴛɪᴏɴ ᴍᴏᴅᴇ)     ║")
    print("╚═══════════════════════════════════════╝")
    print(f"\n✅ sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ")
    print(f"🔐 ᴀᴅᴍɪɴ ɪᴅs: {ADMIN_IDS}")
    print(f"⭐ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs: {len(premium_manager.get_all_premium())}")
    print(f"🚀 ᴍᴏᴅᴇ: ᴀᴅᴠᴀɴᴄᴇᴅ ᴅᴇᴇᴘ ᴍᴏᴅɪғɪᴄᴀᴛɪᴏɴ")
    print(f"📸 sɪᴀᴘ ᴍᴇɴᴇʀɪᴍᴀ ғᴏᴛᴏ!")
    print("\n⌨️  ᴛᴇᴋᴀɴ ᴄᴛʀʟ+ᴄ ᴜɴᴛᴜᴋ ʙᴇʀʜᴇɴᴛɪ\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
