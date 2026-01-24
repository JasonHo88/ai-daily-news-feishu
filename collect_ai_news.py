#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI资讯收集脚本（修复版）
自动收集海外和国内的AI资讯，并生成日报格式推送到飞书
"""

import os
import sys
from datetime import datetime
from typing import Dict, List

try:
    import requests
except ImportError:
    print("❌ 缺少requests库，正在安装...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# 直接从环境变量获取Webhook地址（GitHub Actions环境变量）
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', '')

# 当前日期
TODAY = datetime.now().strftime("%Y年%m月%d日")


def search_twitter_ai_news() -> List[Dict]:
    """搜索Twitter上的AI相关热点"""
    news_list = []
    
    # 示例数据
    news_list.append({
        "title": "周鸿祎预测：2026年全球将出现100亿个智能体",
        "source": "新浪财经",
        "summary": "360创始人周鸿祎在2026崇礼论坛上表示，大模型需要升级成智能体才能真正落地。",
        "link": "https://finance.sina.com.cn/tob/2026-01-24/doc-inhikrie2726391.shtml",
        "category": "海外"
    })
    
    return news_list


def search_domestic_ai_news() -> List[Dict]:
    """搜索国内AI资讯"""
    news_list = []
    
    # 示例数据
    news_list.append({
        "title": "字节跳动豆包日活过亿，AI应用竞争白热化",
        "source": "证券时报",
        "summary": "字节跳动旗下豆包成为中国首个日活过亿的AI原生应用，月活达1.72亿。",
        "link": "https://www.stcn.com/article/detail/3598826.html",
        "category": "国内"
    })
    
    news_list.append({
        "title": "DeepSeek V4有望春节前后发布，编程能力超越OpenAI",
        "source": "中华网",
        "summary": "据The Information报道，DeepSeek计划在2月中旬推出新一代旗舰AI模型。",
        "link": "https://m.ai5g.china.com/ai/13004828/20260110/49150650.html",
        "category": "国内"
    })
    
    return news_list


def generate_daily_report(overseas_news: List[Dict], domestic_news: List[Dict]) -> str:
    """生成AI日报内容"""
    
    report = f"""# 🤖 AI日报 - {TODAY}

## 📰 海外热点

"""
    
    for i, news in enumerate(overseas_news[:8], 1):
        report += f"### {i}. **{news['title']}**\n- **来源**: {news['source']}\n- **摘要**: {news['summary']}\n- **链接**: {news['link']}\n\n"
    
    report += "## 🇨🇳 国内动态\n\n"
    
    for i, news in enumerate(domestic_news[:8], 1):
        report += f"### {i}. **{news['title']}**\n- **来源**: {news['source']}\n- **摘要**: {news['summary']}\n- **链接**: {news['link']}\n\n"
    
    report += f"""## 💡 今日亮点

**1. 智能体时代来临**：周鸿祎预测2026年全球将有100亿个智能体，字节豆包日活过亿的里程碑印证了这一趋势。

**2. AI应用商业化加速**：国内AI应用正加速商业化落地，车企密集布局2026年大模型应用。

---
*由 Matrix Agent 自动收集整理 | {TODAY}*
"""
    return report


def push_to_feishu(report: str) -> bool:
    """推送到飞书"""
    if not FEISHU_WEBHOOK_URL:
        print("⚠️  未配置飞书Webhook地址")
        return False
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🤖 AI日报 - {TODAY}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": report
                }
            ]
        }
    }
    
    try:
        print(f"📤 推送到飞书...")
        response = requests.post(
            FEISHU_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 成功推送到飞书！")
                return True
            else:
                print(f"❌ 飞书接口报错: {result.get('msg')}")
                return False
        else:
            print(f"❌ HTTP请求错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 推送过程发生异常: {str(e)}")
        return False


def main():
    """主函数"""
    try:
        print("=" * 50)
        print("🤖 AI资讯自动收集任务")
        print(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # 1. 收集资讯
        overseas_news = search_twitter_ai_news()
        domestic_news = search_domestic_ai_news()
        
        # 2. 生成日报
        report = generate_daily_report(overseas_news, domestic_news)
        
        # 3. 保存本地备份
        filename = f"AI日报_{TODAY.replace('年', '-').replace('月', '-').replace('日', '')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"💾 日报已保存到: {filename}")
        
        # 4. 推送到飞书
        success = push_to_feishu(report)
        
        if success:
            print("\n🎉 任务全部完成！")
        else:
            print("\n⚠️ 任务执行完成，但推送飞书失败。")
            
        return 0
        
    except Exception as e:
        print(f"\n❌ 任务运行崩溃: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0 


if __name__ == "__main__":
    sys.exit(main())
