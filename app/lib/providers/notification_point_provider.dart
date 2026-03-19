/// AetherVerse — 通知 & 积分状态管理
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/point_notification.dart';
import '../services/notification_service.dart';
import '../services/point_service.dart';

// ============================================================
// 通知
// ============================================================

final unreadCountProvider = StateNotifierProvider<UnreadCountNotifier, UnreadCount>(
  (ref) => UnreadCountNotifier(),
);

class UnreadCountNotifier extends StateNotifier<UnreadCount> {
  UnreadCountNotifier() : super(UnreadCount());

  final NotificationService _service = NotificationService();

  Future<void> refresh() async {
    state = await _service.getUnreadCount();
  }

  /// 标记全部已读后刷新
  Future<void> markAllRead() async {
    await _service.markRead(readAll: true);
    await refresh();
  }
}

// ============================================================
// 积分
// ============================================================

final pointsBalanceProvider = StateNotifierProvider<PointsBalanceNotifier, PointsBalance>(
  (ref) => PointsBalanceNotifier(),
);

class PointsBalanceNotifier extends StateNotifier<PointsBalance> {
  PointsBalanceNotifier() : super(PointsBalance());

  final PointService _service = PointService();

  Future<void> refresh() async {
    state = await _service.getBalance();
  }
}

/// 充值套餐 (一次性加载)
final rechargePackagesProvider = FutureProvider<List<RechargePackage>>((ref) async {
  return PointService().getPackages();
});
