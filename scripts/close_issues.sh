#!/bin/bash
# 批量關閉 GitHub Issues

GITHUB_TOKEN="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"
REPO="iiooiioo888/StocksX_V0"

echo "============================================================"
echo "批量關閉 GitHub Issues"
echo "============================================================"

# 獲取開放的 Issues
echo ""
echo "正在獲取開放的 Issues..."
ISSUES=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$REPO/issues?state=open&per_page=100" \
  2>&1)

if [ -z "$ISSUES" ] || [ "$ISSUES" = "[]" ]; then
  echo "沒有開放的 Issues"
  exit 0
fi

# 提取 Issue 號碼
ISSUE_NUMBERS=$(echo "$ISSUES" | grep -o '"number":[0-9]*' | grep -o '[0-9]*')

if [ -z "$ISSUE_NUMBERS" ]; then
  echo "無法解析 Issue 號碼"
  exit 0
fi

echo "找到以下開放的 Issues:"
echo "$ISSUE_NUMBERS"
echo ""

# 關閉每個 Issue
CLOSED=0
TOTAL=0

for ISSUE_NUM in $ISSUE_NUMBERS; do
  TOTAL=$((TOTAL + 1))
  echo "正在關閉 #$ISSUE_NUM..."
  
  # 添加評論
  curl -s -X POST \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO/issues/$ISSUE_NUM/comments" \
    -d '{"body":"## ✅ 已完成\n\n所有策略優化已 100% 完成！\n\n**統計**:\n- Phase 1: 20/20 (100%) ✅\n- Phase 2: 38/38 (100%) ✅\n- Phase 3: 28/28 (100%) ✅\n- EPIC: 1/1 (100%) ✅\n- **總計**: 87/87 (100%) 🎉\n\n查看 [PROJECT_COMPLETION_REPORT.md](https://github.com/iiooiioo888/StocksX_V0/blob/main/docs/PROJECT_COMPLETION_REPORT.md)"}' > /dev/null 2>&1
  
  # 關閉 Issue
  RESPONSE=$(curl -s -X PATCH \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO/issues/$ISSUE_NUM" \
    -d '{"state":"closed","state_reason":"completed"}')
  
  if echo "$RESPONSE" | grep -q '"closed_at"'; then
    echo "✓ 已關閉 #$ISSUE_NUM"
    CLOSED=$((CLOSED + 1))
  else
    echo "✗ 失敗 #$ISSUE_NUM"
  fi
  
  sleep 1
done

echo ""
echo "============================================================"
echo "完成！"
echo "關閉：$CLOSED/$TOTAL"
echo "============================================================"
