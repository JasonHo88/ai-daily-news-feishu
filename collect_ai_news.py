#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI资讯收集脚本（多源 RSS 旗舰版）
聚合 36Kr, IT之家, 少数派, 极客公园, 虎嗅, AI News, TechCrunch
"""

import os
import sys
import re
from datetime import datetime
from typing import Dict, List
import requests
import feedparser
from deep_translator import GoogleTranslator

# --- 环境配置 ---
# 飞书 Webhook 地址从 GitHub Secrets 中读取
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', '')
TODAY = datetime.now().strftime("%Y年%m月%d日")

# 初始化翻译器 (英翻中)
translator = GoogleTranslator(source='auto', target='zh-CN')

class NewsEngine:
    def __init__(self):
        self.seen_titles = set()

    def translate(self, text: str) -> str:
        """在线翻译标题"""
        if not text: return ""
        try:
            return translator.translate(text)
        except:
            return text

    def is_dup(self, title: str) -> bool:
        """简易指纹去重逻辑"""
        clean = re.sub(r'[^\w\u4e00-\u9fa5]', '', title.lower())[:15]
        if not clean or clean in self.seen_titles:
            return True
        self.seen_titles.add(clean)
        return False

def fetch_domestic_rss(engine: NewsEngine) -> List[Dict]:
    """聚合国内科技媒体 RSS 源"""
    sources = [
        {"name": "36氪", "url": "https://36kr.com/feed-article"},
        {"name": "IT之家", "url": "https://www.ithome.com/rss/"},
        {"name": "少数派", "url": "https://sspai.com/feed"},
        {"name": "极客公园", "url": "http://www.geekpark.net/rss"},
        {"name": "虎嗅", "url": "https://www.huxiu.com/rss/0.xml"}
    ]
    results = []
    for src in sources:
        try:
            print(f"🇨🇳 同步中: {src['name']}")
            feed = feedparser.parse(src['url'])
            count = 0
            for entry in feed.entries:
                if count >= 3: break # 每个源精选3条
                if not engine.is_dup(entry.title):
                    results.append({"title": entry.title, "source": src['name'], "link": entry.link})
                    count += 1
        except Exception as e:
            print(f"⚠️ {src['name']} 暂时无法连接: {e}")
    return results

def fetch_overseas_rss(engine: NewsEngine) -> List[Dict]:
    """抓取海外源并自动翻译"""
    sources = [
        {"name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/"},
        {"name": "TechCrunch", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"}
    ]
    results = []
    for src in sources:
        try:
            print(f"🌐 翻译中: {src['name']}")
            feed = feedparser.parse(src['url'])
            for entry in feed.entries[:4]:
                if not engine.is_dup(entry.title):
                    results.append({
                        "title": engine.translate(entry.title),
                        "source": src['name'],
                        "link": entry.link
                    })
        except:
            pass
    return results

def main():
    engine = NewsEngine()
    print("🚀 正在收集全球 AI 情报...")
    
    domestic = fetch_domestic_rss(engine)
    overseas = fetch_overseas_rss(engine)
    
    if not domestic and not overseas:
        print("❌ 未获取到任何有效资讯")
        return

    # 构造飞书 Markdown 内容
    report = f"# 🤖 全球 AI 科技日报 - {TODAY}\n\n"
    
    report += "## 🌏 海外前沿 (智能翻译)\n\n"
    for i, n in enumerate(overseas[:8], 1):
        report += f"**{i}. {n['title']}**\n- 来源: {n['source']} | [原文链接]({n['link']})\n\n"
    
    report += "## 🇨🇳 国内动态 (多源聚合)\n\n"
    for i, n in enumerate(domestic[:10], 1):
        report += f"**{i}. {n['title']}**\n- 来源: {n['source']} | [阅读全文]({n['link']})\n\n"
    
    report += f"---\n*情报覆盖: 36Kr, IT之家, 少数派, 极客公园, 虎嗅, AI News, TechCrunch*"

    # 发送至飞书
    if FEISHU_WEBHOOK_URL:
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": f"🤖 AI科技情报 - {TODAY}"}, "template": "purple"},
                "elements": [{"tag": "markdown", "content": report}]
            }
        }
        res = requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=20)
        if res.status_code == 200:
            print("✅ 日报推送完成！")
        else:
            print(f"❌ 飞书接口报错: {res.text}")
    else:
        print("⚠️ 未配置 Webhook，仅打印预览:\n", report)

if __name__ == "__main__":
    main()
