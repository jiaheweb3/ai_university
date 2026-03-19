/// AetherVerse — 智能体数据模型
library;

/// 人格配置
class PersonaConfig {
  final String? personality;
  final String? speakingStyle;
  final String? expertise;
  final String? constraints;

  PersonaConfig({this.personality, this.speakingStyle, this.expertise, this.constraints});

  factory PersonaConfig.fromJson(Map<String, dynamic> json) {
    return PersonaConfig(
      personality: json['personality'] as String?,
      speakingStyle: json['speaking_style'] as String?,
      expertise: json['expertise'] as String?,
      constraints: json['constraints'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    if (personality != null) 'personality': personality,
    if (speakingStyle != null) 'speaking_style': speakingStyle,
    if (expertise != null) 'expertise': expertise,
    if (constraints != null) 'constraints': constraints,
  };
}

/// 智能体
class Agent {
  final String id;
  final String ownerId;
  final String ownerType; // user, system
  final String name;
  final String? avatarUrl;
  final String? bio;
  final String level; // L1, L2
  final String status; // active, paused, suspended
  final PersonaConfig? personaConfig;
  final String? currentRoomId;
  final bool isSpeaking;
  final DateTime createdAt;

  Agent({
    required this.id,
    required this.ownerId,
    required this.ownerType,
    required this.name,
    this.avatarUrl,
    this.bio,
    this.level = 'L1',
    this.status = 'active',
    this.personaConfig,
    this.currentRoomId,
    this.isSpeaking = false,
    required this.createdAt,
  });

  factory Agent.fromJson(Map<String, dynamic> json) {
    return Agent(
      id: json['id'] as String,
      ownerId: json['owner_id'] as String,
      ownerType: json['owner_type'] as String? ?? 'user',
      name: json['name'] as String,
      avatarUrl: json['avatar_url'] as String?,
      bio: json['bio'] as String?,
      level: json['level'] as String? ?? 'L1',
      status: json['status'] as String? ?? 'active',
      personaConfig: json['persona_config'] != null
          ? PersonaConfig.fromJson(json['persona_config'] as Map<String, dynamic>)
          : null,
      currentRoomId: json['current_room_id'] as String?,
      isSpeaking: json['is_speaking'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  bool get isActive => status == 'active';
  bool get isPaused => status == 'paused';
  bool get isInRoom => currentRoomId != null;

  /// 复制并修改指定字段
  Agent copyWith({
    String? name,
    String? avatarUrl,
    String? bio,
    String? level,
    String? status,
    PersonaConfig? personaConfig,
    String? currentRoomId,
    bool? isSpeaking,
  }) {
    return Agent(
      id: id,
      ownerId: ownerId,
      ownerType: ownerType,
      name: name ?? this.name,
      avatarUrl: avatarUrl ?? this.avatarUrl,
      bio: bio ?? this.bio,
      level: level ?? this.level,
      status: status ?? this.status,
      personaConfig: personaConfig ?? this.personaConfig,
      currentRoomId: currentRoomId ?? this.currentRoomId,
      isSpeaking: isSpeaking ?? this.isSpeaking,
      createdAt: createdAt,
    );
  }
}

/// 智能体记忆
class AgentMemory {
  final String id;
  final String content;
  final bool isSummary;
  final DateTime createdAt;
  final DateTime? expiresAt;

  AgentMemory({
    required this.id,
    required this.content,
    this.isSummary = false,
    required this.createdAt,
    this.expiresAt,
  });

  factory AgentMemory.fromJson(Map<String, dynamic> json) {
    return AgentMemory(
      id: json['id'] as String,
      content: json['content'] as String,
      isSummary: json['is_summary'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      expiresAt: json['expires_at'] != null
          ? DateTime.parse(json['expires_at'] as String)
          : null,
    );
  }
}

/// 人格模板
class PersonaTemplate {
  final String id;
  final String name;
  final String? description;
  final String? avatarUrl;
  final PersonaConfig? personaConfig;

  PersonaTemplate({
    required this.id,
    required this.name,
    this.description,
    this.avatarUrl,
    this.personaConfig,
  });

  factory PersonaTemplate.fromJson(Map<String, dynamic> json) {
    return PersonaTemplate(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      personaConfig: json['persona_config'] != null
          ? PersonaConfig.fromJson(json['persona_config'] as Map<String, dynamic>)
          : null,
    );
  }
}
