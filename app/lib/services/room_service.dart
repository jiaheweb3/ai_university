/// AetherVerse — 房间 API 服务 (补充 room_provider 缺少的 REST 调用)
library;

import 'api_client.dart';

class RoomService {
  final ApiClient _api = ApiClient();

  /// 房间详情
  Future<Map<String, dynamic>?> getRoomDetail(String roomId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/rooms/$roomId',
      fromData: (d) => d as Map<String, dynamic>,
    );
    return res.isSuccess ? res.data : null;
  }

  /// 加入房间
  Future<void> joinRoom(String roomId) async {
    await _api.post('/rooms/$roomId/join');
  }

  /// 离开房间
  Future<void> leaveRoom(String roomId) async {
    await _api.post('/rooms/$roomId/leave');
  }

  /// 房间成员列表
  Future<List<Map<String, dynamic>>> getMembers(String roomId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/rooms/$roomId/members',
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items.cast<Map<String, dynamic>>();
    }
    return [];
  }
}
