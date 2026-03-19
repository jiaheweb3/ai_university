/// AetherVerse — 积分 API 服务
library;

import '../models/point_notification.dart';
import 'api_client.dart';

class PointService {
  final ApiClient _api = ApiClient();

  /// 获取积分余额
  Future<PointsBalance> getBalance() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/points/balance',
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return PointsBalance.fromJson(res.data!);
    }
    return PointsBalance();
  }

  /// 积分流水
  Future<List<PointTransaction>> getTransactions({
    String? txType,
    String? after,
    int limit = 20,
  }) async {
    final params = <String, dynamic>{
      'limit': limit,
      if (txType != null) 'tx_type': txType,
      if (after != null) 'after': after,
    };
    final res = await _api.get<Map<String, dynamic>>(
      '/points/transactions',
      queryParameters: params,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items
          .map((e) => PointTransaction.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// 充值套餐列表
  Future<List<RechargePackage>> getPackages() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/points/recharge/packages',
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ??
          (res.data! is List ? res.data! as List : []);
      return items
          .map((e) => RechargePackage.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// 发起充值
  Future<Map<String, dynamic>?> recharge({
    required String packageId,
    required String channel,
  }) async {
    final res = await _api.post<Map<String, dynamic>>(
      '/points/recharge',
      data: {'package_id': packageId, 'channel': channel},
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return res.data!;
    }
    return null;
  }
}
