/// AetherVerse — WebSocket 客户端单元测试
library;

import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';

import 'package:aetherverse_app/services/ws_client.dart';

void main() {
  group('WsMessage', () {
    test('fromJson parses all fields', () {
      final json = {
        'event': 'message:new',
        'data': {'room_id': 'room-001', 'content': 'Hello'},
        'request_id': 'req-001',
        'timestamp': '2026-03-19T10:00:00Z',
      };
      final msg = WsMessage.fromJson(json);
      expect(msg.event, 'message:new');
      expect(msg.data?['room_id'], 'room-001');
      expect(msg.requestId, 'req-001');
      expect(msg.timestamp, '2026-03-19T10:00:00Z');
    });

    test('fromJson with minimal fields', () {
      final json = {'event': 'pong'};
      final msg = WsMessage.fromJson(json);
      expect(msg.event, 'pong');
      expect(msg.data, isNull);
      expect(msg.requestId, isNull);
    });

    test('toJson includes only non-null fields', () {
      final msg = WsMessage(event: 'ping');
      final json = msg.toJson();
      expect(json, {'event': 'ping'});
      expect(json.containsKey('data'), false);
      expect(json.containsKey('request_id'), false);
    });

    test('toJson includes all fields when present', () {
      final msg = WsMessage(
        event: 'message:send',
        data: {'room_id': 'r1', 'content': 'Hi'},
        requestId: 'req-123',
        timestamp: '2026-03-19T10:00:00Z',
      );
      final json = msg.toJson();
      expect(json['event'], 'message:send');
      expect(json['data'], isNotNull);
      expect(json['request_id'], 'req-123');
      expect(json['timestamp'], '2026-03-19T10:00:00Z');
    });

    test('roundtrip toJson -> fromJson', () {
      final original = WsMessage(
        event: 'room:join',
        data: {'room_id': 'room-test'},
        requestId: 'abc',
      );
      final jsonStr = jsonEncode(original.toJson());
      final restored = WsMessage.fromJson(
        jsonDecode(jsonStr) as Map<String, dynamic>,
      );
      expect(restored.event, original.event);
      expect(restored.data?['room_id'], 'room-test');
      expect(restored.requestId, 'abc');
    });
  });

  group('WsConnectionState', () {
    test('has all expected values', () {
      expect(WsConnectionState.values.length, 4);
      expect(WsConnectionState.values, contains(WsConnectionState.disconnected));
      expect(WsConnectionState.values, contains(WsConnectionState.connecting));
      expect(WsConnectionState.values, contains(WsConnectionState.connected));
      expect(WsConnectionState.values, contains(WsConnectionState.reconnecting));
    });
  });

  group('WsClient singleton', () {
    test('factory returns same instance', () {
      final a = WsClient();
      final b = WsClient();
      expect(identical(a, b), true);
    });

    test('instance getter returns same object', () {
      expect(identical(WsClient.instance, WsClient()), true);
    });

    test('initial state is disconnected', () {
      expect(WsClient.instance.state, WsConnectionState.disconnected);
    });

    test('events stream is broadcast', () {
      final client = WsClient.instance;
      final sub1 = client.events.listen((_) {});
      final sub2 = client.events.listen((_) {});
      sub1.cancel();
      sub2.cancel();
    });

    test('on() returns filtered stream', () {
      final client = WsClient.instance;
      final sub = client.on('test:event').listen((_) {});
      sub.cancel();
    });
  });
}
