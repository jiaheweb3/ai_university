/// AetherVerse — 消息状态管理 (房间 + 私聊)
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../models/message.dart';
import '../models/shared_types.dart';
import '../services/message_service.dart';
import '../services/ws_client.dart';

const _uuid = Uuid();

// ============================================================
// 房间消息
// ============================================================

/// 房间消息状态
class RoomMessageState {
  final String roomId;
  final List<Message> messages;
  final bool isLoading;
  final bool hasMore;
  final String? oldestMessageId;
  final Set<String> typingUsers; // 正在输入的用户 昵称

  const RoomMessageState({
    required this.roomId,
    this.messages = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.oldestMessageId,
    this.typingUsers = const {},
  });

  RoomMessageState copyWith({
    List<Message>? messages,
    bool? isLoading,
    bool? hasMore,
    String? oldestMessageId,
    Set<String>? typingUsers,
  }) {
    return RoomMessageState(
      roomId: roomId,
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      oldestMessageId: oldestMessageId ?? this.oldestMessageId,
      typingUsers: typingUsers ?? this.typingUsers,
    );
  }
}

/// 房间消息 Provider (按 roomId 维度)
final roomMessageProvider = StateNotifierProvider.family<
    RoomMessageNotifier, RoomMessageState, String>(
  (ref, roomId) => RoomMessageNotifier(roomId),
);

class RoomMessageNotifier extends StateNotifier<RoomMessageState> {
  RoomMessageNotifier(String roomId) : super(RoomMessageState(roomId: roomId));

  final MessageService _messageService = MessageService();
  final WsClient _ws = WsClient.instance;
  StreamSubscription<WsMessage>? _wsSub;

  /// 初始化: 加载历史 + 订阅 WS 事件
  Future<void> init() async {
    await loadMessages();
    _subscribeWsEvents();
  }

  /// 加载历史消息
  Future<void> loadMessages() async {
    if (state.isLoading) return;
    state = state.copyWith(isLoading: true);

    final messages = await _messageService.getRoomMessages(
      state.roomId,
      before: state.oldestMessageId,
    );

    state = state.copyWith(
      messages: [...state.messages, ...messages],
      isLoading: false,
      hasMore: messages.length >= 50,
      oldestMessageId: messages.isNotEmpty ? messages.last.id : state.oldestMessageId,
    );

    // 跟踪最新消息 ID
    if (state.messages.isNotEmpty) {
      _ws.trackLastMessage(state.roomId, state.messages.first.id);
    }
  }

  /// 通过 WS 发送消息 (优先)
  void sendTextMessage(String content, {String? replyToId, List<String>? mentions}) {
    final requestId = _uuid.v4();
    _ws.sendMessage(
      roomId: state.roomId,
      msgType: 'text',
      content: content,
      replyToId: replyToId,
      mentions: mentions,
      requestId: requestId,
    );
  }

  /// 发送图片消息
  void sendImageMessage(String imageUrl) {
    final requestId = _uuid.v4();
    _ws.sendMessage(
      roomId: state.roomId,
      msgType: 'image',
      imageUrl: imageUrl,
      requestId: requestId,
    );
  }

  /// 发送输入状态
  void setTyping(bool isTyping) {
    _ws.sendTyping(state.roomId, isTyping);
  }

  /// 订阅 WS 事件
  void _subscribeWsEvents() {
    _wsSub = _ws.events.listen((msg) {
      switch (msg.event) {
        case WsEvents.messageNew:
          _onNewMessage(msg);
        case WsEvents.typingStart:
          _onTypingStart(msg);
        case WsEvents.typingStop:
          _onTypingStop(msg);
      }
    });
  }

  void _onNewMessage(WsMessage wsMsg) {
    if (wsMsg.data == null) return;
    final msgRoomId = wsMsg.data!['room_id'] as String?;
    if (msgRoomId != state.roomId) return;

    final message = Message.fromJson(wsMsg.data!);
    // 去重
    if (state.messages.any((m) => m.id == message.id)) return;

    state = state.copyWith(
      messages: [message, ...state.messages],
    );
    _ws.trackLastMessage(state.roomId, message.id);
  }

  void _onTypingStart(WsMessage wsMsg) {
    final nick = wsMsg.data?['nickname'] as String?;
    final roomId = wsMsg.data?['room_id'] as String?;
    if (nick != null && roomId == state.roomId) {
      state = state.copyWith(typingUsers: {...state.typingUsers, nick});
    }
  }

  void _onTypingStop(WsMessage wsMsg) {
    final nick = wsMsg.data?['nickname'] as String?;
    final roomId = wsMsg.data?['room_id'] as String?;
    if (nick != null && roomId == state.roomId) {
      state = state.copyWith(
        typingUsers: state.typingUsers.where((n) => n != nick).toSet(),
      );
    }
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    super.dispose();
  }
}

// ============================================================
// 私聊会话列表
// ============================================================

/// 私聊列表状态
class ConversationListState {
  final List<Conversation> conversations;
  final bool isLoading;
  final bool hasMore;
  final String? nextCursor;

  const ConversationListState({
    this.conversations = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.nextCursor,
  });

  ConversationListState copyWith({
    List<Conversation>? conversations,
    bool? isLoading,
    bool? hasMore,
    String? nextCursor,
  }) {
    return ConversationListState(
      conversations: conversations ?? this.conversations,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      nextCursor: nextCursor ?? this.nextCursor,
    );
  }
}

final conversationListProvider =
    StateNotifierProvider<ConversationListNotifier, ConversationListState>(
  (ref) => ConversationListNotifier(),
);

class ConversationListNotifier extends StateNotifier<ConversationListState> {
  ConversationListNotifier() : super(const ConversationListState());

  final MessageService _service = MessageService();

  /// 加载会话列表
  Future<void> load() async {
    state = state.copyWith(isLoading: true);
    final list = await _service.getConversations();
    state = state.copyWith(
      conversations: list,
      isLoading: false,
      hasMore: list.length >= 20,
    );
  }

  /// 发起新的私聊
  Future<String?> startConversation({
    required String targetId,
    required String targetType,
  }) async {
    return _service.startConversation(
      targetId: targetId,
      targetType: targetType,
    );
  }
}
