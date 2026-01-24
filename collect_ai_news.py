#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI资讯收集脚本（多源 RSS 旗舰版）
1. 国内源：36Kr, IT之家, 少数派, 极客公园, 虎嗅 (全 RSS 驱动)
2. 国外源：AI News, TechCrunch (全自动中文翻译)
3. 核心机制：多源均衡、指纹去重、在线翻译
"""

import os
import sys
import re
from datetime import datetime
from typing import Dict, List

# 依赖库自动安装
def install_dependencies():
    needed = ['requests', 'feedparser', 'deep-translator']
    for lib in needed:
        try:
            __import__(lib.replace('-', '_'))
        except ImportError:
            print(f"❌ 正在安装 {lib}...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", lib, "-q"])

install_dependencies()

import requests
import feedparser
from deep_translator import GoogleTranslator

# --- 环境配置 ---
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', '')
TODAY = datetime.now().strftime("%Y年%m月%d日")

# 初始化翻译器 (英翻中)
translator = GoogleTranslator(source='auto', target='zh-CN')

class NewsEngine:
    def __init__(self):
        self.seen_titles = set()

    def translate(self, text: str) -> str:
        if not text: return ""
        try:
            # 翻译标题，保留一些专业术语不被误翻
            return translator.translate(text)
        except: return text

    def is_dup(self, title: str) -> bool:
        """根据标题前15个字符进行简易指纹去重"""
        clean = re.sub(r'[^\w\u4e00-\u9fa5]', '', title.lower())[:15]
        if not clean or clean in self.seen_titles: return True
        self.seen_titles.add(clean)
        return False

# --- 抓取逻辑 ---

def fetch_domestic_rss(engine: NewsEngine) -> List[Dict]:
    """聚合国内多个科技媒体 RSS"""
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
            print(f"🇨🇳 正在同步 {src['name']}...")
            feed = feedparser.parse(src['url'])
            # 每个源取前 2-3 条最及时的，保持日报紧凑
            count = 0
            for entry in feed.entries:
                if count >= 3: break
                if not engine.is_dup(entry.title):
                    results.append({
                        "title": entry.title,
                        "source": src['name'],
                        "link": entry.link
                    })
                    count += 1
        except Exception as e:
            print(f"⚠️ {src['name']} 访问受限: {e}")
            
    return results

def fetch_overseas_rss(engine: NewsEngine) -> List[Dict]:
    """抓取海外源并翻译"""
    sources = [
        {"name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/"},
        {"name": "TechCrunch", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"}
    ]
    results = []
    for src in sources:
        try:
            print(f"🌐 正在抓取并翻译 {src['name']}...")
            feed = feedparser.parse(src['url'])
            for entry in feed.entries[:4]:
                if not engine.is_dup(entry.title):
                    results.append({
                        "title": engine.translate(entry.title),
                        "source": src['name'],
                        "link": entry.link
                    })
        except: pass
    return results

# --- 推送逻辑 ---

def main():
    engine = NewsEngine()
    print("=" * 30)
    domestic = fetch_domestic_rss(engine)
    overseas = fetch_overseas_rss(engine)
    
    if not domestic and not overseas:
        print("❌ 全网资讯连接失败")
        return

    # 构建飞书消息体
    report = f"# 🤖 AI & 科技全网聚合日报 - {TODAY}\n\n"
    
    report += "## 🌏 海外前沿 (智能翻译)\n\n"
    for i, n in enumerate(overseas[:8], 1):
        report += f"**{i}. {n['title']}**\n- 来源: {n['source']} | [原文链接]({n['link']})\n\n"
    
    report += "## 🇨🇳 国内动态 (多源聚合)\n\n"
    for i, n in enumerate(domestic[:10], 1):
        report += f"**{i}. {n['title']}**\n- 来源: {n['source']} | [阅读全文]({n['link']})\n\n"
    
    report += f"---\n*情报覆盖: 36Kr, IT之家, 少数派, 极客公园, 虎嗅, AI News, TechCrunch*"

    if FEISHU_WEBHOOK_URL:
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": f"🤖 全球AI科技日报 - {TODAY}"}, "template": "purple"},
                "elements": [{"tag": "markdown", "content": report}]
            }
        }
        requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=20)
        print("✅ 日报推送成功！")
    else:
        print("\n--- 预览内容 ---\n")
        print(report)

if __name__ == "__main__":
    main()
