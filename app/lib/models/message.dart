/// AetherVerse — 消息数据模型
library;

/// 消息发送者
class MessageSender {
  final String id;
  final String type; // user, agent, system
  final String nickname;
  final String? avatarUrl;
  final bool isAi;
  final String? ownerNickname;

  MessageSender({
    required this.id,
    required this.type,
    required this.nickname,
    this.avatarUrl,
    this.isAi = false,
    this.ownerNickname,
  });

  factory MessageSender.fromJson(Map<String, dynamic> json) {
    return MessageSender(
      id: json['id'] as String,
      type: json['type'] as String? ?? 'user',
      nickname: json['nickname'] as String? ?? '',
      avatarUrl: json['avatar_url'] as String?,
      isAi: json['is_ai'] as bool? ?? false,
      ownerNickname: json['owner_nickname'] as String?,
    );
  }
}

/// 消息
class Message {
  final String id;
  final String? roomId;
  final String? conversationId;
  final MessageSender sender;
  final String msgType; // text, image, system, ai_generated
  final String? content;
  final String? imageUrl;
  final String? replyToId;
  final List<String> mentions;
  final bool isAiGenerated;
  final String? moderationStatus;
  final DateTime createdAt;

  Message({
    required this.id,
    this.roomId,
    this.conversationId,
    required this.sender,
    required this.msgType,
    this.content,
    this.imageUrl,
    this.replyToId,
    this.mentions = const [],
    this.isAiGenerated = false,
    this.moderationStatus,
    required this.createdAt,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'] as String,
      roomId: json['room_id'] as String?,
      conversationId: json['conversation_id'] as String?,
      sender: MessageSender.fromJson(json['sender'] as Map<String, dynamic>),
      msgType: json['msg_type'] as String? ?? 'text',
      content: json['content'] as String?,
      imageUrl: json['image_url'] as String?,
      replyToId: json['reply_to_id'] as String?,
      mentions: (json['mentions'] as List<dynamic>?)?.cast<String>() ?? [],
      isAiGenerated: json['is_ai_generated'] as bool? ?? false,
      moderationStatus: json['moderation_status'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  bool get isText => msgType == 'text';
  bool get isImage => msgType == 'image';
  bool get isSystem => msgType == 'system';
}

/// 私聊会话
class Conversation {
  final String id;
  final String convType; // user_to_user, user_to_agent
  final ConversationParticipant participant;
  final Message? lastMessage;
  final int unreadCount;
  final DateTime updatedAt;

  Conversation({
    required this.id,
    required this.convType,
    required this.participant,
    this.lastMessage,
    this.unreadCount = 0,
    required this.updatedAt,
  });

  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      id: json['id'] as String,
      convType: json['conv_type'] as String? ?? 'user_to_user',
      participant: ConversationParticipant.fromJson(
        json['participant'] as Map<String, dynamic>,
      ),
      lastMessage: json['last_message'] != null
          ? Message.fromJson(json['last_message'] as Map<String, dynamic>)
          : null,
      unreadCount: json['unread_count'] as int? ?? 0,
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}

/// 会话对方
class ConversationParticipant {
  final String id;
  final String nickname;
  final String? avatarUrl;

  ConversationParticipant({
    required this.id,
    required this.nickname,
    this.avatarUrl,
  });

  factory ConversationParticipant.fromJson(Map<String, dynamic> json) {
    return ConversationParticipant(
      id: json['id'] as String,
      nickname: json['nickname'] as String? ?? '',
      avatarUrl: json['avatar_url'] as String?,
    );
  }
}
