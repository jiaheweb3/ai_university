/// AetherVerse — 智能体 API 服务
library;

import '../models/agent.dart';
import 'api_client.dart';

class AgentService {
  final ApiClient _api = ApiClient();

  /// 我的智能体列表
  Future<List<Agent>> getMyAgents() async {
    final res = await _api.get<Map<String, dynamic>>(
      '/agents',
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ??
          (res.data! is List ? res.data! as List : []);
      return items
          .map((e) => Agent.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// 创建智能体 (消耗 50 积分)
  Future<Agent?> createAgent({
    required String name,
    String? avatarUrl,
    String? bio,
    String level = 'L1',
    required PersonaConfig personaConfig,
    String? templateId,
    String? requestId,
  }) async {
    final res = await _api.post<Map<String, dynamic>>(
      '/agents',
      data: {
        'name': name,
        if (avatarUrl != null) 'avatar_url': avatarUrl,
        if (bio != null) 'bio': bio,
        'level': level,
        'persona_config': personaConfig.toJson(),
        if (templateId != null) 'template_id': templateId,
        if (requestId != null) 'request_id': requestId,
      },
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return Agent.fromJson(res.data!);
    }
    return null;
  }

  /// 智能体详情
  Future<Agent?> getAgent(String agentId) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/agents/$agentId',
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return Agent.fromJson(res.data!);
    }
    return null;
  }

  /// 编辑智能体
  Future<Agent?> updateAgent(
    String agentId, {
    String? name,
    String? avatarUrl,
    String? bio,
    PersonaConfig? personaConfig,
  }) async {
    final res = await _api.patch<Map<String, dynamic>>(
      '/agents/$agentId',
      data: {
        if (name != null) 'name': name,
        if (avatarUrl != null) 'avatar_url': avatarUrl,
        if (bio != null) 'bio': bio,
        if (personaConfig != null) 'persona_config': personaConfig.toJson(),
      },
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      return Agent.fromJson(res.data!);
    }
    return null;
  }

  /// 删除智能体
  Future<void> deleteAgent(String agentId) async {
    await _api.delete('/agents/$agentId');
  }

  /// 指派智能体进入房间
  Future<void> assignRoom(String agentId, String roomId) async {
    await _api.post('/agents/$agentId/room/join', data: {'room_id': roomId});
  }

  /// 智能体退出房间
  Future<void> leaveRoom(String agentId) async {
    await _api.post('/agents/$agentId/room/leave');
  }

  /// 暂停/恢复发言
  Future<void> setSpeaking(String agentId, bool isSpeaking) async {
    await _api.patch('/agents/$agentId/speaking', data: {'is_speaking': isSpeaking});
  }

  /// 获取智能体记忆
  Future<List<AgentMemory>> getMemories(
    String agentId, {
    String? after,
    int limit = 20,
  }) async {
    final params = <String, dynamic>{
      'limit': limit,
      if (after != null) 'after': after,
    };
    final res = await _api.get<Map<String, dynamic>>(
      '/agents/$agentId/memories',
      queryParameters: params,
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ?? [];
      return items
          .map((e) => AgentMemory.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// 删除记忆条目
  Future<void> deleteMemory(String agentId, String memoryId) async {
    await _api.delete('/agents/$agentId/memories/$memoryId');
  }

  /// 人格模板列表
  Future<List<PersonaTemplate>> getTemplates({bool onboarding = false}) async {
    final res = await _api.get<Map<String, dynamic>>(
      '/agents/templates',
      queryParameters: {if (onboarding) 'onboarding': true},
      fromData: (d) => d as Map<String, dynamic>,
    );
    if (res.isSuccess && res.data != null) {
      final items = res.data!['items'] as List<dynamic>? ??
          (res.data! is List ? res.data! as List : []);
      return items
          .map((e) => PersonaTemplate.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    return [];
  }
}
