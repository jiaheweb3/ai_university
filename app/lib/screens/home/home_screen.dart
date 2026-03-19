/// AetherVerse — 首页 Shell (底部导航)
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends StatelessWidget {
  final Widget child;
  const HomeScreen({super.key, required this.child});

  static const _tabs = [
    _TabItem(label: '发现', icon: Icons.explore_outlined, activeIcon: Icons.explore),
    _TabItem(label: '消息', icon: Icons.chat_bubble_outline, activeIcon: Icons.chat_bubble),
    _TabItem(label: '创作', icon: Icons.palette_outlined, activeIcon: Icons.palette),
    _TabItem(label: '我的', icon: Icons.person_outline, activeIcon: Icons.person),
  ];

  static const _routes = ['/', '/messages', '/discover', '/profile'];

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    final idx = _routes.indexOf(location);
    return idx >= 0 ? idx : 0;
  }

  @override
  Widget build(BuildContext context) {
    final currentIdx = _currentIndex(context);
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(
            top: BorderSide(
              color: cs.outlineVariant.withValues(alpha: 0.3),
              width: 0.5,
            ),
          ),
        ),
        child: NavigationBar(
          selectedIndex: currentIdx,
          onDestinationSelected: (i) => context.go(_routes[i]),
          labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          height: 64,
          destinations: _tabs
              .map((t) => NavigationDestination(
                    icon: Icon(t.icon),
                    selectedIcon: Icon(t.activeIcon),
                    label: t.label,
                  ))
              .toList(),
        ),
      ),
    );
  }
}

class _TabItem {
  final String label;
  final IconData icon;
  final IconData activeIcon;
  const _TabItem({required this.label, required this.icon, required this.activeIcon});
}
