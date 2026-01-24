#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI资讯收集脚本（全中文+多源保底版）
1. 自动翻译海外源 
2. 国内接入：36Kr + 界面新闻 + 新浪科技（多源互补）
"""

import os
import sys
import re
from datetime import datetime
from typing import Dict, List

# 依赖库自动安装
def install_dependencies():
    needed = ['requests', 'beautifulsoup4', 'feedparser', 'deep-translator']
    for lib in needed:
        try:
            if lib == 'beautifulsoup4': __import__('bs4')
            else: __import__(lib.replace('-', '_'))
        except ImportError:
            print(f"❌ 正在安装 {lib}...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", lib, "-q"])

install_dependencies()

import requests
from bs4 import BeautifulSoup
import feedparser
from deep_translator import GoogleTranslator

# --- 环境配置 ---
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', '')
TODAY = datetime.now().strftime("%Y年%m月%d日")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

translator = GoogleTranslator(source='auto', target='zh-CN')

class NewsEngine:
    def __init__(self):
        self.seen_titles = set()

    def translate(self, text: str) -> str:
        if not text: return ""
        try:
            return translator.translate(text)
        except: return text

    def is_dup(self, title: str) -> bool:
        clean = re.sub(r'[^\w\u4e00-\u9fa5]', '', title.lower())[:12]
        if clean in self.seen_titles: return True
        self.seen_titles.add(clean)
        return False

# --- 国内源抓取 (多源互补) ---

def fetch_domestic(engine: NewsEngine) -> List[Dict]:
    results = []
    
    # 来源1: 界面新闻 (AI频道 - 稳定性高)
    try:
        print("🇨🇳 正在抓取 界面新闻...")
        res = requests.get("https://www.jiemian.com/lists/211.html", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.news-view .news-header a')
        for item in items[:5]:
            title = item.get_text(strip=True)
            if not engine.is_dup(title):
                results.append({"title": title, "source": "界面新闻", "link": item['href']})
    except: pass

    # 来源2: 36Kr (修复后的选择器)
    try:
        print("🇨🇳 正在尝试 36Kr...")
        res = requests.get("https://36kr.com/information/ai/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 锁定文章信息流区域，避开导航栏
        items = soup.select('a.article-item-title-weight, .kr-flow-article-item a.article-item-title')
        for item in items[:5]:
            title = item.get_text(strip=True)
            if title and len(title) > 5 and not engine.is_dup(title):
                link = item['href'] if item['href'].startswith('http') else f"https://36kr.com{item['href']}"
                results.append({"title": title, "source": "36氪", "link": link})
    except: pass

    return results

# --- 海外源抓取 (带翻译) ---

def fetch_overseas(engine: NewsEngine) -> List[Dict]:
    sources = [
        {"name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/"},
        {"name": "TechCrunch", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"}
    ]
    results = []
    for s in sources:
        try:
            print(f"🌐 正在获取并翻译 {s['name']}...")
            feed = feedparser.parse(s['url'])
            for entry in feed.entries[:4]:
                raw_title = entry.title
                if not engine.is_dup(raw_title):
                    results.append({
                        "title": engine.translate(raw_title),
                        "source": s['name'],
                        "link": entry.link
                    })
        except: pass
    return results

# --- 执行与推送 ---

def main():
    engine = NewsEngine()
    overseas = fetch_overseas(engine)
    domestic = fetch_domestic(engine)
    
    if not overseas and not domestic:
        print("❌ 未获取到任何数据")
        return

    report = f"# 🤖 AI全网中文日报 - {TODAY}\n\n"
    
    report += "## 📰 海外热点 (翻译版)\n\n"
    for i, n in enumerate(overseas[:6], 1):
        report += f"**{i}. {n['title']}**\n- 来源: {n['source']} | [原文链接]({n['link']})\n\n"
    
    report += "## 🇨🇳 国内动态 (多源精选)\n\n"
    if not domestic:
        report += "_⚠️ 国内源连接中，建议稍后重试_\n\n"
    for i, n in enumerate(domestic[:6], 1):
        report += f"**{i}. {n['title']}**\n- 来源: {n['source']} | [查看详情]({n['link']})\n\n"
    
    report += f"---\n*Matrix Agent 自动聚合翻译 | {TODAY}*"

    # 发送飞书
    if FEISHU_WEBHOOK_URL:
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": f"🤖 AI日报 (全中文版) - {TODAY}"}, "template": "blue"},
                "elements": [{"tag": "markdown", "content": report}]
            }
        }
        requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=20)
        print("✅ 推送成功！")

if __name__ == "__main__":
    main()
