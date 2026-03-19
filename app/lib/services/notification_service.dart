/// AetherVerse — 通知 API 服务
library;

import '../models/point_notification.dart';
import 'api_client.dart';

class NotificationService {
  final ApiClient _api = ApiClient();

  /// 通知列表
  Future<List<AppNotification>> getNotifications({
    String? ntype,
    bool? isRead,
    String? after,
    int limit = 20,
  }) async {
    final params = <String, dynamic>{
      'limit': limit,
      if (ntype != null) 'ntype': ntype,
      if (isRead != null) 'is_read': isRead,
      if (after != null) 'after': after,
    };
    final res = await _api.get<Map<String, dynamic>>(
      '/notifications',
      queryParameters: params,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items
          .map((e) => AppNotification.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// 未读计数
  Future<UnreadCount> getUnreadCount() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/notifications/unread-count',
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return UnreadCount.fromJson(res.data!);
    }
    return UnreadCount();
  }

  /// 批量标记已读
  Future<void> markRead({List<String>? notificationIds, bool readAll = false}) async {
    await _api.post('/notifications/read', data: {
      if (notificationIds != null) 'notification_ids': notificationIds,
      'read_all': readAll,
    });
  }
}
