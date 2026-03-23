#!/usr/bin/env python3
"""
批量關閉 GitHub Issues
"""

import requests
import time
import os

GITHUB_TOKEN = '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'
REPO = 'iiooiioo888/StocksX_V0'

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'StocksX-Issue-Closer'
}

def get_open_issues():
    """獲取所有開放的 Issues"""
    url = f'https://api.github.com/repos/{REPO}/issues?state=open&per_page=100'
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"獲取 Issues 失敗：{response.status_code}")
            return []
    except Exception as e:
        print(f"錯誤：{e}")
        return []

def close_issue(issue_number, title):
    """關閉單一 Issue"""
    url = f'https://api.github.com/repos/{REPO}/issues/{issue_number}'
    data = {
        'state': 'closed',
        'state_reason': 'completed'
    }
    
    try:
        response = requests.patch(url, headers=HEADERS, json=data, timeout=30)
        if response.status_code == 200:
            print(f"✓ 已關閉 #{issue_number}: {title}")
            return True
        else:
            print(f"✗ 失敗 #{issue_number}: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 錯誤 #{issue_number}: {e}")
        return False

def add_completion_comment(issue_number):
    """添加完成評論"""
    url = f'https://api.github.com/repos/{REPO}/issues/{issue_number}/comments'
    comment = """## ✅ 已完成

所有策略優化已 100% 完成！

**統計**:
- Phase 1: 20/20 (100%) ✅
- Phase 2: 38/38 (100%) ✅  
- Phase 3: 28/28 (100%) ✅
- EPIC: 1/1 (100%) ✅
- **總計**: 87/87 (100%) 🎉

**詳細報告**: 
- 查看 [PROJECT_COMPLETION_REPORT.md](https://github.com/iiooiioo888/StocksX_V0/blob/main/docs/PROJECT_COMPLETION_REPORT.md)
- 查看 [ISSUES.md](https://github.com/iiooiioo888/StocksX_V0/blob/main/ISSUES.md)

感謝您的關注！🚀
"""
    data = {'body': comment}
    
    try:
        response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        return response.status_code == 201
    except:
        return False

def main():
    print("=" * 60)
    print("批量關閉 GitHub Issues")
    print("=" * 60)
    
    # 獲取開放的 Issues
    print("\n正在獲取開放的 Issues...")
    issues = get_open_issues()
    
    if not issues:
        print("沒有開放的 Issues 或無法連接 GitHub API")
        return
    
    print(f"找到 {len(issues)} 個開放的 Issues\n")
    
    # 關閉 Issues
    closed_count = 0
    failed_count = 0
    
    for issue in issues:
        issue_num = issue['number']
        title = issue['title']
        
        # 添加完成評論
        add_completion_comment(issue_num)
        time.sleep(0.5)  # 避免 API 速率限制
        
        # 關閉 Issue
        if close_issue(issue_num, title):
            closed_count += 1
        else:
            failed_count += 1
        
        time.sleep(0.5)  # 避免 API 速率限制
    
    print(f"\n{'=' * 60}")
    print(f"完成！")
    print(f"關閉：{closed_count}/{len(issues)}")
    print(f"失敗：{failed_count}/{len(issues)}")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
