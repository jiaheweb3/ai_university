#!/bin/bash
# AetherVerse — Docker Engine 安装脚本 (WSL2 Ubuntu)
# 重启后在 Ubuntu 终端执行: bash /mnt/c/projects/ai_university/infra/install-docker.sh

set -e

echo "=== 1. 安装 Docker Engine ==="
curl -fsSL https://get.docker.com | sh

echo "=== 2. 将当前用户加入 docker 组 ==="
sudo usermod -aG docker $USER

echo "=== 3. 配置 Docker 资源限制 (适配 8GB RAM) ==="
# 限制 WSL2 内存使用 — 写入 Windows 用户目录的 .wslconfig
WIN_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
WSLCONFIG="/mnt/c/Users/${WIN_USER}/.wslconfig"

if [ ! -f "$WSLCONFIG" ]; then
    cat > "$WSLCONFIG" << 'EOF'
[wsl2]
memory=2GB
processors=2
swap=1GB
EOF
    echo "已创建 $WSLCONFIG (限制 WSL 使用 2GB RAM)"
else
    echo "$WSLCONFIG 已存在，请手动检查 memory 配置"
fi

echo "=== 4. 启动 Docker ==="
sudo service docker start

echo "=== 5. 验证 Docker ==="
docker --version
docker run --rm hello-world

echo ""
echo "✅ Docker 安装完成!"
echo "💡 提示: 如果 docker 命令需要 sudo，请注销重登 WSL/关闭重开 WSL 终端"
echo "💡 WSL 内存限制需要: wsl --shutdown 后重新打开 Ubuntu 终端生效"
