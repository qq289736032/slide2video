---
name: slide2video
description: 将 Marp Markdown 幻灯片转换为带语音旁白、逐句字幕和水印的教学视频。无需 API Key。使用场景：用户要求生成视频、markdown 转视频、幻灯片转视频、slide to video、make video、ppt 转视频。
license: MIT
compatibility: Requires ffmpeg, marp-cli, edge-tts (Python).
metadata:
  author: slide2video
  version: "1.0"
  triggers: "生成视频,markdown转视频,幻灯片转视频,slide to video,make video,ppt转视频"
---

# Slide Video Skill

将 Marp 格式 Markdown 幻灯片（含 `::: notes` 旁白脚本）转换为带语音旁白、逐句字幕和水印的教学视频。无需 API Key，完全免费。

所有脚本位于本 skill 目录下的 `scripts/` 子目录。下文中 `{SKILL_DIR}` 表示本 SKILL.md 所在目录的绝对路径，agent 执行时需替换为实际路径。

## 前置依赖

执行任何操作前，先检查依赖是否就绪：

```bash
ffmpeg -version    # 未安装: brew install ffmpeg
marp --version     # 未安装: npm install -g @marp-team/marp-cli
python3 -c "import edge_tts"  # 未安装: pip install edge-tts
```

如果用户环境缺少依赖，引导用户安装后再继续。

## Agent 执行指引

### 场景 1：用户提供了 Markdown 文件，要求生成视频

一键执行：

```bash
python3 {SKILL_DIR}/scripts/run.py <input.md> -o <output.mp4>
```

常用可选参数：
- `--voice zh-CN-XiaoxiaoNeural` — 切换语音
- `--watermark "@频道名"` — 添加水印
- `--theme dark-blue` — 使用内置主题（见主题列表）
- `--no-subtitle` — 不烧录字幕
- `--keep-temp` — 保留中间文件（调试用）

执行完成后，告知用户视频路径和 SRT 字幕路径。

### 场景 2：用户要求编写 Markdown 幻灯片内容

帮用户创建符合本 skill 输入格式的 Markdown 文件。模板：

```markdown
---
marp: true
theme: default
voice: zh-CN-YunxiNeural
watermark_text: "@频道名"
---

# 页面标题

- 要点内容

::: notes
讲解旁白，不会显示在幻灯片上。
会被转成语音和逐句字幕。
:::

---

# 下一页

更多内容...

::: notes
下一页的讲解旁白。
:::
```

关键规则：
- 用 `---` 分隔每页幻灯片
- 旁白写在 `::: notes` 和 `:::` 之间
- 旁白是"讲解稿"，不是照搬幻灯片文字，应该口语化、有过渡
- 每页旁白建议 2-5 句话，太长会导致单页视频时间过长

### 场景 3：用户想分步执行或调试

按顺序执行以下四步：

```bash
# Step 1: 预处理（解析旁白 + 生成干净版 Markdown）
python3 {SKILL_DIR}/scripts/prepare.py <input.md> -o notes.json

# Step 2: 用干净版渲染幻灯片图片（注意用 _clean.md，不是原文件）
marp --images png <input_name>_clean.md -o slides/slide.png
# 如需使用主题：marp --theme {SKILL_DIR}/themes/dark-blue.css --images png ...

# Step 3: 生成语音音频
python3 {SKILL_DIR}/scripts/generate_audio.py notes.json -o audio/

# Step 4: 合成视频
python3 {SKILL_DIR}/scripts/compose_video.py slides/ audio/ -o output.mp4 --notes notes.json
```

每步执行后可检查中间产物：
- `notes.json` — 确认旁白解析是否正确
- `*_clean.md` — 确认幻灯片内容无旁白文字
- `slides/*.png` — 确认幻灯片渲染效果
- `audio/*.mp3` — 试听语音效果

### 场景 4：用户想调整字幕或水印样式

引导用户在 Markdown frontmatter 中添加配置，或通过命令行参数覆盖。

字幕参数（frontmatter 中以 `subtitle_` 前缀）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `subtitle_font` | PingFang SC | 字体 |
| `subtitle_fontsize` | 48 | 字号 |
| `subtitle_color` | `&H20FFFFFF` | 颜色（ASS &HAABBGGRR，白色半透明） |
| `subtitle_outline_color` | `&H60000000` | 描边色（黑色半透明） |
| `subtitle_outline` | 2 | 描边粗细 |
| `subtitle_margin_v` | 60 | 底部边距 |

水印参数（frontmatter 中以 `watermark_` 前缀）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `watermark_text` | （空） | 水印文字 |
| `watermark_opacity` | 0.15 | 透明度 0.0-1.0 |
| `watermark_position` | top_right | 位置：top_right/top_left/bottom_right/bottom_left |
| `watermark_fontsize` | 28 | 字号 |
| `watermark_color` | white | 颜色 |

配置优先级：代码默认值 → frontmatter → 命令行参数。

### 场景 5：用户想选择或切换主题

内置 10 套主题，覆盖 5 大场景。通过 `--theme` 参数指定主题名即可：

```bash
python3 {SKILL_DIR}/scripts/run.py input.md -o output.mp4 --theme cyber-dark
```

也可以指定自定义 CSS 文件路径：

```bash
python3 {SKILL_DIR}/scripts/run.py input.md -o output.mp4 --theme /path/to/custom.css
```

## 内置主题

| 系列 | 主题名 | 风格 | 适用场景 |
|------|--------|------|----------|
| 商务 | `dark-blue` | 深蓝渐变，白字 | 汇报、演讲 |
| 商务 | `steel-blue` | 钢蓝渐变，冷静理性 | 数据报告 |
| 科技 | `dark-keynote` | 纯黑，苹果风 | 产品发布 |
| 科技 | `cyber-dark` | 黑底青光，径向渐变 | 技术分享、开发者 |
| 教育 | `clean-white` | 白底蓝色点缀 | 培训、日常 |
| 教育 | `warm-sand` | 暖沙色，柔和 | 长时间阅读 |
| 创意 | `gradient-purple` | 紫粉渐变 | 营销、年轻化 |
| 创意 | `sunset-gradient` | 日落粉橙渐变 | 自媒体、Vlog |
| 学术 | `minimal-academic` | 纯白极简，衬线字体 | 论文答辩 |
| 学术 | `latex-beamer` | 白底蓝色导航条 | 学术报告 |

主题文件位于 `{SKILL_DIR}/themes/` 目录下。

## 常用语音

| Voice | 性别 | 风格 | 语言 |
|-------|------|------|------|
| `zh-CN-YunxiNeural` | 男 | 自然叙述 | 中文 |
| `zh-CN-XiaoxiaoNeural` | 女 | 温暖亲切 | 中文 |
| `zh-CN-YunjianNeural` | 男 | 新闻播报 | 中文 |
| `en-US-GuyNeural` | 男 | 自然 | 英文 |
| `en-US-JennyNeural` | 女 | 自然 | 英文 |

## 输出

| 文件 | 说明 |
|------|------|
| `output.mp4` | 视频，1920x1080，H.264+AAC，30fps，含硬字幕和水印 |
| `output.srt` | SRT 字幕文件，逐句时间轴 |

## 目录结构

```
slide2video/                ← 整个目录拷贝即可使用
├── SKILL.md                ← 本文件，skill 入口
├── scripts/
│   ├── run.py              ← 一键 pipeline
│   ├── prepare.py          ← 预处理：解析 notes + 生成 clean .md
│   ├── generate_audio.py   ← edge-tts 语音合成
│   ├── compose_video.py    ← ffmpeg 视频合成 + 字幕 + 水印
│   ├── subtitle.py         ← 字幕生成（SRT/ASS）
│   ├── config.py           ← 集中配置
│   └── requirements.txt    ← Python 依赖
├── themes/                 ← 10 套内置 Marp CSS 主题
│   ├── dark-blue.css
│   ├── steel-blue.css
│   ├── dark-keynote.css
│   ├── cyber-dark.css
│   ├── clean-white.css
│   ├── warm-sand.css
│   ├── gradient-purple.css
│   ├── sunset-gradient.css
│   ├── minimal-academic.css
│   └── latex-beamer.css
└── example/
    └── demo.md             ← 示例文件
```

## 安装方式

将整个 `slide2video/` 目录拷贝到你的 agent skills 目录下：

- Kiro: `.kiro/skills/slide2video/` 或 `~/.kiro/skills/slide2video/`
- Claude: `.claude/skills/slide2video/`
- 其他 agent: 按该 agent 的 skill 目录规范放置

然后安装系统依赖：

```bash
brew install ffmpeg
npm install -g @marp-team/marp-cli
pip install edge-tts
```

## 限制

- 需要网络连接（edge-tts 依赖微软在线 TTS 服务）
- 字幕时间轴按字数比例分配，非精确语音对齐
- 页间无过渡动画（硬切）
- 不支持同一文件内不同页使用不同语音
