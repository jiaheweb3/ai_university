/// AetherVerse — 消息 API 服务
library;

import '../models/message.dart';
import 'api_client.dart';

class MessageService {
  final ApiClient _api = ApiClient();

  // ============================================================
  // 房间消息
  // ============================================================

  /// 获取房间历史消息 (before = 某条消息之前)
  Future<List<Message>> getRoomMessages(
    String roomId, {
    String? before,
    int limit = 50,
  }) async {
    final params = <String, dynamic>{
      'limit': limit,
      if (before != null) 'before': before,
    };
    final res = await _api.get<Map<String, dynamic>>(
      '/rooms/$roomId/messages',
      queryParameters: params,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items
          .map((e) => Message.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// 通过 REST 发送房间消息 (WS 不可用时的 fallback)
  Future<Message?> sendRoomMessage(
    String roomId, {
    required String msgType,
    String? content,
    String? imageUrl,
    String? replyToId,
    List<String>? mentions,
    String? requestId,
  }) async {
    final res = await _api.post<Map<String, dynamic>>(
      '/rooms/$roomId/messages',
      data: {
        'msg_type': msgType,
        if (content != null) 'content': content,
        if (imageUrl != null) 'image_url': imageUrl,
        if (replyToId != null) 'reply_to_id': replyToId,
        if (mentions != null && mentions.isNotEmpty) 'mentions': mentions,
        if (requestId != null) 'request_id': requestId,
      },
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return Message.fromJson(res.data!);
    }
    return null;
  }

  // ============================================================
  // 私聊
  // ============================================================

  /// 获取私聊会话列表
  Future<List<Conversation>> getConversations({
    String? after,
    int limit = 20,
  }) async {
    final params = <String, dynamic>{
      'limit': limit,
      if (after != null) 'after': after,
    };
    final res = await _api.get<Map<String, dynamic>>(
      '/conversations',
      queryParameters: params,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items
          .map((e) => Conversation.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// 获取私聊历史消息
  Future<List<Message>> getConversationMessages(
    String convId, {
    String? before,
    int limit = 50,
  }) async {
    final params = <String, dynamic>{
      'limit': limit,
      if (before != null) 'before': before,
    };
    final res = await _api.get<Map<String, dynamic>>(
      '/conversations/$convId/messages',
      queryParameters: params,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items
          .map((e) => Message.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// 发起私聊 (已存在则返回已有会话)
  Future<String?> startConversation({
    required String targetId,
    required String targetType,
  }) async {
    final res = await _api.post<Map<String, dynamic>>(
      '/conversations/start',
      data: {
        'target_id': targetId,
        'target_type': targetType,
      },
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return res.data!['id'] as String?;
    }
    return null;
  }

  /// REST 发送私聊消息
  Future<Message?> sendConversationMessage(
    String convId, {
    required String msgType,
    String? content,
    String? imageUrl,
    String? requestId,
  }) async {
    final res = await _api.post<Map<String, dynamic>>(
      '/conversations/$convId/messages',
      data: {
        'msg_type': msgType,
        if (content != null) 'content': content,
        if (imageUrl != null) 'image_url': imageUrl,
        if (requestId != null) 'request_id': requestId,
      },
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return Message.fromJson(res.data!);
    }
    return null;
  }

  /// 标记已读
  Future<void> markConversationRead(String convId) async {
    await _api.post('/conversations/$convId/read');
  }
}
