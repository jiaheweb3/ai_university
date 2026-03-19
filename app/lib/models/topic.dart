/// AetherVerse — 话题 & 创作数据模型
library;

/// 话题简要
class TopicBrief {
  final String id;
  final String title;
  final String status; // draft, active, ended, archived
  final DateTime? deadline;

  TopicBrief({required this.id, required this.title, this.status = 'active', this.deadline});

  factory TopicBrief.fromJson(Map<String, dynamic> json) {
    return TopicBrief(
      id: json['id'] as String,
      title: json['title'] as String,
      status: json['status'] as String? ?? 'active',
      deadline: json['deadline'] != null ? DateTime.parse(json['deadline'] as String) : null,
    );
  }

  bool get isActive => status == 'active';
  bool get isEnded => status == 'ended';
}

/// 话题详情
class Topic extends TopicBrief {
  final String? description;
  final List<String> keywords;
  final String? referenceUrl;
  final int participantCount;
  final int artworkCount;
  final DateTime createdAt;

  Topic({
    required super.id,
    required super.title,
    super.status,
    super.deadline,
    this.description,
    this.keywords = const [],
    this.referenceUrl,
    this.participantCount = 0,
    this.artworkCount = 0,
    required this.createdAt,
  });

  factory Topic.fromJson(Map<String, dynamic> json) {
    return Topic(
      id: json['id'] as String,
      title: json['title'] as String,
      status: json['status'] as String? ?? 'active',
      deadline: json['deadline'] != null ? DateTime.parse(json['deadline'] as String) : null,
      description: json['description'] as String?,
      keywords: (json['keywords'] as List<dynamic>?)?.cast<String>() ?? [],
      referenceUrl: json['reference_url'] as String?,
      participantCount: json['participant_count'] as int? ?? 0,
      artworkCount: json['artwork_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

/// 作品
class Artwork {
  final String id;
  final String topicId;
  final String? imageUrl;
  final String? thumbnailUrl;
  final String status; // generating, pending_review, approved, rejected, failed
  final int pointsCost;
  final DateTime createdAt;

  Artwork({
    required this.id,
    required this.topicId,
    this.imageUrl,
    this.thumbnailUrl,
    this.status = 'generating',
    this.pointsCost = 0,
    required this.createdAt,
  });

  factory Artwork.fromJson(Map<String, dynamic> json) {
    return Artwork(
      id: json['id'] as String,
      topicId: json['topic_id'] as String,
      imageUrl: json['image_url'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
      status: json['status'] as String? ?? 'generating',
      pointsCost: json['points_cost'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  bool get isApproved => status == 'approved';
  bool get isGenerating => status == 'generating';
}
