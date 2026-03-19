/// AetherVerse — 注册页
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/constants.dart';
import '../../core/theme.dart';
import '../../providers/auth_provider.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();
  final _nicknameController = TextEditingController();

  bool _obscurePassword = true;
  bool _agreeTerms = false;
  int _countdown = 0;
  Timer? _timer;

  @override
  void dispose() {
    _phoneController.dispose();
    _codeController.dispose();
    _passwordController.dispose();
    _nicknameController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  void _sendCode() async {
    final phone = _phoneController.text.trim();
    if (!AppConstants.phonePattern.hasMatch(phone)) {
      _showError('请输入正确的手机号');
      return;
    }
    try {
      await ref.read(authStateProvider.notifier).sendSmsCode(phone, purpose: 'register');
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

  void _register() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    if (!_agreeTerms) {
      _showError('请同意用户协议与隐私政策');
      return;
    }

    await ref.read(authStateProvider.notifier).register(
          phone: _phoneController.text.trim(),
          code: _codeController.text.trim(),
          password: _passwordController.text,
          nickname: _nicknameController.text.trim(),
        );

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
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);
    final isLoading = authState.valueOrNull?.isLoading ?? false;
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 20),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 8),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // --- Logo ---
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    gradient: AppTheme.accentGradient,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(Icons.person_add, color: Colors.white, size: 28),
                ),
                const SizedBox(height: 20),

                Text('创建账号', style: Theme.of(context).textTheme.headlineLarge),
                const SizedBox(height: 6),
                Text(
                  '加入 AetherVerse，遇见你的 AI 搭档',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: cs.onSurfaceVariant,
                      ),
                ),
                const SizedBox(height: 32),

                // --- 昵称 ---
                TextFormField(
                  controller: _nicknameController,
                  decoration: const InputDecoration(
                    labelText: '昵称',
                    prefixIcon: Icon(Icons.badge_outlined),
                    hintText: '2-16 个字符',
                  ),
                  validator: (v) {
                    if (v == null || v.trim().length < 2) return '昵称至少 2 个字符';
                    if (v.trim().length > AppConstants.maxNicknameLength) {
                      return '昵称最多 ${AppConstants.maxNicknameLength} 个字符';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // --- 手机号 ---
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: '手机号',
                    prefixIcon: Icon(Icons.phone_android),
                  ),
                  validator: (v) {
                    if (v == null || !AppConstants.phonePattern.hasMatch(v.trim())) {
                      return '请输入正确的手机号';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // --- 验证码 ---
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
                        child: Text(_countdown > 0 ? '${_countdown}s' : '获取验证码'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // --- 密码 ---
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    labelText: '密码',
                    prefixIcon: const Icon(Icons.lock_outline),
                    hintText: '8-20 位',
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
                    if (v.length > AppConstants.maxPasswordLength) {
                      return '密码最多 ${AppConstants.maxPasswordLength} 位';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 20),

                // --- 协议勾选 ---
                Row(
                  children: [
                    Checkbox(
                      value: _agreeTerms,
                      onChanged: (v) => setState(() => _agreeTerms = v ?? false),
                      visualDensity: VisualDensity.compact,
                    ),
                    Expanded(
                      child: Wrap(
                        children: [
                          Text('我已阅读并同意 ',
                              style: TextStyle(fontSize: 13, color: cs.onSurfaceVariant)),
                          GestureDetector(
                            onTap: () {}, // TODO: 用户协议
                            child: Text('《用户协议》',
                                style: TextStyle(fontSize: 13, color: cs.primary)),
                          ),
                          Text(' 和 ',
                              style: TextStyle(fontSize: 13, color: cs.onSurfaceVariant)),
                          GestureDetector(
                            onTap: () {}, // TODO: 隐私政策
                            child: Text('《隐私政策》',
                                style: TextStyle(fontSize: 13, color: cs.primary)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // --- 注册按钮 ---
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: isLoading ? null : _register,
                    child: isLoading
                        ? const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('注册'),
                  ),
                ),
                const SizedBox(height: 16),

                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('已有账号？', style: TextStyle(color: cs.onSurfaceVariant)),
                    TextButton(
                      onPressed: () => context.pop(),
                      child: const Text('去登录'),
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
