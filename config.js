// config.js متطور
window.APP_CONFIG = {
  // سيرفر أساسي
  PRIMARY_SERVER: "https://server1.onrender.com",
  
  // سيرفر احتياطي
  BACKUP_SERVER: "https://server2.onrender.com",
  
  // إعدادات أخرى
  MAX_RETRIES: 3,
  TIMEOUT: 10000,
  
  // دالة لاختيار السيرفر
  getServerUrl: function() {
    return this.PRIMARY_SERVER;
  }
};

var SERVER_URL = window.APP_CONFIG.getServerUrl();
