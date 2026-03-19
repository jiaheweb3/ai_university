/// AetherVerse — 房间状态管理
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/api_client.dart';

/// 房间模型 (从 API 解析)
class Room {
  final String id;
  final String name;
  final String? description;
  final String? category;
  final List<String> tags;
  final String? coverUrl;
  final String status;
  final int onlineCount;
  final int messageCount;
  final DateTime createdAt;

  Room({
    required this.id,
    required this.name,
    this.description,
    this.category,
    this.tags = const [],
    this.coverUrl,
    this.status = 'active',
    this.onlineCount = 0,
    this.messageCount = 0,
    required this.createdAt,
  });

  factory Room.fromJson(Map<String, dynamic> json) {
    return Room(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      category: json['category'] as String?,
      tags: (json['tags'] as List<dynamic>?)?.cast<String>() ?? [],
      coverUrl: json['cover_url'] as String?,
      status: json['status'] as String? ?? 'active',
      onlineCount: json['online_count'] as int? ?? 0,
      messageCount: json['message_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

/// 房间列表状态
class RoomListState {
  final List<Room> rooms;
  final bool isLoading;
  final bool hasMore;
  final String? nextCursor;
  final String? error;
  final String? category;
  final String sort;
  final String? search;

  const RoomListState({
    this.rooms = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.nextCursor,
    this.error,
    this.category,
    this.sort = 'hot',
    this.search,
  });

  RoomListState copyWith({
    List<Room>? rooms,
    bool? isLoading,
    bool? hasMore,
    String? nextCursor,
    String? error,
    String? category,
    String? sort,
    String? search,
  }) {
    return RoomListState(
      rooms: rooms ?? this.rooms,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      nextCursor: nextCursor ?? this.nextCursor,
      error: error,
      category: category ?? this.category,
      sort: sort ?? this.sort,
      search: search ?? this.search,
    );
  }
}

/// 房间列表 Provider
final roomListProvider =
    StateNotifierProvider<RoomListNotifier, RoomListState>(
  (ref) => RoomListNotifier(),
);

class RoomListNotifier extends StateNotifier<RoomListState> {
  RoomListNotifier() : super(const RoomListState());

  final ApiClient _api = ApiClient();

  /// 加载房间列表 (首次/刷新)
  Future<void> loadRooms({String? category, String? sort, String? search}) async {
    state = state.copyWith(
      isLoading: true,
      category: category,
      sort: sort ?? state.sort,
      search: search,
    );

    try {
      final params = <String, dynamic>{
        'limit': 20,
        if (category != null) 'category': category,
        'sort': sort ?? state.sort,
        if (search != null && search.isNotEmpty) 'search': search,
      };

      final res = await _api.get<Map<String, dynamic>>(
        '/rooms',
        queryParameters: params,
        fromData: (d) => d as Map<String, dynamic>,
      );

      if (res.isSuccess && res.data != null) {
        final items = (res.data!['items'] as List<dynamic>)
            .map((e) => Room.fromJson(e as Map<String, dynamic>))
            .toList();
        state = state.copyWith(
          rooms: items,
          isLoading: false,
          hasMore: res.data!['has_more'] as bool? ?? false,
          nextCursor: res.data!['next_cursor'] as String?,
        );
      } else {
        state = state.copyWith(isLoading: false, error: res.message);
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// 加载更多 (翻页)
  Future<void> loadMore() async {
    if (state.isLoading || !state.hasMore || state.nextCursor == null) return;

    state = state.copyWith(isLoading: true);

    try {
      final params = <String, dynamic>{
        'limit': 20,
        'after': state.nextCursor,
        if (state.category != null) 'category': state.category,
        'sort': state.sort,
        if (state.search != null && state.search!.isNotEmpty)
          'search': state.search,
      };

      final res = await _api.get<Map<String, dynamic>>(
        '/rooms',
        queryParameters: params,
        fromData: (d) => d as Map<String, dynamic>,
      );

      if (res.isSuccess && res.data != null) {
        final items = (res.data!['items'] as List<dynamic>)
            .map((e) => Room.fromJson(e as Map<String, dynamic>))
            .toList();
        state = state.copyWith(
          rooms: [...state.rooms, ...items],
          isLoading: false,
          hasMore: res.data!['has_more'] as bool? ?? false,
          nextCursor: res.data!['next_cursor'] as String?,
        );
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// 切换排序
  void setSort(String sort) {
    loadRooms(sort: sort, category: state.category);
  }

  /// 切换分类
  void setCategory(String? category) {
    loadRooms(category: category, sort: state.sort);
  }

  /// 搜索
  void searchRooms(String query) {
    loadRooms(search: query, sort: state.sort);
  }
}
