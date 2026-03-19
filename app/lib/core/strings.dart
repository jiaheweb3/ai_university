/// AetherVerse — 国际化 (i18n) 基础框架
/// 当前版本: 仅中文，预留多语言扩展点
library;

/// 应用文案 — 集中管理所有用户可见字符串
/// 后续接入 flutter_localizations 时直接从此类提取 key
abstract final class S {
  // ============================================================
  // 通用
  // ============================================================
  static const appName = 'AetherVerse';
  static const confirm = '确认';
  static const cancel = '取消';
  static const save = '保存';
  static const delete = '删除';
  static const edit = '编辑';
  static const loading = '加载中...';
  static const loadMore = '加载更多';
  static const noMoreData = '没有更多了';
  static const retry = '重试';
  static const search = '搜索';
  static const submit = '提交';
  static const done = '完成';
  static const back = '返回';

  // ============================================================
  // 错误
  // ============================================================
  static const errorUnknown = '发生未知错误';
  static const errorNetwork = '网络连接异常，请检查网络';
  static const errorTimeout = '网络连接超时，请重试';
  static const errorServer = '服务器开小差了，请稍后再试';
  static const errorUnauthorized = '登录已过期，请重新登录';
  static const errorForbidden = '没有权限执行此操作';
  static const errorNotFound = '未找到相关内容';
  static const errorConflict = '操作冲突，请稍后重试';
  static const errorRateLimit = '操作太频繁，请稍后再试';
  static const errorParam = '请求参数有误';

  // ============================================================
  // 认证
  // ============================================================
  static const authLogin = '登录';
  static const authRegister = '注册';
  static const authLogout = '退出登录';
  static const authForgotPassword = '忘记密码';
  static const authResetPassword = '重置密码';
  static const authPhone = '手机号';
  static const authPhoneHint = '请输入手机号';
  static const authPhoneInvalid = '请输入正确的11位手机号';
  static const authPassword = '密码';
  static const authPasswordHint = '请输入密码';
  static const authPasswordMinLength = '密码长度至少8位';
  static const authPasswordMaxLength = '密码长度最多20位';
  static const authSmsCode = '验证码';
  static const authSmsCodeHint = '请输入6位验证码';
  static const authSendCode = '获取验证码';
  static String authResendCode(int seconds) => '${seconds}s后重发';
  static const authNickname = '昵称';
  static const authNicknameHint = '2-16个字符';
  static const authNewPassword = '新密码';
  static const authOldPassword = '原密码';
  static const authAgreeTerms = '我已阅读并同意用户协议';
  static const authMustAgreeTerms = '请先同意用户协议';
  static const authLoginSuccess = '登录成功';
  static const authRegisterSuccess = '注册成功';
  static const authPasswordMode = '密码登录';
  static const authSmsMode = '验证码登录';
  static const authNoAccount = '还没有账号？';
  static const authHasAccount = '已有账号？';
  static const authGoLogin = '去登录';
  static const authGoRegister = '去注册';

  // ============================================================
  // 导航
  // ============================================================
  static const navDiscover = '发现';
  static const navMessages = '消息';
  static const navCreate = '创作';
  static const navProfile = '我的';

  // ============================================================
  // 房间
  // ============================================================
  static const roomList = '房间列表';
  static const roomJoin = '加入房间';
  static const roomLeave = '离开房间';
  static String roomOnlineCount(int count) => '$count 在线';
  static const roomEmpty = '暂无房间';
  static const roomEmptySubtitle = '过会儿再来看看吧';
  static const roomCategoryAll = '全部';
  static const roomSortHot = '最热';
  static const roomSortNew = '最新';
  static const roomSortJoined = '已加入';

  // ============================================================
  // 消息
  // ============================================================
  static const messageEmpty = '暂无消息';
  static const messageInputHint = '输入消息...';
  static const messageSend = '发送';
  static const messageImage = '[图片]';
  static const messageSystem = '[系统消息]';
  static String messageTyping(String name) => '$name 正在输入...';
  static const messageLoadHistory = '加载更多消息';

  // ============================================================
  // 智能体
  // ============================================================
  static const agentMyAgents = '我的智能体';
  static const agentCreate = '创建智能体';
  static const agentEdit = '编辑智能体';
  static const agentDelete = '删除智能体';
  static const agentDeleteConfirm = '确定要删除这个智能体吗？删除后无法恢复。';
  static const agentName = '名称';
  static const agentNameHint = '2-12个字符';
  static const agentBio = '简介';
  static const agentPersonality = '性格';
  static const agentSpeakingStyle = '口吻';
  static const agentExpertise = '特长';
  static const agentConstraints = '禁止事项';
  static const agentAssignRoom = '指派到房间';
  static const agentLeaveRoom = '退出房间';
  static const agentPause = '暂停发言';
  static const agentResume = '恢复发言';
  static const agentMemories = '记忆';
  static const agentTemplates = '人格模板';
  static const agentStatusActive = '活跃';
  static const agentStatusPaused = '已暂停';
  static const agentCreateCost = '创建智能体将消耗 50 积分';

  // ============================================================
  // 话题 & 创作
  // ============================================================
  static const topicList = '创作话题';
  static const topicActive = '进行中';
  static const topicEnded = '已结束';
  static const topicClaim = '领取任务';
  static const topicArtworks = '作品';
  static const topicClaimConfirm = '领取任务将预扣积分，确定继续吗？';

  // ============================================================
  // 积分
  // ============================================================
  static const pointsBalance = '积分余额';
  static const pointsTransactions = '积分流水';
  static const pointsRecharge = '充值';
  static const pointsRechargeSuccess = '充值成功';
  static String pointsAmount(int amount) => '$amount 积分';

  // ============================================================
  // 通知
  // ============================================================
  static const notificationTitle = '通知中心';
  static const notificationEmpty = '暂无通知';
  static const notificationMarkAllRead = '全部已读';

  // ============================================================
  // 用户
  // ============================================================
  static const profileTitle = '个人中心';
  static const profileEdit = '编辑资料';
  static const profileSettings = '设置';
  static const profileSecurity = '账号安全';
  static const profileAbout = '关于';

  // ============================================================
  // 举报
  // ============================================================
  static const reportSubmit = '提交举报';
  static const reportReason = '举报原因';
  static const reportReasonHint = '请描述举报原因 (最多500字)';
  static const reportSuccess = '举报已提交，我们会尽快处理';

  // ============================================================
  // 空状态
  // ============================================================
  static const emptyDefault = '暂无内容';
  static const emptyConversation = '暂无会话';
  static const emptyAgent = '还没有智能体';
  static const emptyAgentSubtitle = '创建一个属于你的AI分身吧';
}
