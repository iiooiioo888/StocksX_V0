#!/bin/bash
# GitHub 推送脚本

echo "========================================"
echo "StocksX_V0 - GitHub 推送脚本"
echo "========================================"
echo ""

# 检查 Git 状态
echo "📊 检查 Git 状态..."
git status --short
echo ""

# 显示最近的提交
echo "📝 最近的提交:"
git log --oneline -5
echo ""

# 推送
echo "🚀 推送到 GitHub..."
echo "提示：如果推送失败，请使用以下命令："
echo "  git push https://YOUR_GITHUB_TOKEN@github.com/iiooiioo888/StocksX_V0.git main"
echo ""

# 尝试推送
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功!"
    echo "查看提交：https://github.com/iiooiioo888/StocksX_V0/commits/main"
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "解决方法:"
    echo "1. 生成 GitHub Personal Access Token:"
    echo "   https://github.com/settings/tokens"
    echo ""
    echo "2. 使用 token 推送:"
    echo "   git push https://YOUR_TOKEN@github.com/iiooiioo888/StocksX_V0.git main"
    echo ""
    echo "或者配置 SSH 密钥后使用:"
    echo "   git remote set-url origin git@github.com:iiooiioo888/StocksX_V0.git"
    echo "   git push origin main"
fi
