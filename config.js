// config.js - ضعه على سيرفر مركزي موثوق
// مثال: https://my-central-server.com/config.js

(function() {
    'use strict';
    
    // 🔄 الإصدار الحالي - يغير نفسه تلقائياً
    var CONFIG_VERSION = '2.3_' + new Date().getTime();
    
    // 🌐 رابط السيرفر الجديد - غير هذا فقط عندما تريد التبديل
    var NEW_SERVER_URL = "https://bot-k.onrender.com";
    
    // 🎯 محاولة منع التخزين المؤقت بطرق متعددة
    if (typeof window !== 'undefined') {
        // 1. تعيين المتغير الرئيسي
        window.SERVER_URL = NEW_SERVER_URL;
        
        // 2. تعيين إصدار التكوين للتتبع
        window.CONFIG_VERSION = CONFIG_VERSION;
        
        // 3. إضافة تاريخ التحديث
        window.CONFIG_LAST_UPDATE = new Date().toISOString();
        
        // 4. التحقق من وجود تكوين قديم وإعادة التحميل إذا اختلف
        if (window.OLD_SERVER_URL && window.OLD_SERVER_URL !== NEW_SERVER_URL) {
            console.log('🔄 تم تغيير السيرفر من ' + window.OLD_SERVER_URL + ' إلى ' + NEW_SERVER_URL);
            
            // إعادة تحميل الصفحة بعد ثانيتين إذا تغير السيرفر
            setTimeout(function() {
                if (window.location && !window.location.href.includes('reload')) {
                    window.location.reload(true);
                }
            }, 2000);
        }
        
        // 5. حفظ السيرفر الحالي للمقارنة المستقبلية
        window.OLD_SERVER_URL = NEW_SERVER_URL;
        
        // 6. رسالة تأكيد في الكونسول
        console.log('✅ تم تحميل التكوين بنجاح - السيرفر: ' + NEW_SERVER_URL);
        console.log('📅 إصدار التكوين: ' + CONFIG_VERSION);
    }
    
    // 7. لمنع التخزين المؤقت، أضف رأسيات HTTP إذا كان الخادم يدعم ذلك
    if (typeof document !== 'undefined') {
        var meta = document.createElement('meta');
        meta.httpEquiv = 'Cache-Control';
        meta.content = 'no-cache, no-store, must-revalidate';
        document.head.appendChild(meta);
    }
})();
