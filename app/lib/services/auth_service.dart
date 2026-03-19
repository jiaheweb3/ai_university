/// AetherVerse — 认证 API 服务
library;

import '../models/shared_types.dart';
import 'api_client.dart';
import 'storage_service.dart';

class AuthService {
  final ApiClient _api = ApiClient();

  /// 发送短信验证码
  Future<void> sendSmsCode(String phone, {String purpose = 'login'}) async {
    final res = await _api.post('/auth/sms/send', data: {
      'phone': phone,
      'purpose': purpose,
    });
    if (!res.isSuccess) throw ApiException(code: res.code, message: res.message);
  }

  /// 手机号注册
  Future<UserProfile> register({
    required String phone,
    required String code,
    required String password,
    required String nickname,
  }) async {
    final res = await _api.post<Map<String, dynamic>>(
      '/auth/register',
      data: {
        'phone': phone,
        'code': code,
        'password': password,
        'nickname': nickname,
      },
      fromData: (d) => d as Map<String, dynamic>,
    );

    if (!res.isSuccess || res.data == null) {
      throw ApiException(code: res.code, message: res.message);
    }

    await _saveAuthData(res.data!);
    return UserProfile.fromJson(res.data!['user'] as Map<String, dynamic>);
  }

  /// 密码登录
  Future<UserProfile> loginByPassword({
    required String phone,
    required String password,
  }) async {
    final res = await _api.post<Map<String, dynamic>>(
      '/auth/login/password',
      data: {'phone': phone, 'password': password},
      fromData: (d) => d as Map<String, dynamic>,
    );

    if (!res.isSuccess || res.data == null) {
      throw ApiException(code: res.code, message: res.message);
    }

    await _saveAuthData(res.data!);
    return UserProfile.fromJson(res.data!['user'] as Map<String, dynamic>);
  }

  /// 验证码登录
  Future<UserProfile> loginBySms({
    required String phone,
    required String code,
  }) async {
    final res = await _api.post<Map<String, dynamic>>(
      '/auth/login/sms',
      data: {'phone': phone, 'code': code},
      fromData: (d) => d as Map<String, dynamic>,
    );

    if (!res.isSuccess || res.data == null) {
      throw ApiException(code: res.code, message: res.message);
    }

    await _saveAuthData(res.data!);
    return UserProfile.fromJson(res.data!['user'] as Map<String, dynamic>);
  }

  /// 重置密码
  Future<void> resetPassword({
    required String phone,
    required String code,
    required String newPassword,
  }) async {
    final res = await _api.post('/auth/password/reset', data: {
      'phone': phone,
      'code': code,
      'new_password': newPassword,
    });
    if (!res.isSuccess) throw ApiException(code: res.code, message: res.message);
  }

  /// 退出登录
  Future<void> logout() async {
    try {
      await _api.post('/auth/logout');
    } finally {
      await StorageService.clearTokens();
    }
  }

  /// 获取当前用户信息
  Future<UserProfile> getCurrentUser() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/users/me',
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (!res.isSuccess || res.data == null) {
      throw ApiException(code: res.code, message: res.message);
    }
    return UserProfile.fromJson(res.data!);
  }

  // --- 内部 ---
  Future<void> _saveAuthData(Map<String, dynamic> data) async {
    await StorageService.saveTokens(
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
      expiresIn: data['expires_in'] as int,
    );
  }
}
