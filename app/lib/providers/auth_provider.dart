/// AetherVerse — 认证状态管理
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/shared_types.dart';
import '../services/auth_service.dart';
import '../services/storage_service.dart';

/// 认证状态
class AuthState {
  final bool isLoggedIn;
  final UserProfile? user;
  final bool isLoading;
  final String? error;

  const AuthState({
    this.isLoggedIn = false,
    this.user,
    this.isLoading = false,
    this.error,
  });

  AuthState copyWith({
    bool? isLoggedIn,
    UserProfile? user,
    bool? isLoading,
    String? error,
  }) {
    return AuthState(
      isLoggedIn: isLoggedIn ?? this.isLoggedIn,
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

/// AuthState Provider
final authStateProvider =
    AsyncNotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends AsyncNotifier<AuthState> {
  late final AuthService _authService;

  @override
  Future<AuthState> build() async {
    _authService = AuthService();

    // 检查本地 Token
    if (StorageService.isLoggedIn) {
      try {
        final user = await _authService.getCurrentUser();
        return AuthState(isLoggedIn: true, user: user);
      } catch (_) {
        await StorageService.clearTokens();
      }
    }
    return const AuthState();
  }

  /// 密码登录
  Future<void> loginByPassword(String phone, String password) async {
    final currentUser = state.valueOrNull?.user;
    state = AsyncValue.data(AuthState(isLoading: true, user: currentUser));
    try {
      final user = await _authService.loginByPassword(
        phone: phone,
        password: password,
      );
      state = AsyncValue.data(AuthState(isLoggedIn: true, user: user));
    } catch (e) {
      state = AsyncValue.data(AuthState(error: e.toString()));
    }
  }

  /// 验证码登录
  Future<void> loginBySms(String phone, String code) async {
    final currentUser = state.valueOrNull?.user;
    state = AsyncValue.data(AuthState(isLoading: true, user: currentUser));
    try {
      final user = await _authService.loginBySms(phone: phone, code: code);
      state = AsyncValue.data(AuthState(isLoggedIn: true, user: user));
    } catch (e) {
      state = AsyncValue.data(AuthState(error: e.toString()));
    }
  }

  /// 注册
  Future<void> register({
    required String phone,
    required String code,
    required String password,
    required String nickname,
  }) async {
    state = const AsyncValue.data(AuthState(isLoading: true));
    try {
      final user = await _authService.register(
        phone: phone,
        code: code,
        password: password,
        nickname: nickname,
      );
      state = AsyncValue.data(AuthState(isLoggedIn: true, user: user));
    } catch (e) {
      state = AsyncValue.data(AuthState(error: e.toString()));
    }
  }

  /// 登出
  Future<void> logout() async {
    try {
      await _authService.logout();
    } finally {
      state = const AsyncValue.data(AuthState());
    }
  }

  /// 发送验证码
  Future<void> sendSmsCode(String phone, {String purpose = 'login'}) async {
    await _authService.sendSmsCode(phone, purpose: purpose);
  }
}
