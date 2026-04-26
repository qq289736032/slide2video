---
marp: true
theme: default
voice: zh-CN-YunxiNeural
silence_duration: 3
watermark_text: "@SlideVideo"
watermark_opacity: 0.15
subtitle_fontsize: 44
subtitle_color: "&H20FFFFFF"
subtitle_outline: 2
---

# Slide Video

**Markdown 一键生成教学视频**

- 轻量本地工具，无需 API Key
- 支持中英文语音合成
- 自动生成逐句字幕
- 可配置水印、字幕样式

::: notes
大家好，欢迎来到 Slide Video 的功能介绍。
这是一个轻量的本地工具，能把 Markdown 幻灯片一键转成带语音旁白的教学视频。
整个过程不需要任何 API Key，完全免费。
:::

---

# 工作流程

```
 demo.md → 解析 → 渲染 → 语音 → 合成 → output.mp4
```

1. 编写 Marp 格式 Markdown（含旁白脚本）
2. 解析 notes，生成干净版 Markdown
3. Marp CLI 渲染幻灯片为图片
4. edge-tts 生成语音音频
5. ffmpeg 合成最终视频

::: notes
整个工作流程分为五步。
首先，你编写一个 Marp 格式的 Markdown 文件，在里面用 notes 块写上讲解旁白。
然后工具会自动解析出旁白内容，同时生成一份去掉旁白的干净版 Markdown。
接着用 Marp 命令行工具把干净版渲染成幻灯片图片。
再用 edge-tts 把旁白文字转成语音音频。
最后用 ffmpeg 把图片、音频、字幕和水印合成为一个完整的 MP4 视频。
:::

---

# 输入格式

用 `---` 分页，`::: notes` 写旁白

- frontmatter 中设置 `marp: true` 和语音参数
- 每页用 `---` 分隔
- 旁白写在 `::: notes` 和 `:::` 之间
- 旁白不会显示在幻灯片画面上

::: notes
输入格式非常简单。
用三条横线分隔每一页幻灯片，用 notes 块来写讲解旁白。
旁白内容不会出现在幻灯片画面上，而是会被转成语音和字幕。
这个格式兼容 Marp 生态，你可以直接在 VS Code 里预览幻灯片效果。
:::

---

# 逐句字幕

字幕像电影一样一句一句出现

- 自动按句子拆分旁白文本
- 按字数比例分配时间轴
- 硬字幕烧录，适合上传自媒体平台
- 同时输出 SRT 文件备用

::: notes
字幕功能是一个亮点。
工具会自动把旁白按句子拆分，每句话单独显示，像电影字幕一样逐句出现。
字幕直接烧录到视频里，上传到 B站、抖音、YouTube 都能正常显示。
同时还会输出一份 SRT 字幕文件，方便你在其他平台使用。
:::

---

# 10 套主题

内置 10 套经典渐变主题

| 系列 | 主题 |
|------|------|
| 商务 | dark-blue、steel-blue |
| 科技 | dark-keynote、cyber-dark |
| 教育 | clean-white、warm-sand |
| 创意 | gradient-purple、sunset-gradient |
| 学术 | minimal-academic、latex-beamer |

::: notes
工具内置了十套经典主题，覆盖商务、科技、教育、创意和学术五大场景。
每个系列有两套风格可选，通过命令行参数一键切换。
所有主题都使用 CSS 渐变实现，不依赖外部图片，保持轻量。
:::

---

# 水印与样式

低调水印 + 可配置字幕

- 水印：右上角，透明度 15%
- 字幕：白色半透明，黑色描边
- 所有参数均可在 frontmatter 中配置

::: notes
水印功能可以帮你保护视频内容。
默认是右上角的文字水印，透明度只有百分之十五，非常低调。
字幕样式也完全可以自定义，字体、字号、颜色、描边都可以调整。
:::

---

# 语音选择

支持多种中英文语音

| 语音 | 性别 | 风格 |
|------|------|------|
| zh-CN-YunxiNeural | 男 | 自然叙述 |
| zh-CN-XiaoxiaoNeural | 女 | 温暖亲切 |
| en-US-GuyNeural | 男 | 英文旁白 |

::: notes
语音方面，工具使用微软的 edge-tts 引擎，支持多种中英文语音。
你只需要在 frontmatter 里指定 voice 参数就可以切换。
:::

---

# 快速开始

一条命令搞定

```bash
python run.py demo.md -o output.mp4 \
  --theme dark-blue \
  --watermark @MyChannel
```

::: notes
使用起来非常简单，一条命令就能完成。
指定输入文件、输出路径、主题和水印，剩下的全部自动处理。
:::

---

# 感谢观看

**Slide Video** — Markdown 一键生成教学视频

- 📄 阅读 SKILL.md 了解完整用法
- 🎬 开始制作你的第一个视频吧！

::: notes
感谢观看这个功能介绍。
Slide Video 让你用最熟悉的 Markdown 格式，快速制作专业的教学视频。
现在就开始制作你的第一个视频吧！
:::
