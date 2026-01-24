#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions AI资讯日报项目

这是一个使用GitHub Actions自动收集AI资讯并推送到飞书的项目。

## 功能特性

- 🤖 自动收集海外和国内的AI热点资讯
- 📊 整理成结构化的日报格式
- 📤 每天自动推送到飞书群组
- 🔄 支持手动触发执行

## 快速开始

### 1. Fork本项目

点击GitHub页面右上角的"Fork"按钮创建您自己的仓库。

### 2. 配置飞书Webhook

在GitHub仓库中配置密钥：

1. 进入仓库的 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加以下密钥：
   - **Name**: `FEISHU_WEBHOOK_URL`
   - **Value**: 您的飞书机器人Webhook地址

获取飞书Webhook地址：
1. 在飞书群组中添加自定义机器人
2. 复制Webhook地址（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxx`）
3. 在GitHub Secrets中配置

### 3. 手动测试

在GitHub Actions页面：
1. 进入 **Actions** 标签
2. 选择 "AI资讯日报自动收集" 工作流
3. 点击 **Run workflow** → **Run workflow**

## 项目结构

```
ai-daily-news/
├── .github/
│   └── workflows/
│       └── ai-daily-report.yml    # GitHub Actions工作流配置
├── collect_ai_news.py              # AI资讯收集脚本
├── push_to_feishu.py               # 飞书推送脚本
├── requirements.txt                # Python依赖
├── README.md                       # 项目说明
└── .gitignore                      # Git忽略文件
```

## 配置说明

### 定时任务设置

工作流文件：`.github/workflows/ai-daily-report.yml`

默认触发时间：每天UTC 0点（北京时间8:00）

修改触发时间：
```yaml
schedule:
  - cron: '0 0 * * *'  # UTC时间
```

时区转换：
- UTC 0:00 = 北京时间 8:00
- UTC 12:00 = 北京时间 20:00
- UTC 16:00 = 北京时间 24:00

### 手动触发

工作流支持手动触发：
1. 进入GitHub Actions页面
2. 点击 "AI资讯日报自动收集"
3. 点击 "Run workflow" 按钮
4. 可选择"调试模式"输出更多信息

## 依赖说明

### Python依赖

```
requests>=2.28.0
python-dotenv>=1.0.0
```

安装命令：
```bash
pip install -r requirements.txt
```

### GitHub Secrets

| 密钥名称 | 必需 | 说明 |
|---------|------|------|
| `FEISHU_WEBHOOK_URL` | ✅ | 飞书机器人Webhook地址 |

## 运行日志

### GitHub Actions日志

每次执行都会生成详细日志：
- 📥 代码检出
- 🐍 Python环境设置
- 📦 依赖安装
- 🤖 AI资讯收集
- 📤 推送到飞书

### 本地运行日志

运行日志保存在：
```
AI日报_YYYY-MM-DD.md
```

## 常见问题

### Q1: 推送失败怎么办？

1. 检查Secrets中的Webhook地址是否正确
2. 确认飞书机器人仍在群组中
3. 查看GitHub Actions日志中的错误信息

### Q2: 如何修改收集的资讯源？

编辑 `collect_ai_news.py` 文件：
```python
def search_twitter_ai_news():
    # 添加自定义的资讯源

def search_domestic_ai_news():
    # 添加自定义的国内资讯源
```

### Q3: 可以自定义日报格式吗？

可以！修改 `generate_daily_report()` 函数：
```python
def generate_daily_report(overseas_news: List[Dict], domestic_news: List[Dict]) -> str:
    # 自定义您需要的日报格式
```

### Q4: 触发时间不对？

检查cron表达式：
```yaml
schedule:
  - cron: '分 时 日 月 周'
  # 示例：每天8点(UTC)
  - cron: '0 0 * * *'
```

时区转换工具：https://crontab.guru/

### Q5: GitHub Actions用完怎么办？

免费额度：
- Linux: 每月 2,000 分钟
- Windows: 每月 1,000 分钟

一般使用量：每次执行约 2-5 分钟，足够使用。

## 自定义配置

### 添加更多资讯源

```python
# 在 collect_ai_news.py 中添加
def search_custom_source() -> List[Dict]:
    """自定义资讯源"""
    # 实现逻辑
    return []
```

### 添加通知渠道

```python
# 发送邮件通知
def send_email_notification():
    pass

# 发送Slack通知
def send_slack_notification():
    pass
```

### 修改日报模板

```python
# 在 generate_daily_report() 中修改
report = f"""# 您的自定义标题

## 您的自定义内容

...
"""
```

## 最佳实践

1. **定期检查**：每周查看执行记录
2. **优化来源**：根据需求调整资讯源
3. **备份配置**：保存Webhook地址的副本
4. **监控执行**：开启邮件通知（GitHub Pro）

## 进阶功能

- 📊 数据分析：统计资讯趋势
- 🔍 关键词过滤：自定义过滤规则
- 🏷️ 自动标签：按类别分类资讯
- 📈 可视化：生成统计图表
- 🌐 多语言：支持中英文日报

## 贡献指南

欢迎贡献代码：
1. Fork本项目
2. 创建分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -am 'Add xxx'`)
4. 推送到分支 (`git push origin feature/xxx`)
5. 创建Pull Request

## 许可证

MIT License - 欢迎使用和修改！

## 联系与支持

- 📧 问题反馈：GitHub Issues
- 📖 文档：查看README和Wiki
- 💬 讨论：GitHub Discussions

---

** Made with ❤️ by Matrix Agent **
** 让AI资讯获取更简单！ **
