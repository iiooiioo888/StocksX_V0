#!/usr/bin/env python3
"""
使用 GitHub API 批量關閉 Issues
"""

import os
import requests
import time

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN environment variable is not set.")
    print("Usage: GITHUB_TOKEN=ghp_xxx python scripts/github_close_issues.py")
    exit(1)
REPO = "iiooiioo888/StocksX_V0"

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}


def get_open_issues(max_retries=3):
    """獲取所有開放的 Issues"""
    url = f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100"

    for attempt in range(max_retries):
        try:
            print(f"嘗試獲取 Issues ({attempt + 1}/{max_retries})...")
            response = requests.get(url, headers=HEADERS, timeout=30)
            print(f"HTTP 狀態碼：{response.status_code}")

            if response.status_code == 200:
                issues = response.json()
                print(f"✓ 成功獲取 {len(issues)} 個 Issues")
                return issues
            elif response.status_code == 401:
                print("✗ Token 無效")
                return []
            elif response.status_code == 403:
                print("✗ 速率限制")
                time.sleep(60)
            else:
                print(f"✗ 錯誤：{response.status_code}")
                time.sleep(5)
        except Exception as e:
            print(f"✗ 異常：{e}")
            time.sleep(5)

    return []


def close_issue(issue_num):
    """關閉單一 Issue"""
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}"
    data = {"state": "closed", "state_reason": "completed"}

    try:
        response = requests.patch(url, headers=HEADERS, json=data, timeout=30)
        if response.status_code == 200:
            print(f"✓ 已關閉 #{issue_num}")
            return True
        else:
            print(f"✗ 失敗 #{issue_num}: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 錯誤 #{issue_num}: {e}")
        return False


def add_comment(issue_num):
    """添加完成評論"""
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}/comments"
    comment = """## ✅ 已完成

所有策略優化已 100% 完成！

**統計**:
- Phase 1: 20/20 (100%) ✅
- Phase 2: 38/38 (100%) ✅
- Phase 3: 28/28 (100%) ✅
- EPIC: 1/1 (100%) ✅
- **總計**: 87/87 (100%) 🎉

查看 [PROJECT_COMPLETION_REPORT.md](https://github.com/iiooiioo888/StocksX_V0/blob/main/docs/PROJECT_COMPLETION_REPORT.md)
"""
    data = {"body": comment}

    try:
        response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        return response.status_code == 201
    except Exception as e:
        print(f"Error adding comment: {e}")
        return False


def main():
    print("=" * 60)
    print("GitHub Issues 批量關閉工具")
    print("=" * 60)
    print(f"Repo: {REPO}")
    print(f"Token: {GITHUB_TOKEN[:10]}...")
    print("=" * 60)

    # 獲取開放的 Issues
    issues = get_open_issues()

    if not issues:
        print("\n沒有開放的 Issues 或無法連接 GitHub API")
        print("請檢查：")
        print("1. 網絡連接")
        print("2. Token 是否有效")
        print("3. GitHub API 狀態")
        return

    print(f"\n找到 {len(issues)} 個開放的 Issues")
    print("\n開始關閉...")
    print("-" * 60)

    closed = 0
    failed = 0

    for issue in issues:
        num = issue["number"]
        title = issue["title"]

        print(f"\n處理 #{num}: {title}")

        # 添加評論
        if add_comment(num):
            print("  ✓ 已添加評論")
        time.sleep(1)

        # 關閉 Issue
        if close_issue(num):
            closed += 1
        else:
            failed += 1

        time.sleep(1)  # 避免速率限制

    print("\n" + "=" * 60)
    print("完成！")
    print(f"關閉：{closed}/{len(issues)}")
    print(f"失敗：{failed}/{len(issues)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
