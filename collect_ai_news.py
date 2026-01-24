#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI资讯收集脚本（多源聚合版）
聚合国内外多个权威源，支持自动去重与容错
"""

import os
import sys
import time
import re
from datetime import datetime
from typing import Dict, List

# 自动检查并安装必要的第三方库
def install_dependencies():
    needed = ['requests', 'beautifulsoup4', 'feedparser']
    for lib in needed:
        try:
            __import__(lib if lib != 'beautifulsoup4' else 'bs4')
        except ImportError:
            print(f"❌ 缺少 {lib} 库，正在自动安装...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", lib, "-q"])

install_dependencies()

import requests
from bs4 import BeautifulSoup
import feedparser

# --- 配置区 ---
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', '')
TODAY = datetime.now().strftime("%Y年%m月%d日")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# --- 辅助功能：去重 ---
class NewsDeleter:
    def __init__(self):
        self.seen_titles = set()

    def is_duplicate(self, title: str) -> bool:
        # 清洗标题（去空格、去符号）
        clean_title = re.sub(r'[^\w\u4e00-\u9fa5]', '', title.lower())
        # 取前15个字符做简易指纹匹配
        fingerprint = clean_title[:15]
        if fingerprint in self.seen_titles:
            return True
        self.seen_titles.add(fingerprint)
        return False

# --- 抓取逻辑 ---

def fetch_rss_news(source_name: str, url: str) -> List[Dict]:
    """通用的 RSS 抓取逻辑"""
    news = []
    try:
        print(f"🌐 正在抓取国外源: {source_name}...")
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            news.append({
                "title": entry.title,
                "source": source_name,
                "summary": entry.get('summary', '查看原文').split('<')[0][:80] + "...",
                "link": entry.link
            })
    except Exception as e:
        print(f"⚠️ {source_name} 抓取失败: {e}")
    return news

def fetch_36kr() -> List[Dict]:
    """抓取 36Kr AI 频道"""
    news = []
    try:
        print("🇨🇳 正在抓取国内源: 36氪...")
        res = requests.get("https://36kr.com/information/ai/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.article-item-title-weight')
        for item in items[:5]:
            news.append({
                "title": item.get_text(strip=True),
                "source": "36氪",
                "link": "https://36kr.com" + item['href']
            })
    except Exception as e:
        print(f"⚠️ 36Kr 抓取失败: {e}")
    return news

def fetch_ithome() -> List[Dict]:
    """抓取 IT之家 AI 标签"""
    news = []
    try:
        print("🇨🇳 正在抓取国内源: IT之家...")
        res = requests.get("https://www.ithome.com/tag/ai", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.news-item .title')
        for item in items[:5]:
            news.append({
                "title": item.get_text(strip=True),
                "source": "IT之家",
                "link": item['href']
            })
    except Exception as e:
        print(f"⚠️ IT之家 抓取失败: {e}")
    return news

# --- 主逻辑聚合 ---

def get_all_news():
    duplicator = NewsDeleter()
    
    # 1. 抓取海外（多源）
    overseas_sources = [
        {"name": "AI News", "url": "https://www.artificialintelligence-news.com/feed/"},
        {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
        {"name": "The Verge AI", "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"}
    ]
    all_overseas = []
    for s in overseas_sources:
        raw_news = fetch_rss_news(s['name'], s['url'])
        for n in raw_news:
            if not duplicator.is_duplicate(n['title']):
                all_overseas.append(n)
    
    # 2. 抓取国内（多源）
    all_domestic = []
    domestic_raw = fetch_36kr() + fetch_ithome()
    for n in domestic_raw:
        if not duplicator.is_duplicate(n['title']):
            all_domestic.append(n)
            
    return all_overseas[:8], all_domestic[:8] # 各自截取精选 8 条

def generate_daily_report(overseas: List[Dict], domestic: List[Dict]) -> str:
    report = f"# 🤖 AI 全网聚合日报 - {TODAY}\n\n"
    
    report += "## 📰 海外头条 (Multi-Source)\n\n"
    for i, n in enumerate(overseas, 1):
        report += f"### {i}. {n['title']}\n- 来源: {n['source']}\n- 链接: {n['link']}\n\n"
    
    report += "## 🇨🇳 国内动态 (Multi-Source)\n\n"
    for i, n in enumerate(domestic, 1):
        report += f"### {i}. {n['title']}\n- 来源: {n['source']}\n- 链接: {n['link']}\n\n"
    
    report += f"---\n*Matrix Agent 聚合检索 | 覆盖源: 36Kr, IT之家, TechCrunch, AI News, The Verge*"
    return report

def push_to_feishu(content: str):
    if not FEISHU_WEBHOOK_URL:
        print("⚠️ 未配置飞书 Webhook")
        return
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": f"🤖 AI多源日报 - {TODAY}"}, "template": "purple"},
            "elements": [{"tag": "markdown", "content": content}]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=20)

def main():
    print(f"🚀 启动多源情报抓取任务...")
    overseas, domestic = get_all_news()
    if not overseas and not domestic:
        print("❌ 未获取到任何资讯")
        return
    report = generate_daily_report(overseas, domestic)
    push_to_feishu(report)
    print("✅ 日报推送完成")

if __name__ == "__main__":
    main()
