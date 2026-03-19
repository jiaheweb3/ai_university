/// AetherVerse — 话题 & 创作 API 服务
library;

import '../models/topic.dart';
import 'api_client.dart';

class TopicService {
  final ApiClient _api = ApiClient();

  /// 话题列表
  Future<List<Topic>> getTopics({
    String? status,
    String? after,
    int limit = 20,
  }) async {
    final params = <String, dynamic>{
      'limit': limit,
      if (status != null) 'status': status,
      if (after != null) 'after': after,
    };
    final res = await _api.get<Map<String, dynamic>>(
      '/topics',
      queryParameters: params,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items.map((e) => Topic.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }

  /// 话题详情
  Future<Topic?> getTopic(String topicId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/topics/$topicId',
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return Topic.fromJson(res.data!);
    }
    return null;
  }

  /// 领取创作任务 (预扣积分)
  Future<void> claimTask(String topicId, {required String agentId, String? requestId}) async {
    final res = await _api.post(
      '/topics/$topicId/claim',
      data: {
        'agent_id': agentId,
        if (requestId != null) 'request_id': requestId,
      },
    );
    if (!res.isSuccess) {
      throw ApiException(code: res.code, message: res.message);
    }
  }

  /// 话题作品列表
  Future<List<Artwork>> getArtworks(
    String topicId, {
    String? after,
    int limit = 20,
  }) async {
    final params = <String, dynamic>{
      'limit': limit,
      if (after != null) 'after': after,
    };
    final res = await _api.get<Map<String, dynamic>>(
      '/topics/$topicId/artworks',
      queryParameters: params,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items.map((e) => Artwork.fromJson(e as Map<String, dynamic>)).toList();
    }
    return [];
  }
}
