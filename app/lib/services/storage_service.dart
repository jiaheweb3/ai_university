/// AetherVerse — 本地存储服务
library;

import 'package:shared_preferences/shared_preferences.dart';

import '../core/constants.dart';

class StorageService {
  static late SharedPreferences _prefs;

  /// 初始化 (main.dart 中调用)
  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // ============================================================
  // Token 管理
  // ============================================================

  static Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    required int expiresIn,
  }) async {
    final expiry = DateTime.now().add(Duration(seconds: expiresIn));
    await Future.wait([
      _prefs.setString(AppConstants.keyAccessToken, accessToken),
      _prefs.setString(AppConstants.keyRefreshToken, refreshToken),
      _prefs.setString(AppConstants.keyTokenExpiry, expiry.toIso8601String()),
    ]);
  }

  static String? get accessToken =>
      _prefs.getString(AppConstants.keyAccessToken);

  static String? get refreshToken =>
      _prefs.getString(AppConstants.keyRefreshToken);

  static bool get isLoggedIn {
    final token = accessToken;
    if (token == null || token.isEmpty) return false;
    final expiryStr = _prefs.getString(AppConstants.keyTokenExpiry);
    if (expiryStr == null) return false;
    return DateTime.parse(expiryStr).isAfter(DateTime.now());
  }

  static Future<void> clearTokens() async {
    await Future.wait([
      _prefs.remove(AppConstants.keyAccessToken),
      _prefs.remove(AppConstants.keyRefreshToken),
      _prefs.remove(AppConstants.keyTokenExpiry),
    ]);
  }
}
