/// AetherVerse — Provider 状态流转测试
library;

import 'package:flutter_test/flutter_test.dart';

import 'package:aetherverse_app/providers/room_provider.dart';
import 'package:aetherverse_app/providers/message_provider.dart';
import 'package:aetherverse_app/providers/agent_provider.dart';

import 'package:aetherverse_app/models/agent.dart';
import 'package:aetherverse_app/models/message.dart';
import 'package:aetherverse_app/models/point_notification.dart';

void main() {
  group('RoomListState', () {
    test('initial state has correct defaults', () {
      const state = RoomListState();
      expect(state.rooms, isEmpty);
      expect(state.isLoading, false);
      expect(state.hasMore, true);
      expect(state.nextCursor, isNull);
      expect(state.error, isNull);
      expect(state.sort, 'hot');
      expect(state.search, isNull);
    });

    test('copyWith preserves unchanged fields', () {
      const state = RoomListState(sort: 'new', category: 'tech');
      final updated = state.copyWith(isLoading: true);
      expect(updated.isLoading, true);
      expect(updated.sort, 'new');
      expect(updated.category, 'tech');
    });

    test('copyWith allows error to be set and cleared', () {
      const state = RoomListState();
      final withError = state.copyWith(error: '网络错误');
      expect(withError.error, '网络错误');

      // error 可被显式设为 null（copyWith 设计允许）
      final cleared = withError.copyWith(error: null);
      expect(cleared.error, isNull);
    });
  });

  group('Room model', () {
    test('fromJson parses all fields', () {
      final json = {
        'id': 'room-001',
        'name': 'AI讨论室',
        'description': '探讨AI技术发展趋势',
        'category': 'tech',
        'tags': ['AI', '科技', '讨论'],
        'cover_url': 'https://img.example.com/room.jpg',
        'status': 'active',
        'online_count': 15,
        'message_count': 230,
        'created_at': '2026-03-10T08:00:00Z',
      };
      final room = Room.fromJson(json);
      expect(room.name, 'AI讨论室');
      expect(room.tags, ['AI', '科技', '讨论']);
      expect(room.onlineCount, 15);
    });

    test('fromJson handles missing optional fields', () {
      final json = {
        'id': 'room-002',
        'name': '简单房间',
        'created_at': '2026-03-10T08:00:00Z',
      };
      final room = Room.fromJson(json);
      expect(room.description, isNull);
      expect(room.category, isNull);
      expect(room.tags, isEmpty);
      expect(room.coverUrl, isNull);
      expect(room.status, 'active');
      expect(room.onlineCount, 0);
    });
  });

  group('RoomMessageState', () {
    test('initial state', () {
      const state = RoomMessageState(roomId: 'room-001');
      expect(state.messages, isEmpty);
      expect(state.isLoading, false);
      expect(state.hasMore, true);
      expect(state.typingUsers, isEmpty);
    });

    test('copyWith updates messages only', () {
      const state = RoomMessageState(roomId: 'room-001');
      final msg = Message.fromJson({
        'id': 'msg-001',
        'sender': {'id': 'u1', 'type': 'user', 'nickname': 'A'},
        'msg_type': 'text',
        'content': 'Hi',
        'created_at': '2026-03-19T10:00:00Z',
      });
      final updated = state.copyWith(messages: [msg]);
      expect(updated.messages.length, 1);
      expect(updated.roomId, 'room-001');
      expect(updated.isLoading, false);
    });

    test('typing users can be added and removed', () {
      const state = RoomMessageState(roomId: 'room-001');
      final withTyping = state.copyWith(typingUsers: {'Alice', 'Bob'});
      expect(withTyping.typingUsers, {'Alice', 'Bob'});

      final removed = withTyping.copyWith(
        typingUsers: withTyping.typingUsers.where((n) => n != 'Alice').toSet(),
      );
      expect(removed.typingUsers, {'Bob'});
    });
  });

  group('ConversationListState', () {
    test('initial state', () {
      const state = ConversationListState();
      expect(state.conversations, isEmpty);
      expect(state.isLoading, false);
      expect(state.hasMore, true);
    });
  });

  group('AgentListState', () {
    test('initial state', () {
      const state = AgentListState();
      expect(state.agents, isEmpty);
      expect(state.isLoading, false);
      expect(state.error, isNull);
    });

    test('copyWith adds agents', () {
      final agent = Agent.fromJson({
        'id': 'agent-001',
        'owner_id': 'user-001',
        'owner_type': 'user',
        'name': '小智',
        'status': 'active',
        'created_at': '2026-03-19T08:00:00Z',
      });
      const state = AgentListState();
      final updated = state.copyWith(agents: [agent]);
      expect(updated.agents.length, 1);
      expect(updated.agents.first.name, '小智');
    });

    test('error can be set', () {
      const state = AgentListState();
      final withError = state.copyWith(isLoading: false, error: 'API Error');
      expect(withError.error, 'API Error');
      expect(withError.isLoading, false);
    });
  });

  group('PointsBalance computed properties', () {
    test('available = balance - frozen', () {
      final bal = PointsBalance(balance: 500, frozen: 30);
      expect(bal.available, 470);
    });

    test('zero balance', () {
      final bal = PointsBalance();
      expect(bal.available, 0);
    });
  });

  group('UnreadCount', () {
    test('defaults', () {
      final count = UnreadCount();
      expect(count.total, 0);
      expect(count.byType, isEmpty);
    });
  });
}
