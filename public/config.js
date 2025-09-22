// config.js متطور
window.APP_CONFIG = {
  // سيرفر أساسي
  PRIMARY_SERVER: "https://bot-k.onrender.com",
  
  // سيرفر احتياطي
  BACKUP_SERVER: "https://bot-k.onrender.com",
  
  // إعدادات أخرى
  MAX_RETRIES: 3,
  TIMEOUT: 10000,
  
  // دالة لاختيار السيرفر
  getServerUrl: function() {
    return this.PRIMARY_SERVER;
  }
};

var SERVER_URL = window.APP_CONFIG.getServerUrl();
