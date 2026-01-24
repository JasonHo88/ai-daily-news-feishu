#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI资讯收集脚本（多源+全中文修复版）
1. 自动翻译海外资讯为中文
2. 修复并增强国内抓取源
3. 聚合去重与飞书推送
"""

import os
import sys
import re
from datetime import datetime
from typing import Dict, List

# 自动安装必要库
def install_dependencies():
    needed = ['requests', 'beautifulsoup4', 'feedparser', 'deep-translator']
    for lib in needed:
        try:
            if lib == 'beautifulsoup4': __import__('bs4')
            elif lib == 'deep-translator': __import__('deep_translator')
            else: __import__(lib)
        except ImportError:
            print(f"❌ 缺少 {lib}，正在安装...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", lib, "-q"])

install_dependencies()

import requests
from bs4 import BeautifulSoup
import feedparser
from deep_translator import GoogleTranslator

# --- 配置区 ---
FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL', '')
TODAY = datetime.now().strftime("%Y年%m月%d日")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 初始化翻译器
translator = GoogleTranslator(source='auto', target='zh-CN')

# --- 辅助功能 ---
class ContentProcessor:
    def __init__(self):
        self.seen_titles = set()

    def translate(self, text: str) -> str:
        """自动翻译为中文"""
        if not text: return ""
        try:
            return translator.translate(text)
        except Exception as e:
            print(f"⚠️ 翻译失败: {e}")
            return text

    def is_duplicate(self, title: str) -> bool:
        clean_title = re.sub(r'[^\w\u4e00-\u9fa5]', '', title.lower())
        fingerprint = clean_title[:15]
        if fingerprint in self.seen_titles: return True
        self.seen_titles.add(fingerprint)
        return False

# --- 抓取逻辑 ---

def fetch_overseas_v3(processor: ContentProcessor) -> List[Dict]:
    """抓取海外源并翻译"""
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
                if processor.is_duplicate(raw_title): continue
                
                # 执行翻译
                zh_title = processor.translate(raw_title)
                results.append({
                    "title": zh_title,
                    "source": s['name'],
                    "link": entry.link
                })
        except Exception as e:
            print(f"⚠️ 海外源 {s['name']} 异常: {e}")
    return results

def fetch_domestic_v3(processor: ContentProcessor) -> List[Dict]:
    """修复国内抓取逻辑"""
    results = []
    # 策略：如果 36Kr 失败，自动尝试 IT之家
    try:
        print("🇨🇳 正在尝试 36Kr...")
        res = requests.get("https://36kr.com/information/ai/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 兼容多种可能的 36Kr 标题类名
        items = soup.find_all('a', class_=re.compile(r'article-item-title|weight'))
        for item in items[:10]:
            title = item.get_text(strip=True)
            if title and not processor.is_duplicate(title):
                link = item['href'] if item['href'].startswith('http') else f"https://36kr.com{item['href']}"
                results.append({"title": title, "source": "36氪", "link": link})
    except Exception as e:
        print(f"⚠️ 36Kr 解析失败: {e}")

    try:
        print("🇨🇳 正在尝试 IT之家...")
        res = requests.get("https://www.ithome.com/tag/ai", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.news-item .title')
        for item in items[:8]:
            title = item.get_text(strip=True)
            if title and not processor.is_duplicate(title):
                results.append({"title": title, "source": "IT之家", "link": item['href']})
    except Exception as e:
        print(f"⚠️ IT之家 解析失败: {e}")
        
    return results

# --- 主程序 ---

def main():
    processor = ContentProcessor()
    
    overseas = fetch_overseas_v3(processor)
    domestic = fetch_domestic_v3(processor)
    
    if not overseas and not domestic:
        print("❌ 未获取到任何有效数据，请检查网络或 Secret 配置。")
        return

    # 构造飞书卡片内容
    report = f"# 🤖 AI 全网聚合日报 - {TODAY}\n\n"
    
    report += "## 📰 海外热点 (已翻译)\n\n"
    for i, n in enumerate(overseas[:6], 1):
        report += f"**{i}. {n['title']}**\n- 来源: {n['source']} | [查看详情]({n['link']})\n\n"
    
    report += "## 🇨🇳 国内动态\n\n"
    if not domestic:
        report += "_⚠️ 国内资讯抓取暂时受限，正在修复中_\n\n"
    for i, n in enumerate(domestic[:6], 1):
        report += f"**{i}. {n['title']}**\n- 来源: {n['source']} | [查看详情]({n['link']})\n\n"
    
    report += f"---\n*Matrix Agent 智能聚合翻译版 | {TODAY}*"

    # 推送逻辑
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": f"🤖 AI日报 (全中文版) - {TODAY}"}, "template": "blue"},
            "elements": [{"tag": "markdown", "content": report}]
        }
    }
    
    if FEISHU_WEBHOOK_URL:
        requests.post(FEISHU_WEBHOOK_URL, json=payload, timeout=20)
        print("✅ 全中文日报推送完成！")
    else:
        print("⚠️ 未发现 Webhook 地址，无法推送。")

if __name__ == "__main__":
    main()
