/// AetherVerse — 登录页
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/constants.dart';
import '../../core/theme.dart';
import '../../providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _codeController = TextEditingController();

  bool _isPasswordMode = true;
  bool _obscurePassword = true;
  int _countdown = 0;
  Timer? _timer;

  @override
  void dispose() {
    _phoneController.dispose();
    _passwordController.dispose();
    _codeController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  // --- 发送验证码 ---
  void _sendCode() async {
    final phone = _phoneController.text.trim();
    if (!AppConstants.phonePattern.hasMatch(phone)) {
      _showError('请输入正确的手机号');
      return;
    }

    try {
      await ref.read(authStateProvider.notifier).sendSmsCode(phone);
      _showMessage('验证码已发送');
      setState(() => _countdown = AppConstants.smsCountdownSeconds);
      _timer = Timer.periodic(const Duration(seconds: 1), (t) {
        setState(() {
          _countdown--;
          if (_countdown <= 0) t.cancel();
        });
      });
    } catch (e) {
      _showError(e.toString());
    }
  }

  // --- 登录 ---
  void _login() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    final phone = _phoneController.text.trim();

    if (_isPasswordMode) {
      await ref.read(authStateProvider.notifier).loginByPassword(
            phone,
            _passwordController.text,
          );
    } else {
      await ref.read(authStateProvider.notifier).loginBySms(
            phone,
            _codeController.text.trim(),
          );
    }

    final state = ref.read(authStateProvider).valueOrNull;
    if (state?.error != null && mounted) {
      _showError(state!.error!);
    }
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.redAccent),
    );
  }

  void _showMessage(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);
    final isLoading = authState.valueOrNull?.isLoading ?? false;
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 60),

                // --- Logo ---
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    gradient: AppTheme.brandGradient,
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: const Icon(Icons.auto_awesome, color: Colors.white, size: 32),
                ),
                const SizedBox(height: 24),

                // --- 标题 ---
                Text('欢迎回来', style: Theme.of(context).textTheme.headlineLarge),
                const SizedBox(height: 6),
                Text(
                  '登录 AetherVerse，开启 AI 社交之旅',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: cs.onSurfaceVariant,
                      ),
                ),
                const SizedBox(height: 40),

                // --- 手机号 ---
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: '手机号',
                    prefixIcon: Icon(Icons.phone_android),
                    hintText: '请输入 11 位手机号',
                  ),
                  validator: (v) {
                    if (v == null || !AppConstants.phonePattern.hasMatch(v.trim())) {
                      return '请输入正确的手机号';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // --- 密码 / 验证码 ---
                if (_isPasswordMode)
                  TextFormField(
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    decoration: InputDecoration(
                      labelText: '密码',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscurePassword ? Icons.visibility_off : Icons.visibility,
                        ),
                        onPressed: () =>
                            setState(() => _obscurePassword = !_obscurePassword),
                      ),
                    ),
                    validator: (v) {
                      if (v == null || v.length < AppConstants.minPasswordLength) {
                        return '密码至少 ${AppConstants.minPasswordLength} 位';
                      }
                      return null;
                    },
                  )
                else
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _codeController,
                          keyboardType: TextInputType.number,
                          maxLength: AppConstants.smsCodeLength,
                          decoration: const InputDecoration(
                            labelText: '验证码',
                            prefixIcon: Icon(Icons.sms_outlined),
                            counterText: '',
                          ),
                          validator: (v) {
                            if (v == null || v.length != AppConstants.smsCodeLength) {
                              return '请输入 ${AppConstants.smsCodeLength} 位验证码';
                            }
                            return null;
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      SizedBox(
                        width: 120,
                        height: 52,
                        child: OutlinedButton(
                          onPressed: _countdown > 0 ? null : _sendCode,
                          child: Text(
                            _countdown > 0 ? '${_countdown}s' : '获取验证码',
                          ),
                        ),
                      ),
                    ],
                  ),
                const SizedBox(height: 12),

                // --- 切换登录方式 ---
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton(
                      onPressed: () => setState(() {
                        _isPasswordMode = !_isPasswordMode;
                      }),
                      child: Text(
                        _isPasswordMode ? '验证码登录' : '密码登录',
                      ),
                    ),
                    if (_isPasswordMode)
                      TextButton(
                        onPressed: () => context.push('/forgot-password'),
                        child: const Text('忘记密码？'),
                      ),
                  ],
                ),
                const SizedBox(height: 28),

                // --- 登录按钮 ---
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: isLoading ? null : _login,
                    child: isLoading
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('登录'),
                  ),
                ),
                const SizedBox(height: 20),

                // --- 注册入口 ---
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      '还没有账号？',
                      style: TextStyle(color: cs.onSurfaceVariant),
                    ),
                    TextButton(
                      onPressed: () => context.push('/register'),
                      child: const Text('立即注册'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
