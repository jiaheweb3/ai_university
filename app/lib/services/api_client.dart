/// AetherVerse — Dio HTTP 客户端封装
library;

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../core/constants.dart';
import '../models/shared_types.dart';
import 'storage_service.dart';

/// 统一 API 异常
class ApiException implements Exception {
  final int code;
  final String message;
  final String? detail;

  ApiException({required this.code, required this.message, this.detail});

  @override
  String toString() => 'ApiException($code): $message';
}

/// Dio HTTP 客户端 — 统一 JWT 注入 / 自动刷新 / 错误处理
class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;
  bool _isRefreshing = false;
  final List<void Function(String)> _pendingRequests = [];

  ApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      contentType: 'application/json',
    ));

    // --- Auth 拦截器 ---
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = StorageService.accessToken;
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 && !_isRefreshing) {
          await _handleTokenRefresh(error, handler);
        } else {
          handler.next(error);
        }
      },
    ));

    // --- 日志拦截器 (仅 debug) ---
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (o) => debugPrint(o.toString()),
      ));
    }
  }

  Dio get dio => _dio;

  // ============================================================
  // 泛型请求方法
  // ============================================================

  /// GET 请求
  Future<ApiResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    T Function(dynamic)? fromData,
  }) async {
    final response = await _request(
      () => _dio.get(path, queryParameters: queryParameters),
    );
    return ApiResponse.fromJson(response.data, fromData);
  }

  /// POST 请求
  Future<ApiResponse<T>> post<T>(
    String path, {
    dynamic data,
    T Function(dynamic)? fromData,
  }) async {
    final response = await _request(
      () => _dio.post(path, data: data),
    );
    return ApiResponse.fromJson(response.data, fromData);
  }

  /// PATCH 请求
  Future<ApiResponse<T>> patch<T>(
    String path, {
    dynamic data,
    T Function(dynamic)? fromData,
  }) async {
    final response = await _request(
      () => _dio.patch(path, data: data),
    );
    return ApiResponse.fromJson(response.data, fromData);
  }

  /// PUT 请求
  Future<ApiResponse<T>> put<T>(
    String path, {
    dynamic data,
    T Function(dynamic)? fromData,
  }) async {
    final response = await _request(
      () => _dio.put(path, data: data),
    );
    return ApiResponse.fromJson(response.data, fromData);
  }

  /// DELETE 请求
  Future<ApiResponse<T>> delete<T>(
    String path, {
    T Function(dynamic)? fromData,
  }) async {
    final response = await _request(
      () => _dio.delete(path),
    );
    return ApiResponse.fromJson(response.data, fromData);
  }

  /// 上传文件
  Future<ApiResponse<T>> upload<T>(
    String path, {
    required FormData formData,
    T Function(dynamic)? fromData,
    void Function(int, int)? onSendProgress,
  }) async {
    final response = await _request(
      () => _dio.post(
        path,
        data: formData,
        onSendProgress: onSendProgress,
      ),
    );
    return ApiResponse.fromJson(response.data, fromData);
  }

  // ============================================================
  // 内部方法
  // ============================================================

  Future<Response> _request(Future<Response> Function() request) async {
    try {
      return await request();
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  ApiException _handleDioError(DioException e) {
    if (e.response?.data is Map<String, dynamic>) {
      final data = e.response!.data as Map<String, dynamic>;
      return ApiException(
        code: data['code'] as int? ?? e.response!.statusCode ?? -1,
        message: data['message'] as String? ?? '请求失败',
        detail: data['detail'] as String?,
      );
    }

    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiException(code: -1, message: '网络连接超时，请重试');
      case DioExceptionType.connectionError:
        return ApiException(code: -1, message: '无法连接服务器');
      case DioExceptionType.cancel:
        return ApiException(code: -1, message: '请求已取消');
      default:
        return ApiException(
          code: e.response?.statusCode ?? -1,
          message: '网络请求失败: ${e.message}',
        );
    }
  }

  /// Token 自动刷新 (401 → refresh → 重试)
  Future<void> _handleTokenRefresh(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    _isRefreshing = true;

    try {
      final refreshToken = StorageService.refreshToken;
      if (refreshToken == null) {
        await StorageService.clearTokens();
        handler.next(error);
        return;
      }

      // 用独立 Dio 实例刷新 (避免循环)
      final freshDio = Dio(BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        contentType: 'application/json',
      ));
      final response = await freshDio.post(
        '/auth/token/refresh',
        data: {'refresh_token': refreshToken},
      );

      final data = response.data as Map<String, dynamic>;
      if (data['code'] == 0 && data['data'] != null) {
        final tokenData = data['data'] as Map<String, dynamic>;
        await StorageService.saveTokens(
          accessToken: tokenData['access_token'] as String,
          refreshToken: tokenData['refresh_token'] as String,
          expiresIn: tokenData['expires_in'] as int,
        );

        // 重试原请求
        final opts = error.requestOptions;
        opts.headers['Authorization'] =
            'Bearer ${tokenData['access_token']}';
        final retryResponse = await _dio.fetch(opts);
        handler.resolve(retryResponse);

        // 通知排队的请求
        for (final callback in _pendingRequests) {
          callback(tokenData['access_token'] as String);
        }
        _pendingRequests.clear();
      } else {
        await StorageService.clearTokens();
        handler.next(error);
      }
    } catch (_) {
      await StorageService.clearTokens();
      handler.next(error);
    } finally {
      _isRefreshing = false;
    }
  }
}
