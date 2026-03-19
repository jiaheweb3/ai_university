/// AetherVerse — GoRouter 路由定义
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/splash_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/splash',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isLoggedIn = authState.valueOrNull?.isLoggedIn ?? false;
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register' ||
          state.matchedLocation == '/forgot-password' ||
          state.matchedLocation == '/splash';

      // 未登录且不在认证页面 → 跳登录
      if (!isLoggedIn && !isAuthRoute) {
        return '/login';
      }
      // 已登录但在认证页面 → 跳首页
      if (isLoggedIn && isAuthRoute) {
        return '/';
      }
      return null;
    },
    routes: [
      // --- 闪屏 ---
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),

      // --- 认证 ---
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        builder: (context, state) => const ForgotPasswordScreen(),
      ),

      // --- 主页 Shell (底部导航) ---
      ShellRoute(
        builder: (context, state, child) => HomeScreen(child: child),
        routes: [
          GoRoute(
            path: '/',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: _RoomListPlaceholder(),
            ),
          ),
          GoRoute(
            path: '/messages',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: _PlaceholderPage(title: '消息'),
            ),
          ),
          GoRoute(
            path: '/discover',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: _PlaceholderPage(title: '创作'),
            ),
          ),
          GoRoute(
            path: '/profile',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: _PlaceholderPage(title: '我的'),
            ),
          ),
        ],
      ),

      // --- 二级页面 (Week 3+ 实现) ---
      GoRoute(
        path: '/rooms/:roomId',
        builder: (context, state) => _PlaceholderPage(
          title: '房间 ${state.pathParameters['roomId']?.substring(0, 8) ?? ''}',
        ),
      ),
      GoRoute(
        path: '/chat/:convId',
        builder: (context, state) => _PlaceholderPage(
          title: '私聊 ${state.pathParameters['convId']?.substring(0, 8) ?? ''}',
        ),
      ),
      GoRoute(
        path: '/agents',
        builder: (context, state) => const _PlaceholderPage(title: '智能体管理'),
      ),
      GoRoute(
        path: '/points',
        builder: (context, state) => const _PlaceholderPage(title: '积分中心'),
      ),
      GoRoute(
        path: '/settings',
        builder: (context, state) => const _PlaceholderPage(title: '设置'),
      ),
      GoRoute(
        path: '/notifications',
        builder: (context, state) => const _PlaceholderPage(title: '通知中心'),
      ),
    ],
  );
});

// --- 临时占位页 (后续 Week 替换) ---
class _PlaceholderPage extends StatelessWidget {
  final String title;
  const _PlaceholderPage({required this.title});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.construction_rounded,
              size: 64,
              color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.5),
            ),
            const SizedBox(height: 16),
            Text(
              title,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              '功能开发中...',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

// Room list uses the real screen (imported later)
class _RoomListPlaceholder extends StatelessWidget {
  const _RoomListPlaceholder();

  @override
  Widget build(BuildContext context) {
    // This will be replaced with RoomListScreen import
    return const _PlaceholderPage(title: '发现');
  }
}
