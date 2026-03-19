/// AetherVerse — 智能体状态管理
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/agent.dart';
import '../services/agent_service.dart';

/// 我的智能体列表状态
class AgentListState {
  final List<Agent> agents;
  final bool isLoading;
  final String? error;

  const AgentListState({
    this.agents = const [],
    this.isLoading = false,
    this.error,
  });

  AgentListState copyWith({
    List<Agent>? agents,
    bool? isLoading,
    String? error,
  }) {
    return AgentListState(
      agents: agents ?? this.agents,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// 智能体列表 Provider
final agentListProvider =
    StateNotifierProvider<AgentListNotifier, AgentListState>(
  (ref) => AgentListNotifier(),
);

class AgentListNotifier extends StateNotifier<AgentListState> {
  AgentListNotifier() : super(const AgentListState());

  final AgentService _service = AgentService();

  /// 加载列表
  Future<void> load() async {
    state = state.copyWith(isLoading: true);
    try {
      final agents = await _service.getMyAgents();
      state = state.copyWith(agents: agents, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// 创建智能体
  Future<Agent?> create({
    required String name,
    String? avatarUrl,
    String? bio,
    String level = 'L1',
    required PersonaConfig personaConfig,
    String? templateId,
  }) async {
    final agent = await _service.createAgent(
      name: name,
      avatarUrl: avatarUrl,
      bio: bio,
      level: level,
      personaConfig: personaConfig,
      templateId: templateId,
    );
    if (agent != null) {
      state = state.copyWith(agents: [...state.agents, agent]);
    }
    return agent;
  }

  /// 编辑智能体
  Future<void> update(
    String agentId, {
    String? name,
    String? avatarUrl,
    String? bio,
    PersonaConfig? personaConfig,
  }) async {
    final updated = await _service.updateAgent(
      agentId,
      name: name,
      avatarUrl: avatarUrl,
      bio: bio,
      personaConfig: personaConfig,
    );
    if (updated != null) {
      state = state.copyWith(
        agents: state.agents.map((a) => a.id == agentId ? updated : a).toList(),
      );
    }
  }

  /// 删除智能体 (乐观删除 + API 失败回滚)
  Future<void> delete(String agentId) async {
    final backup = state.agents;
    // 乐观删除
    state = state.copyWith(
      agents: state.agents.where((a) => a.id != agentId).toList(),
    );
    try {
      await _service.deleteAgent(agentId);
    } catch (e) {
      // API 失败 → 回滚
      state = state.copyWith(agents: backup);
      rethrow;
    }
  }

  /// 指派进入房间
  Future<void> assignRoom(String agentId, String roomId) async {
    await _service.assignRoom(agentId, roomId);
    await load(); // 刷新
  }

  /// 退出房间
  Future<void> leaveRoom(String agentId) async {
    await _service.leaveRoom(agentId);
    await load();
  }

  /// 暂停/恢复发言
  Future<void> toggleSpeaking(String agentId, bool isSpeaking) async {
    await _service.setSpeaking(agentId, isSpeaking);
    state = state.copyWith(
      agents: state.agents.map((a) {
        return a.id == agentId ? a.copyWith(isSpeaking: isSpeaking) : a;
      }).toList(),
    );
  }
}

/// 人格模板 Provider
final personaTemplatesProvider =
    FutureProvider<List<PersonaTemplate>>((ref) async {
  return AgentService().getTemplates();
});
