/// AetherVerse — 模型序列化/反序列化测试
library;

import 'package:flutter_test/flutter_test.dart';

import 'package:aetherverse_app/models/message.dart';
import 'package:aetherverse_app/models/agent.dart';
import 'package:aetherverse_app/models/topic.dart';
import 'package:aetherverse_app/models/point_notification.dart';

void main() {
  group('Message models', () {
    test('MessageSender.fromJson parses correctly', () {
      final json = {
        'id': 'sender-001',
        'type': 'user',
        'nickname': 'TestUser',
        'avatar_url': 'https://img.example.com/a.png',
        'is_ai': false,
        'owner_nickname': null,
      };
      final sender = MessageSender.fromJson(json);
      expect(sender.id, 'sender-001');
      expect(sender.type, 'user');
      expect(sender.nickname, 'TestUser');
      expect(sender.avatarUrl, 'https://img.example.com/a.png');
      expect(sender.isAi, false);
      expect(sender.ownerNickname, isNull);
    });

    test('MessageSender.fromJson handles AI agent', () {
      final json = {
        'id': 'agent-001',
        'type': 'agent',
        'nickname': '小智',
        'is_ai': true,
        'owner_nickname': 'Creator',
      };
      final sender = MessageSender.fromJson(json);
      expect(sender.isAi, true);
      expect(sender.ownerNickname, 'Creator');
    });

    test('Message.fromJson parses text message', () {
      final json = {
        'id': 'msg-001',
        'room_id': 'room-001',
        'sender': {
          'id': 'user-001',
          'type': 'user',
          'nickname': 'Alice',
        },
        'msg_type': 'text',
        'content': 'Hello World',
        'mentions': ['user-002'],
        'is_ai_generated': false,
        'created_at': '2026-03-19T10:00:00Z',
      };
      final msg = Message.fromJson(json);
      expect(msg.id, 'msg-001');
      expect(msg.roomId, 'room-001');
      expect(msg.isText, true);
      expect(msg.isImage, false);
      expect(msg.isSystem, false);
      expect(msg.content, 'Hello World');
      expect(msg.mentions, ['user-002']);
      expect(msg.sender.nickname, 'Alice');
    });

    test('Message.fromJson parses image message', () {
      final json = {
        'id': 'msg-002',
        'room_id': 'room-001',
        'sender': {'id': 'user-001', 'type': 'user', 'nickname': 'Bob'},
        'msg_type': 'image',
        'image_url': 'https://img.example.com/pic.jpg',
        'created_at': '2026-03-19T10:01:00Z',
      };
      final msg = Message.fromJson(json);
      expect(msg.isImage, true);
      expect(msg.imageUrl, 'https://img.example.com/pic.jpg');
      expect(msg.content, isNull);
    });

    test('Message.fromJson handles reply_to and conversation', () {
      final json = {
        'id': 'msg-003',
        'conversation_id': 'conv-001',
        'sender': {'id': 'user-001', 'type': 'user', 'nickname': 'Eve'},
        'msg_type': 'text',
        'content': 'Reply here',
        'reply_to_id': 'msg-001',
        'created_at': '2026-03-19T10:02:00Z',
      };
      final msg = Message.fromJson(json);
      expect(msg.conversationId, 'conv-001');
      expect(msg.replyToId, 'msg-001');
      expect(msg.roomId, isNull);
    });

    test('Conversation.fromJson parses correctly', () {
      final json = {
        'id': 'conv-001',
        'conv_type': 'user_to_agent',
        'participant': {
          'id': 'agent-001',
          'nickname': 'AI助手',
          'avatar_url': 'https://img.example.com/ai.png',
        },
        'unread_count': 5,
        'updated_at': '2026-03-19T12:00:00Z',
      };
      final conv = Conversation.fromJson(json);
      expect(conv.convType, 'user_to_agent');
      expect(conv.participant.nickname, 'AI助手');
      expect(conv.unreadCount, 5);
      expect(conv.lastMessage, isNull);
    });

    test('Conversation.fromJson with last_message', () {
      final json = {
        'id': 'conv-002',
        'conv_type': 'user_to_user',
        'participant': {'id': 'user-002', 'nickname': 'Charlie'},
        'last_message': {
          'id': 'msg-100',
          'sender': {'id': 'user-002', 'type': 'user', 'nickname': 'Charlie'},
          'msg_type': 'text',
          'content': 'Hi there!',
          'created_at': '2026-03-19T11:00:00Z',
        },
        'unread_count': 1,
        'updated_at': '2026-03-19T11:00:00Z',
      };
      final conv = Conversation.fromJson(json);
      expect(conv.lastMessage, isNotNull);
      expect(conv.lastMessage!.content, 'Hi there!');
    });
  });

  group('Agent models', () {
    test('PersonaConfig roundtrip', () {
      final config = PersonaConfig(
        personality: '温和友善',
        speakingStyle: '日式敬语',
        expertise: 'AI技术',
        constraints: '不讨论政治',
      );
      final json = config.toJson();
      expect(json['personality'], '温和友善');
      expect(json['speaking_style'], '日式敬语');

      final restored = PersonaConfig.fromJson(json);
      expect(restored.personality, '温和友善');
      expect(restored.speakingStyle, '日式敬语');
      expect(restored.expertise, 'AI技术');
      expect(restored.constraints, '不讨论政治');
    });

    test('PersonaConfig.toJson omits null fields', () {
      final config = PersonaConfig(personality: '活泼');
      final json = config.toJson();
      expect(json.containsKey('personality'), true);
      expect(json.containsKey('speaking_style'), false);
    });

    test('Agent.fromJson parses correctly', () {
      final json = {
        'id': 'agent-001',
        'owner_id': 'user-001',
        'owner_type': 'user',
        'name': '小明',
        'avatar_url': 'https://img.example.com/agent.png',
        'bio': '我是一个AI助手',
        'level': 'L1',
        'status': 'active',
        'persona_config': {
          'personality': '热情开朗',
          'speaking_style': '口语化',
        },
        'current_room_id': 'room-001',
        'is_speaking': true,
        'created_at': '2026-03-19T08:00:00Z',
      };
      final agent = Agent.fromJson(json);
      expect(agent.name, '小明');
      expect(agent.isActive, true);
      expect(agent.isPaused, false);
      expect(agent.isInRoom, true);
      expect(agent.isSpeaking, true);
      expect(agent.personaConfig?.personality, '热情开朗');
    });

    test('Agent status helpers', () {
      final json = {
        'id': 'agent-002',
        'owner_id': 'user-001',
        'owner_type': 'user',
        'name': '小红',
        'status': 'paused',
        'created_at': '2026-03-19T08:00:00Z',
      };
      final agent = Agent.fromJson(json);
      expect(agent.isActive, false);
      expect(agent.isPaused, true);
      expect(agent.isInRoom, false);
    });

    test('AgentMemory.fromJson', () {
      final json = {
        'id': 'mem-001',
        'content': '用户喜欢科幻小说',
        'is_summary': true,
        'created_at': '2026-03-19T10:00:00Z',
        'expires_at': '2026-04-19T10:00:00Z',
      };
      final mem = AgentMemory.fromJson(json);
      expect(mem.content, '用户喜欢科幻小说');
      expect(mem.isSummary, true);
      expect(mem.expiresAt, isNotNull);
    });

    test('PersonaTemplate.fromJson', () {
      final json = {
        'id': 'tmpl-001',
        'name': '科技达人',
        'description': '擅长讨论AI和科技话题',
        'persona_config': {
          'personality': '理性冷静',
          'expertise': 'AI/ML',
        },
      };
      final tmpl = PersonaTemplate.fromJson(json);
      expect(tmpl.name, '科技达人');
      expect(tmpl.personaConfig?.expertise, 'AI/ML');
    });
  });

  group('Topic models', () {
    test('TopicBrief.fromJson', () {
      final json = {
        'id': 'topic-001',
        'title': 'AI绘画挑战',
        'status': 'active',
        'deadline': '2026-04-01T00:00:00Z',
      };
      final topic = TopicBrief.fromJson(json);
      expect(topic.title, 'AI绘画挑战');
      expect(topic.isActive, true);
      expect(topic.isEnded, false);
      expect(topic.deadline, isNotNull);
    });

    test('Topic.fromJson extends TopicBrief', () {
      final json = {
        'id': 'topic-002',
        'title': '赛博朋克创作',
        'status': 'ended',
        'description': '创作赛博朋克风格的图像',
        'keywords': ['赛博朋克', 'AI', '科幻'],
        'reference_url': 'https://example.com/ref',
        'participant_count': 42,
        'artwork_count': 120,
        'created_at': '2026-03-01T00:00:00Z',
      };
      final topic = Topic.fromJson(json);
      expect(topic.isEnded, true);
      expect(topic.keywords, ['赛博朋克', 'AI', '科幻']);
      expect(topic.participantCount, 42);
      expect(topic.artworkCount, 120);
    });

    test('Artwork.fromJson', () {
      final json = {
        'id': 'art-001',
        'topic_id': 'topic-001',
        'image_url': 'https://img.example.com/art.png',
        'thumbnail_url': 'https://img.example.com/art_thumb.png',
        'status': 'approved',
        'points_cost': 10,
        'created_at': '2026-03-19T14:00:00Z',
      };
      final art = Artwork.fromJson(json);
      expect(art.isApproved, true);
      expect(art.isGenerating, false);
      expect(art.pointsCost, 10);
    });
  });

  group('Point & Notification models', () {
    test('PointsBalance.fromJson', () {
      final json = {
        'balance': 1000,
        'frozen': 50,
        'free_chat_remaining': 3,
        'free_image_remaining': 1,
      };
      final bal = PointsBalance.fromJson(json);
      expect(bal.balance, 1000);
      expect(bal.frozen, 50);
      expect(bal.available, 950);
      expect(bal.freeChatRemaining, 3);
    });

    test('PointsBalance defaults', () {
      final bal = PointsBalance.fromJson({});
      expect(bal.balance, 0);
      expect(bal.frozen, 0);
      expect(bal.available, 0);
    });

    test('PointTransaction.fromJson', () {
      final json = {
        'id': 'tx-001',
        'tx_type': 'chat_deduction',
        'status': 'confirmed',
        'amount': -5,
        'balance_after': 995,
        'description': 'AI聊天消耗',
        'created_at': '2026-03-19T12:00:00Z',
      };
      final tx = PointTransaction.fromJson(json);
      expect(tx.txType, 'chat_deduction');
      expect(tx.amount, -5);
      expect(tx.isIncome, false);
      expect(tx.balanceAfter, 995);
    });

    test('PointTransaction income detection', () {
      final json = {
        'id': 'tx-002',
        'tx_type': 'recharge',
        'amount': 100,
        'balance_after': 1100,
        'created_at': '2026-03-19T12:01:00Z',
      };
      final tx = PointTransaction.fromJson(json);
      expect(tx.isIncome, true);
    });

    test('RechargePackage.fromJson', () {
      final json = {
        'id': 'pkg-001',
        'amount_yuan': 6.0,
        'points': 60,
        'bonus_points': 10,
      };
      final pkg = RechargePackage.fromJson(json);
      expect(pkg.amountYuan, 6.0);
      expect(pkg.points, 60);
      expect(pkg.totalPoints, 70);
    });

    test('AppNotification.fromJson', () {
      final json = {
        'id': 'notif-001',
        'ntype': 'moderation_result',
        'title': '审核通过',
        'content': '你的消息已通过审核',
        'is_read': false,
        'created_at': '2026-03-19T13:00:00Z',
      };
      final notif = AppNotification.fromJson(json);
      expect(notif.ntype, 'moderation_result');
      expect(notif.isRead, false);
    });

    test('UnreadCount.fromJson', () {
      final json = {
        'total': 7,
        'by_type': {
          'moderation_result': 2,
          'agent_status': 5,
        },
      };
      final count = UnreadCount.fromJson(json);
      expect(count.total, 7);
      expect(count.byType['agent_status'], 5);
    });

    test('UnreadCount defaults', () {
      final count = UnreadCount.fromJson({});
      expect(count.total, 0);
      expect(count.byType, isEmpty);
    });
  });
}
