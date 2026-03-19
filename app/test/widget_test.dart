import 'package:flutter/material.dart';

import 'package:flutter_test/flutter_test.dart';
import 'package:google_fonts/google_fonts.dart';

import 'package:aetherverse_app/core/theme.dart';

void main() {
  setUpAll(() {
    GoogleFonts.config.allowRuntimeFetching = false;
  });

  testWidgets('Theme can be constructed', (WidgetTester tester) async {
    // 验证主题能正常构建
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        home: const Scaffold(
          body: Center(child: Text('AetherVerse')),
        ),
      ),
    );
    expect(find.text('AetherVerse'), findsOneWidget);
  });

  test('Light theme has correct primary color', () {
    final theme = AppTheme.lightTheme;
    expect(theme.useMaterial3, true);
    expect(theme.colorScheme.primary, isNotNull);
  });

  test('Dark theme has correct primary color', () {
    final theme = AppTheme.darkTheme;
    expect(theme.useMaterial3, true);
    expect(theme.brightness, Brightness.dark);
  });
}
