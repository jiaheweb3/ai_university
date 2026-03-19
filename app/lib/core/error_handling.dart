/// AetherVerse — 全局错误处理
library;

import 'package:flutter/material.dart';

import '../services/api_client.dart';

/// 全局 Snackbar 工具
class AppSnackBar {
  static final GlobalKey<ScaffoldMessengerState> messengerKey =
      GlobalKey<ScaffoldMessengerState>();

  /// 显示普通消息
  static void show(String message, {Duration? duration}) {
    messengerKey.currentState?.showSnackBar(
      SnackBar(
        content: Text(message),
        duration: duration ?? const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  /// 显示错误消息
  static void showError(String message) {
    messengerKey.currentState?.showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.white, size: 20),
            const SizedBox(width: 8),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: Colors.redAccent,
        duration: const Duration(seconds: 3),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  /// 显示成功消息
  static void showSuccess(String message) {
    messengerKey.currentState?.showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.check_circle_outline, color: Colors.white, size: 20),
            const SizedBox(width: 8),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: Colors.green,
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }

  /// 显示带重试操作的错误
  static void showRetry(String message, VoidCallback onRetry) {
    messengerKey.currentState?.showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.redAccent,
        duration: const Duration(seconds: 5),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        action: SnackBarAction(
          label: '重试',
          textColor: Colors.white,
          onPressed: onRetry,
        ),
      ),
    );
  }
}

/// API 异常 → 用户友好消息
String mapApiError(Object error) {
  if (error is ApiException) {
    return switch (error.code) {
      40001 => '请求参数有误',
      40101 => '登录已过期，请重新登录',
      40301 => '没有权限执行此操作',
      40401 => '未找到相关内容',
      40901 => '操作冲突，请稍后重试',
      42901 => '操作太频繁，请稍后再试',
      _ when error.code >= 500 => '服务器开小差了，请稍后再试',
      _ when error.code == -1 => error.message, // 网络超时等已翻译
      _ => error.message,
    };
  }
  return '发生未知错误';
}

/// 安全执行异步操作 + 自动错误提示
Future<T?> safeCall<T>(
  Future<T> Function() action, {
  String? successMessage,
  VoidCallback? onError,
}) async {
  try {
    final result = await action();
    if (successMessage != null) {
      AppSnackBar.showSuccess(successMessage);
    }
    return result;
  } catch (e) {
    AppSnackBar.showError(mapApiError(e));
    onError?.call();
    return null;
  }
}

/// 安全执行异步操作 + 带重试
Future<T?> safeCallWithRetry<T>(
  Future<T> Function() action, {
  String? errorMessage,
}) async {
  try {
    return await action();
  } catch (e) {
    AppSnackBar.showRetry(
      errorMessage ?? mapApiError(e),
      () => safeCallWithRetry(action, errorMessage: errorMessage),
    );
    return null;
  }
}

/// Flutter 全局错误边界
class ErrorBoundary extends StatelessWidget {
  final Widget child;
  const ErrorBoundary({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    // 在 MaterialApp 级别使用 ErrorWidget.builder
    ErrorWidget.builder = (FlutterErrorDetails details) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.bug_report_outlined,
                  size: 64,
                  color: Theme.of(context).colorScheme.error,
                ),
                const SizedBox(height: 16),
                Text(
                  '出了点问题',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  '请尝试重新启动应用',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ),
      );
    };
    return child;
  }
}
