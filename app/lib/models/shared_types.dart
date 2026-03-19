/// AetherVerse — Flutter 共享类型定义
/// 从 db-schema.sql 和 api-schema.yaml 生成
/// Agent C (Apollo) 引用此文件
/// 
/// 文件位置: docs/contracts/shared-types.dart
/// 注意: 这是契约文件 (只读), Flutter 项目中应 import 或复制使用

// ============================================================
// 枚举 (对应 PostgreSQL ENUM)
// ============================================================

enum UserStatus { active, bannedTemp, bannedPerm, deleted }

enum RoomStatus { active, archived }

enum RoomMemberRole { member, moderator, admin }

enum RoomMemberType { user, agent }

enum MessageType { text, image, system, aiGenerated }

enum ModerationStatus { pending, approved, rejected, appealed }

enum AgentOwnerType { user, system }

enum AgentLevel { l1, l2 }

enum AgentStatus { active, paused, suspended }

enum TopicStatus { draft, active, ended, archived }

enum ArtworkStatus { generating, pendingReview, approved, rejected, failed }

enum PointTxType { recharge, dailyFree, chatCost, imageCost, agentCreate, adminAdjust, refund }

enum PointTxStatus { frozen, confirmed, refunded }

enum NotificationType { moderationResult, agentStatus, accountSecurity, taskStatus, transaction }

enum ConversationType { userToUser, userToAgent }


// ============================================================
// API 响应模型
// ============================================================

class ApiResponse<T> {
  final int code;
  final String message;
  final T? data;

  ApiResponse({required this.code, required this.message, this.data});

  bool get isSuccess => code == 0;

  factory ApiResponse.fromJson(Map<String, dynamic> json, T Function(dynamic)? fromData) {
    return ApiResponse(
      code: json['code'] as int,
      message: json['message'] as String,
      data: json['data'] != null && fromData != null ? fromData(json['data']) : null,
    );
  }
}

class PaginatedData<T> {
  final List<T> items;
  final String? nextCursor;
  final bool hasMore;

  PaginatedData({required this.items, this.nextCursor, required this.hasMore});
}


// ============================================================
// 用户
// ============================================================

class UserProfileBrief {
  final String id;
  final String nickname;
  final String? avatarUrl;

  UserProfileBrief({required this.id, required this.nickname, this.avatarUrl});

  factory UserProfileBrief.fromJson(Map<String, dynamic> json) {
    return UserProfileBrief(
      id: json['id'] as String,
      nickname: json['nickname'] as String,
      avatarUrl: json['avatar_url'] as String?,
    );
  }
}

class UserProfile extends UserProfileBrief {
  final String? bio;
  final int pointsBalance;
  final int agentCount;
  final DateTime createdAt;

  UserProfile({
    required super.id,
    required super.nickname,
    super.avatarUrl,
    this.bio,
    required this.pointsBalance,
    required this.agentCount,
    required this.createdAt,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as String,
      nickname: json['nickname'] as String,
      avatarUrl: json['avatar_url'] as String?,
      bio: json['bio'] as String?,
      pointsBalance: json['points_balance'] as int? ?? 0,
      agentCount: json['agent_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}


// ============================================================
// WebSocket 事件名常量
// ============================================================

class WsEvents {
  static const ping = 'ping';
  static const pong = 'pong';
  static const roomJoin = 'room.join';
  static const roomLeave = 'room.leave';
  static const roomJoined = 'room.joined';
  static const messageSend = 'message.send';
  static const messageSendPrivate = 'message.send_private';
  static const messageNew = 'message.new';
  static const messageNewPrivate = 'message.new_private';
  static const messageSent = 'message.sent';
  static const messageRejected = 'message.rejected';
  static const messageDeleted = 'message.deleted';
  static const memberJoined = 'member.joined';
  static const memberLeft = 'member.left';
  static const agentStatusChange = 'agent.status';
  static const typingStart = 'typing.start';
  static const typingStop = 'typing.stop';
  static const typingIndicator = 'typing.indicator';
  static const notificationNew = 'notification.new';
  static const sync = 'sync';
  static const error = 'error';
}
