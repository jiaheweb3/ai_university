/// AetherVerse — 举报 / 用户 / 上传 API 服务
library;

import 'package:dio/dio.dart';

import 'api_client.dart';

// ============================================================
// 举报
// ============================================================

class ReportService {
  final ApiClient _api = ApiClient();

  /// 提交举报
  Future<void> submitReport({
    required String targetId,
    required String targetType,
    required String reason,
  }) async {
    final res = await _api.post(
      '/reports',
      data: {
        'target_id': targetId,
        'target_type': targetType,
        'reason': reason,
      },
    );
    if (!res.isSuccess) {
      throw ApiException(code: res.code, message: res.message);
    }
  }
}

// ============================================================
// 用户
// ============================================================

class UserService {
  final ApiClient _api = ApiClient();

  /// 获取当前用户信息
  Future<Map<String, dynamic>?> getMe() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/users/me',
      fromData: (d) => d as Map<String, dynamic>,
    );
    return res.isSuccess ? res.data : null;
  }

  /// 更新个人资料
  Future<void> updateProfile({
    String? nickname,
    String? avatarUrl,
    String? bio,
  }) async {
    await _api.patch('/users/me', data: {
      if (nickname != null) 'nickname': nickname,
      if (avatarUrl != null) 'avatar_url': avatarUrl,
      if (bio != null) 'bio': bio,
    });
  }

  /// 修改密码 (已登录)
  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    final res = await _api.put(
      '/users/me/password',
      data: {'old_password': oldPassword, 'new_password': newPassword},
    );
    if (!res.isSuccess) {
      throw ApiException(code: res.code, message: res.message);
    }
  }

  /// 注销账号
  Future<void> deleteAccount({required String code, String? reason}) async {
    await _api.post('/users/me/delete', data: {
      'code': code,
      if (reason != null) 'reason': reason,
    });
  }

  /// 获取设置
  Future<Map<String, dynamic>?> getSettings() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/users/me/settings',
      fromData: (d) => d as Map<String, dynamic>,
    );
    return res.isSuccess ? res.data : null;
  }

  /// 更新设置
  Future<void> updateSettings({
    bool? notificationEnabled,
    bool? privacyShowAgents,
  }) async {
    await _api.patch('/users/me/settings', data: {
      if (notificationEnabled != null) 'notification_enabled': notificationEnabled,
      if (privacyShowAgents != null) 'privacy_show_agents': privacyShowAgents,
    });
  }

  /// 查看用户主页
  Future<Map<String, dynamic>?> getUserProfile(String userId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/users/$userId',
      fromData: (d) => d as Map<String, dynamic>,
    );
    return res.isSuccess ? res.data : null;
  }

  /// 屏蔽用户/智能体
  Future<void> blockUser(String userId, {String blockedType = 'user'}) async {
    await _api.post('/users/$userId/block', data: {'blocked_type': blockedType});
  }

  /// 取消屏蔽
  Future<void> unblockUser(String userId) async {
    await _api.delete('/users/$userId/block');
  }
}

// ============================================================
// 文件上传
// ============================================================

class UploadService {
  final ApiClient _api = ApiClient();

  /// 上传图片 → 返回 { url, thumbnail_url }
  Future<Map<String, String>?> uploadImage(String filePath) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
    });
    final res = await _api.upload<Map<String, dynamic>>(
      '/uploads/image',
      formData: formData,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return {
        'url': res.data!['url'] as String? ?? '',
        'thumbnail_url': res.data!['thumbnail_url'] as String? ?? '',
      };
    }
    return null;
  }

  /// 上传头像
  Future<String?> uploadAvatar(String filePath) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
    });
    final res = await _api.upload<Map<String, dynamic>>(
      '/uploads/avatar',
      formData: formData,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return res.data!['url'] as String?;
    }
    return null;
  }
}
