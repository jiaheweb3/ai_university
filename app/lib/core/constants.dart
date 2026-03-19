/// AetherVerse — 常量定义
library;

class AppConstants {
  AppConstants._();

  // ============================================================
  // API 配置
  // ============================================================
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  static const String wsBaseUrl = String.fromEnvironment(
    'WS_BASE_URL',
    defaultValue: 'ws://localhost:8000/ws',
  );

  // ============================================================
  // 分页
  // ============================================================
  static const int defaultPageSize = 20;
  static const int maxPageSize = 100;
  static const int messagePageSize = 50;

  // ============================================================
  // WebSocket
  // ============================================================
  static const Duration heartbeatInterval = Duration(seconds: 30);
  static const Duration heartbeatTimeout = Duration(seconds: 60);
  static const Duration reconnectMinDelay = Duration(seconds: 1);
  static const Duration reconnectMaxDelay = Duration(seconds: 30);

  // ============================================================
  // 消息限制
  // ============================================================
  static const int maxMessageLength = 500;
  static const int maxNicknameLength = 16;
  static const int minPasswordLength = 8;
  static const int maxPasswordLength = 20;
  static const int smsCodeLength = 6;
  static const int smsCountdownSeconds = 60;

  // ============================================================
  // Token Keys (SharedPreferences)
  // ============================================================
  static const String keyAccessToken = 'access_token';
  static const String keyRefreshToken = 'refresh_token';
  static const String keyTokenExpiry = 'token_expiry';

  // ============================================================
  // 电话号码正则
  // ============================================================
  static final RegExp phonePattern = RegExp(r'^1[3-9]\d{9}$');
}
