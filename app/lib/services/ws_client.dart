/// AetherVerse — WebSocket 客户端
/// 对齐 docs/contracts/websocket-protocol.md
library;

import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../core/constants.dart';
import '../models/shared_types.dart';
import 'storage_service.dart';

/// WebSocket 事件
class WsMessage {
  final String event;
  final Map<String, dynamic>? data;
  final String? requestId;
  final String? timestamp;

  WsMessage({
    required this.event,
    this.data,
    this.requestId,
    this.timestamp,
  });

  factory WsMessage.fromJson(Map<String, dynamic> json) {
    return WsMessage(
      event: json['event'] as String,
      data: json['data'] as Map<String, dynamic>?,
      requestId: json['request_id'] as String?,
      timestamp: json['timestamp'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{'event': event};
    if (data != null) map['data'] = data;
    if (requestId != null) map['request_id'] = requestId;
    if (timestamp != null) map['timestamp'] = timestamp;
    return map;
  }
}

/// WebSocket 连接状态
enum WsConnectionState {
  disconnected,
  connecting,
  connected,
  reconnecting,
}

/// WebSocket 客户端 — 心跳/重连/事件分发 (单例)
class WsClient {
  static final WsClient _instance = WsClient._internal();
  static WsClient get instance => _instance;
  factory WsClient() => _instance;

  WsClient._internal();

  WebSocketChannel? _channel;
  Timer? _heartbeatTimer;
  Timer? _pongTimeoutTimer;
  Timer? _reconnectTimer;

  WsConnectionState _state = WsConnectionState.disconnected;
  int _reconnectAttempts = 0;

  /// 各房间最后已知消息 ID (用于 sync)
  final Map<String, String> _lastRoomMessageIds = {};
  final Map<String, String> _lastConvMessageIds = {};

  // --- 事件流 ---
  final StreamController<WsMessage> _eventController =
      StreamController<WsMessage>.broadcast();

  /// 所有事件的广播流
  Stream<WsMessage> get events => _eventController.stream;

  /// 按事件名过滤
  Stream<WsMessage> on(String eventName) =>
      events.where((msg) => msg.event == eventName);

  /// 连接状态流
  final StreamController<WsConnectionState> _stateController =
      StreamController<WsConnectionState>.broadcast();
  Stream<WsConnectionState> get stateStream => _stateController.stream;
  WsConnectionState get state => _state;

  // ============================================================
  // 连接
  // ============================================================

  /// 建立 WebSocket 连接
  Future<void> connect() async {
    if (_state == WsConnectionState.connected ||
        _state == WsConnectionState.connecting) {
      return;
    }

    final token = StorageService.accessToken;
    if (token == null || token.isEmpty) {
      debugPrint('[WS] 无 Token，取消连接');
      return;
    }

    _updateState(WsConnectionState.connecting);

    try {
      final uri = Uri.parse('${AppConstants.wsBaseUrl}?token=$token');
      _channel = WebSocketChannel.connect(uri);
      await _channel!.ready;
      
      _updateState(WsConnectionState.connected);
      _reconnectAttempts = 0;
      _startHeartbeat();

      // 监听消息
      _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );

      // 重连后同步
      if (_lastRoomMessageIds.isNotEmpty || _lastConvMessageIds.isNotEmpty) {
        _sendSync();
      }

      debugPrint('[WS] 已连接');
    } catch (e) {
      debugPrint('[WS] 连接失败: $e');
      _scheduleReconnect();
    }
  }

  /// 断开连接
  void disconnect() {
    _heartbeatTimer?.cancel();
    _pongTimeoutTimer?.cancel();
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    _updateState(WsConnectionState.disconnected);
    debugPrint('[WS] 已断开');
  }

  // ============================================================
  // 发送
  // ============================================================

  /// 发送事件
  void send(WsMessage message) {
    if (_state != WsConnectionState.connected) {
      debugPrint('[WS] 未连接，丢弃事件: ${message.event}');
      return;
    }
    final jsonStr = jsonEncode(message.toJson());
    _channel?.sink.add(jsonStr);
  }

  /// 加入房间
  void joinRoom(String roomId) {
    send(WsMessage(
      event: WsEvents.roomJoin,
      data: {'room_id': roomId},
    ));
  }

  /// 离开房间
  void leaveRoom(String roomId) {
    send(WsMessage(
      event: WsEvents.roomLeave,
      data: {'room_id': roomId},
    ));
  }

  /// 发送消息
  void sendMessage({
    required String roomId,
    required String msgType,
    String? content,
    String? imageUrl,
    String? replyToId,
    List<String>? mentions,
    required String requestId,
  }) {
    send(WsMessage(
      event: WsEvents.messageSend,
      data: {
        'room_id': roomId,
        'msg_type': msgType,
        if (content != null) 'content': content,
        if (imageUrl != null) 'image_url': imageUrl,
        if (replyToId != null) 'reply_to_id': replyToId,
        if (mentions != null && mentions.isNotEmpty) 'mentions': mentions,
      },
      requestId: requestId,
    ));
  }

  /// 发送私聊消息
  void sendPrivateMessage({
    required String conversationId,
    required String msgType,
    String? content,
    String? imageUrl,
    required String requestId,
  }) {
    send(WsMessage(
      event: WsEvents.messageSendPrivate,
      data: {
        'conversation_id': conversationId,
        'msg_type': msgType,
        if (content != null) 'content': content,
        if (imageUrl != null) 'image_url': imageUrl,
      },
      requestId: requestId,
    ));
  }

  /// 发送输入状态
  void sendTyping(String roomId, bool isTyping) {
    send(WsMessage(
      event: isTyping ? WsEvents.typingStart : WsEvents.typingStop,
      data: {'room_id': roomId},
    ));
  }

  /// 记录最后消息 ID (用于断连重连后 sync)
  void trackLastMessage(String roomId, String messageId,
      {bool isConversation = false}) {
    if (isConversation) {
      _lastConvMessageIds[roomId] = messageId;
    } else {
      _lastRoomMessageIds[roomId] = messageId;
    }
  }

  // ============================================================
  // 内部方法
  // ============================================================

  void _onMessage(dynamic raw) {
    try {
      final json = jsonDecode(raw as String) as Map<String, dynamic>;
      final message = WsMessage.fromJson(json);

      // pong 处理
      if (message.event == WsEvents.pong) {
        _pongTimeoutTimer?.cancel();
        return;
      }

      // fatal error → 断开
      if (message.event == WsEvents.error) {
        final isFatal = message.data?['fatal'] as bool? ?? false;
        if (isFatal) {
          debugPrint('[WS] Fatal error: ${message.data?['message']}');
          disconnect();
          return;
        }
      }

      // 分发事件
      _eventController.add(message);
    } catch (e) {
      debugPrint('[WS] 解析消息失败: $e');
    }
  }

  void _onError(Object error) {
    debugPrint('[WS] 错误: $error');
    _scheduleReconnect();
  }

  void _onDone() {
    debugPrint('[WS] 连接关闭');
    _heartbeatTimer?.cancel();
    _pongTimeoutTimer?.cancel();
    if (_state != WsConnectionState.disconnected) {
      _scheduleReconnect();
    }
  }

  // --- 心跳 ---
  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(
      AppConstants.heartbeatInterval,
      (_) {
        send(WsMessage(event: WsEvents.ping));
        // 60s 未收到 pong → 重连
        _pongTimeoutTimer?.cancel();
        _pongTimeoutTimer = Timer(AppConstants.heartbeatTimeout, () {
          debugPrint('[WS] Pong 超时，触发重连');
          _channel?.sink.close();
        });
      },
    );
  }

  // --- 断线重连 (指数退避) ---
  void _scheduleReconnect() {
    _heartbeatTimer?.cancel();
    _pongTimeoutTimer?.cancel();
    _channel = null;

    _updateState(WsConnectionState.reconnecting);

    final delay = Duration(
      milliseconds: min(
        AppConstants.reconnectMinDelay.inMilliseconds *
            pow(2, _reconnectAttempts).toInt(),
        AppConstants.reconnectMaxDelay.inMilliseconds,
      ),
    );

    debugPrint('[WS] ${delay.inSeconds}s 后重连 (第${_reconnectAttempts + 1}次)');

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () {
      _reconnectAttempts++;
      connect();
    });
  }

  // --- sync 事件 ---
  void _sendSync() {
    send(WsMessage(
      event: WsEvents.sync,
      data: {
        'rooms': _lastRoomMessageIds,
        'conversations': _lastConvMessageIds,
      },
    ));
  }

  void _updateState(WsConnectionState newState) {
    _state = newState;
    _stateController.add(newState);
  }

  /// 释放资源
  void dispose() {
    disconnect();
    _eventController.close();
    _stateController.close();
  }
}
