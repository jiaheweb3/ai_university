/// AetherVerse — App 入口
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'error_handling.dart';
import 'router.dart';
import 'theme.dart';

class AetherVerseApp extends ConsumerWidget {
  const AetherVerseApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final GoRouter router = ref.watch(routerProvider);

    return ErrorBoundary(
      child: MaterialApp.router(
        title: 'AetherVerse',
        debugShowCheckedModeBanner: false,
        scaffoldMessengerKey: AppSnackBar.messengerKey,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        routerConfig: router,
        locale: const Locale('zh', 'CN'),
        supportedLocales: const [
          Locale('zh', 'CN'),
        ],
      ),
    );
  }
}
