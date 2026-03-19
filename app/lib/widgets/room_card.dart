/// AetherVerse — 房间卡片
library;

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../providers/room_provider.dart';

class RoomCard extends StatelessWidget {
  final Room room;
  final VoidCallback? onTap;

  const RoomCard({super.key, required this.room, this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              // --- 封面 ---
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: SizedBox(
                  width: 72,
                  height: 72,
                  child: room.coverUrl != null && room.coverUrl!.isNotEmpty
                      ? CachedNetworkImage(
                          imageUrl: room.coverUrl!,
                          fit: BoxFit.cover,
                          placeholder: (_, __) => _coverPlaceholder(cs),
                          errorWidget: (_, __, ___) => _coverPlaceholder(cs),
                        )
                      : _coverPlaceholder(cs),
                ),
              ),
              const SizedBox(width: 14),

              // --- 信息 ---
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 房间名
                    Text(
                      room.name,
                      style: tt.titleMedium?.copyWith(fontWeight: FontWeight.w600),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),

                    // 描述
                    if (room.description != null && room.description!.isNotEmpty)
                      Text(
                        room.description!,
                        style: tt.bodySmall,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    const SizedBox(height: 8),

                    // 标签 + 在线人数
                    Row(
                      children: [
                        // 分类标签
                        if (room.category != null)
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: cs.primaryContainer,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              room.category!,
                              style: tt.bodySmall?.copyWith(
                                color: cs.onPrimaryContainer,
                                fontSize: 11,
                              ),
                            ),
                          ),
                        const Spacer(),
                        // 在线人数
                        Icon(
                          Icons.circle,
                          size: 8,
                          color: room.onlineCount > 0
                              ? Colors.greenAccent[400]
                              : cs.outlineVariant,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${room.onlineCount} 在线',
                          style: tt.bodySmall?.copyWith(fontSize: 11),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              // --- 箭头 ---
              Icon(
                Icons.chevron_right,
                color: cs.onSurfaceVariant.withValues(alpha: 0.5),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _coverPlaceholder(ColorScheme cs) {
    return Container(
      color: cs.surfaceContainerHighest,
      child: Icon(
        Icons.forum_outlined,
        color: cs.onSurfaceVariant.withValues(alpha: 0.4),
        size: 28,
      ),
    );
  }
}
