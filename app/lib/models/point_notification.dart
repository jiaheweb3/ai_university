/// AetherVerse — 积分 & 通知 & 举报 数据模型
library;

// ============================================================
// 积分
// ============================================================

/// 积分余额
class PointsBalance {
  final int balance;
  final int frozen;
  final int freeChatRemaining;
  final int freeImageRemaining;

  PointsBalance({
    this.balance = 0,
    this.frozen = 0,
    this.freeChatRemaining = 0,
    this.freeImageRemaining = 0,
  });

  factory PointsBalance.fromJson(Map<String, dynamic> json) {
    return PointsBalance(
      balance: json['balance'] as int? ?? 0,
      frozen: json['frozen'] as int? ?? 0,
      freeChatRemaining: json['free_chat_remaining'] as int? ?? 0,
      freeImageRemaining: json['free_image_remaining'] as int? ?? 0,
    );
  }

  int get available => balance - frozen;
}

/// 积分流水
class PointTransaction {
  final String id;
  final String txType;
  final String status; // frozen, confirmed, refunded
  final int amount;
  final int balanceAfter;
  final String? description;
  final DateTime createdAt;

  PointTransaction({
    required this.id,
    required this.txType,
    this.status = 'confirmed',
    required this.amount,
    required this.balanceAfter,
    this.description,
    required this.createdAt,
  });

  factory PointTransaction.fromJson(Map<String, dynamic> json) {
    return PointTransaction(
      id: json['id'] as String,
      txType: json['tx_type'] as String,
      status: json['status'] as String? ?? 'confirmed',
      amount: json['amount'] as int,
      balanceAfter: json['balance_after'] as int,
      description: json['description'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  bool get isIncome => amount > 0;
}

/// 充值套餐
class RechargePackage {
  final String id;
  final double amountYuan;
  final int points;
  final int bonusPoints;

  RechargePackage({
    required this.id,
    required this.amountYuan,
    required this.points,
    this.bonusPoints = 0,
  });

  factory RechargePackage.fromJson(Map<String, dynamic> json) {
    return RechargePackage(
      id: json['id'] as String,
      amountYuan: (json['amount_yuan'] as num).toDouble(),
      points: json['points'] as int,
      bonusPoints: json['bonus_points'] as int? ?? 0,
    );
  }

  int get totalPoints => points + bonusPoints;
}

// ============================================================
// 通知
// ============================================================

/// 通知
class AppNotification {
  final String id;
  final String ntype; // moderation_result, agent_status, account_security, task_status, transaction
  final String title;
  final String? content;
  final bool isRead;
  final DateTime createdAt;

  AppNotification({
    required this.id,
    required this.ntype,
    required this.title,
    this.content,
    this.isRead = false,
    required this.createdAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as String,
      ntype: json['ntype'] as String,
      title: json['title'] as String,
      content: json['content'] as String?,
      isRead: json['is_read'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

/// 未读通知数
class UnreadCount {
  final int total;
  final Map<String, int> byType;

  UnreadCount({this.total = 0, this.byType = const {}});

  factory UnreadCount.fromJson(Map<String, dynamic> json) {
    return UnreadCount(
      total: json['total'] as int? ?? 0,
      byType: (json['by_type'] as Map<String, dynamic>?)
              ?.map((k, v) => MapEntry(k, v as int)) ??
          {},
    );
  }
}
