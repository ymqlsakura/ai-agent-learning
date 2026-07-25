# QUICKSTART — 快速启动指南

> 给新会话的第一口饭。读完这个就能动手。详细上下文在 [HANDOFF.md](HANDOFF.md)。

## 环境

- **API**: DeepSeek, 端点 `https://api.deepseek.com`
- **SDK**: `openai` Python 包, `base_url` 改到 DeepSeek
- **模型**: `deepseek-v4-flash`（快+便宜）、`deepseek-v4-pro`（深度推理）
- **API Key**: 环境变量 `DEEPSEEK_API_KEY`
- ⚠️ 旧名 `deepseek-chat` / `deepseek-reasoner` 于 2026-07-24 废弃
- **成本**: 聊天分析 ~¥0.004/次, 长文本分片 ~¥0.01-0.02/次

## 三个工具

所有工具在 `stage-5-document-assistant/` 目录。

### 论文降重（最常用）

🆕 **三种输入方式**：

1. **拖拽运行**：把论文 `.txt`/`.docx`/`.pdf`/`.pptx` 文件拖到 `论文降重.bat` 图标上
2. **粘贴文字**：双击 `论文降重.bat`（或 `python 论文降重.py`），直接粘贴论文内容，Ctrl+Z 回车完成
3. **剪贴板**：`python 论文降重.py --clipboard` 从剪贴板读取

或者命令行：
```
python 论文降重.py 你的论文.txt               → 输出降重版 txt + HTML 对比报告
python 论文降重.py                             → 粘贴模式（无文件时自动进入）
python 论文降重.py --clipboard                 → 从剪贴板读取
```

支持 `.txt`、`.docx`（Word 文档）、`.pdf`（PDF）、`.pptx`（PPT）四种输入格式：
```
python 论文降重.py 论文.docx
python 论文降重.py 论文.pdf
```
⚠️ PDF 仅支持文字型（Word 另存为的 PDF），不支持扫描版（图片 PDF）

### 聊天分析

```
python chat_analyzer.py 你的聊天文件.txt     → 输出分析报告 HTML
```

### 文档总结

```
python doc_assistant.py 你的文档.txt          → 输出文档总结
```

## 🚨 铁律

- **所有代码和文件必须在 D 盘**——绝对不要碰 C 盘
- **永不新建空白文件**——从 chat_analyzer.py 或 doc_assistant.py 改起
- **改 prompt 要改两处**——一处代码、一处说明
- **Windows GBK 编码**——中文文件用 `encoding='utf-8'` 读
- **中文弯引号**会导致语法错误——用直引号 `""` 和 `''`

## 最快上手指南

1. 搜索并读取 `**/HANDOFF.md`、`memory/MEMORY.md` + 索引中每个 `.md` 文件
2. 读 [STATUS.md](STATUS.md) 了解当前状态和下一步计划
3. 开口对樱漫清澜说话
