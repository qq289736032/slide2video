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

# Slide Video 使用指南

**从 Markdown 到教学视频，一键搞定**

🎬 无需 API Key · 完全免费 · 本地运行

::: notes
大家好，欢迎来到 Slide Video 的完整使用指南。
今天我会带你从零开始，了解如何用这个工具把 Markdown 幻灯片变成一个带语音旁白和字幕的教学视频。
整个过程完全免费，不需要任何 API Key，所有处理都在你的本地电脑上完成。
:::

---

# 什么是 Slide Video？

一个轻量的本地工具链，将 Marp Markdown 转换为教学视频

- ✍️ 用 Markdown 写幻灯片和讲解稿（也可以用大模型生成 Marp 格式幻灯片演讲文稿）
- 🗣️ 自动将文字转为语音旁白（edge-tts）
- 📝 自动生成逐句字幕，烧录到视频中
- 🏷️ 支持自定义水印保护内容
- 📦 输出 1920×1080 MP4 视频 + SRT 字幕文件

::: notes
Slide Video 是一个本地工具链，核心功能就是把 Marp 格式的 Markdown 文件转换成教学视频。
你只需要用 Markdown 写好幻灯片内容和讲解稿，工具会自动帮你完成语音合成、字幕生成和视频合成。
最终输出的是一个 1920 乘 1080 分辨率的 MP4 视频，同时还有一份 SRT 字幕文件。
:::

---

# 核心工作流程

```
Markdown (.md) → 解析旁白 → 渲染幻灯片 → 语音合成 → 视频合成
```

| 步骤 | 工具 | 产物 |
|------|------|------|
| **1. 预处理** | `prepare.py` | `notes.json` + `_clean.md` |
| **2. 渲染** | `marp-cli` | `slides/*.png` |
| **3. 语音** | `edge-tts` | `audio/*.mp3` |
| **4. 合成** | `ffmpeg` | `output.mp4` + `output.srt` |

::: notes
整个流程分为四个步骤。
第一步是预处理，解析 Markdown 中的旁白内容，生成一份 JSON 文件和一份去掉旁白的干净版 Markdown。
第二步用 Marp 命令行工具把干净版渲染成一张张幻灯片图片。
第三步用微软的 edge-tts 引擎把旁白文字转成语音音频。
最后一步用 ffmpeg 把所有素材合成为最终的视频，包含硬字幕和水印。
:::

---

# 环境准备

安装三个必备工具

```bash
# 1. 安装 ffmpeg（视频处理引擎）
brew install ffmpeg

# 2. 安装 Marp CLI（幻灯片渲染）
npm install -g @marp-team/marp-cli

# 3. 安装 edge-tts（语音合成）
pip install edge-tts
```

✅ 验证安装：

```bash
ffmpeg -version && marp --version && python3 -c "import edge_tts"
```

::: notes
在开始之前，你需要安装三个工具。
第一个是 ffmpeg，用 brew install 就可以安装，它负责视频的编码和合成。
第二个是 Marp 命令行工具，用 npm 全局安装，它负责把 Markdown 渲染成幻灯片图片。
第三个是 edge-tts，用 pip 安装，它是微软的免费语音合成引擎。
安装完成后，运行验证命令确认三个工具都正常工作。
:::

---

# Markdown 文件格式

## Frontmatter 配置区

```yaml
---
marp: true
theme: default
voice: zh-CN-YunxiNeural      # 语音角色
watermark_text: "@我的频道"     # 水印文字
subtitle_fontsize: 44          # 字幕字号
---
```

`marp: true` 是必须的，其他参数可选

::: notes
Markdown 文件的开头是 frontmatter 配置区，用三条横线包裹。
其中 marp: true 是必须的，告诉 Marp 这是一个幻灯片文件。
voice 参数指定语音角色，watermark_text 设置水印文字，subtitle 开头的参数控制字幕样式。
这些参数都有默认值，你可以按需配置。
:::

---

# 幻灯片内容与旁白

## 每页结构

```markdown
# 页面标题

- 要点一
- 要点二

::: notes
这里写讲解旁白。
旁白会被转成语音和字幕。
不会显示在幻灯片画面上。
:::

---
```

⚠️ 用 `---` 分隔每页 · 旁白写在 `::: notes` 和 `:::` 之间

::: notes
每一页幻灯片的结构很简单。
上面写幻灯片上要显示的内容，比如标题、要点、代码块、表格等等。
下面用 notes 块写讲解旁白，这些文字不会出现在画面上，而是会被转成语音和字幕。
页与页之间用三条横线分隔。
旁白建议写成口语化的讲解稿，每页两到五句话比较合适。
:::

---

# 旁白写作技巧

好的旁白让视频更专业

- ✅ 口语化表达，像在跟观众聊天
- ✅ 每页 2-5 句话，控制单页时长
- ✅ 有过渡衔接，"接下来我们看看..."
- ✅ 补充幻灯片上没有的细节
- ❌ 不要照搬幻灯片上的文字
- ❌ 不要写太长，单页超过 8 句会显得拖沓

::: notes
写旁白有几个小技巧。
首先，旁白应该是口语化的讲解，不是照搬幻灯片上的文字。
其次，每页控制在两到五句话，太长会导致单页视频时间过长，观众容易走神。
另外，页与页之间加一些过渡语句，比如"接下来我们看看"，会让整个视频更流畅自然。
旁白的作用是补充和解释幻灯片上的内容，而不是重复它。
:::

---

# 一键生成视频

最简单的方式：使用 `run.py`

```bash
python3 {SKILL_DIR}/scripts/run.py input.md -o output.mp4
```

**常用参数：**

| 参数 | 说明 | 示例 |
|------|------|------|
| **`-o`** | 输出文件路径 | `-o my_video.mp4` |
| **`--voice`** | 覆盖语音角色 | `--voice zh-CN-XiaoxiaoNeural` |
| **`--watermark`** | 覆盖水印文字 | `--watermark @MyChannel` |
| **`--theme`** | 使用内置主题 | `--theme dark-blue` |
| **`--no-subtitle`** | 不烧录字幕 | |
| **`--keep-temp`** | 保留中间文件 | |

::: notes
最简单的使用方式是一键执行 run.py 脚本。
只需要指定输入的 Markdown 文件和输出的视频路径，一条命令就搞定了。
如果你想临时切换语音或修改水印，可以用命令行参数覆盖 frontmatter 里的设置。
加上 keep-temp 参数可以保留中间产物，方便调试。
:::

---

# 分步执行（调试模式）

适合需要检查中间产物的场景

```bash
# Step 1: 预处理 — 解析旁白 + 生成干净版 Markdown
python3 {SKILL_DIR}/scripts/prepare.py input.md -o notes.json

# Step 2: 渲染幻灯片图片
marp --images png input_clean.md -o slides/slide.png

# Step 3: 生成语音音频
python3 {SKILL_DIR}/scripts/generate_audio.py notes.json -o audio/

# Step 4: 合成最终视频
python3 {SKILL_DIR}/scripts/compose_video.py \
  slides/ audio/ -o output.mp4 --notes notes.json
```

::: notes
如果你想逐步检查每个环节的输出，可以分四步手动执行。
第一步运行 prepare.py，它会解析出旁白内容保存为 JSON，同时生成一份去掉旁白的干净版 Markdown。
第二步用 marp 命令把干净版渲染成 PNG 图片，注意要用 clean 版本，不是原文件。
第三步运行 generate_audio.py 生成每一页的语音音频。
最后运行 compose_video.py 把所有素材合成为视频。
每一步执行后你都可以检查中间产物，确认效果是否符合预期。
:::

---

# 字幕配置详解

在 frontmatter 中自定义字幕样式

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **`subtitle_font`** | `PingFang SC` | 字体名称 |
| **`subtitle_fontsize`** | `48` | 字号大小 |
| **`subtitle_color`** | `&H20FFFFFF` | ASS 格式颜色（白色半透明） |
| **`subtitle_outline_color`** | `&H60000000` | 描边颜色（黑色半透明） |
| **`subtitle_outline`** | `2` | 描边粗细 |
| **`subtitle_margin_v`** | `60` | 距底部边距（像素） |

💡 颜色格式为 ASS 标准：**`&HAABBGGRR`**（注意是 BGR 不是 RGB）

::: notes
字幕样式可以通过 frontmatter 参数精细控制。
字体默认是苹方，字号默认 48，在 1080p 视频里大小适中。
颜色使用 ASS 字幕的标准格式，注意顺序是 Alpha、蓝、绿、红，和常见的 RGB 不同。
描边可以让字幕在各种背景下都清晰可读，默认粗细为 2。
底部边距控制字幕离画面底部的距离，默认 60 像素。
:::

---

# 水印配置详解

保护你的视频内容 🔒

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **`watermark_text`** | （空） | 水印文字，留空则不显示 |
| **`watermark_opacity`** | `0.15` | 透明度（`0.0` 全透明 ~ `1.0` 不透明） |
| **`watermark_position`** | `top_right` | 位置选项 👇 |
| **`watermark_fontsize`** | `28` | 字号 |
| **`watermark_color`** | `white` | 颜色 |

📍 位置选项：`top_right` · `top_left` · `bottom_right` · `bottom_left`

::: notes
水印功能通过 watermark 开头的参数配置。
watermark_text 设置水印文字，如果留空就不会显示水印。
透明度默认百分之十五，非常低调，不会干扰观看。
位置支持四个角落，默认在右上角。
你也可以调整字号和颜色来匹配你的品牌风格。
:::

---

# 语音角色选择

支持中英文多种语音风格 🗣️

| Voice ID | 性别 | 风格 | 语言 |
|----------|------|------|------|
| **`zh-CN-YunxiNeural`** | 男 | 自然叙述 | 🇨🇳 中文 |
| **`zh-CN-XiaoxiaoNeural`** | 女 | 温暖亲切 | 🇨🇳 中文 |
| **`zh-CN-YunjianNeural`** | 男 | 新闻播报 | 🇨🇳 中文 |
| **`en-US-GuyNeural`** | 男 | 自然 | 🇺🇸 英文 |
| **`en-US-JennyNeural`** | 女 | 自然 | 🇺🇸 英文 |

在 frontmatter 中设置：**`voice: zh-CN-YunxiNeural`**

::: notes
语音角色方面，工具基于微软的 edge-tts 引擎，提供了多种选择。
中文推荐云希，声音自然适合教学叙述；晓晓的声音温暖亲切，适合轻松的内容。
如果你做英文内容，可以选择 Guy 或 Jenny。
注意目前不支持同一个文件里不同页使用不同语音，整个视频只能用一个语音角色。
:::

---

# 10 套内置主题

覆盖 **5 大场景**，通过 `--theme` 一键切换 🎨

| 系列 | 主题名 | 风格 |
|------|--------|------|
| 🏢 商务 | **`dark-blue`** | 深蓝渐变，沉稳专业 |
| 🏢 商务 | **`steel-blue`** | 钢蓝渐变，冷静理性 |
| 💻 科技 | **`dark-keynote`** | 纯黑，苹果 Keynote 风 |
| 💻 科技 | **`cyber-dark`** | 黑底青光，赛博朋克 |
| 📚 教育 | **`clean-white`** | 白底蓝色点缀，清爽 |
| 📚 教育 | **`warm-sand`** | 暖沙色，柔和护眼 |
| 🎨 创意 | **`gradient-purple`** | 紫粉渐变，年轻活力 |
| 🎨 创意 | **`sunset-gradient`** | 日落粉橙，自媒体风 |
| 🎓 学术 | **`minimal-academic`** | 纯白极简，衬线字体 |
| 🎓 学术 | **`latex-beamer`** | 白底蓝色导航条 |

::: notes
工具内置了十套经典主题，分为商务、科技、教育、创意和学术五个系列。
每个系列有两套风格可选，比如商务系列有深蓝和钢蓝，科技系列有苹果黑和赛博暗夜。
所有主题都用纯 CSS 渐变实现，不依赖外部图片，保持 skill 的轻量。
:::

---

# 使用主题

命令行指定主题名或 CSS 文件路径

```bash
# 使用内置主题（自动查找 themes/ 目录）
python3 run.py input.md -o output.mp4 --theme cyber-dark

# 使用自定义 CSS 文件
python3 run.py input.md -o output.mp4 --theme /path/to/my-theme.css
```

分步执行时，在 Marp 渲染步骤指定主题：

```bash
marp --theme {SKILL_DIR}/themes/dark-blue.css \
  --images png input_clean.md -o slides/slide.png
```

::: notes
使用主题非常简单，在一键命令里加上 theme 参数就行。
直接写主题名，工具会自动在 themes 目录下查找对应的 CSS 文件。
你也可以指定一个自定义的 CSS 文件路径，方便使用自己设计的主题。
如果是分步执行，在 Marp 渲染那一步加上 theme 参数即可。
建议根据你的内容场景选择合适的主题，比如技术分享用赛博暗夜，自媒体用日落渐变。
:::

---

# 配置优先级

三层配置，灵活覆盖

```
代码默认值  →  frontmatter  →  命令行参数
（最低优先级）                  （最高优先级）
```

**示例：** frontmatter 设置了 `voice: zh-CN-YunxiNeural`
命令行加 `--voice zh-CN-XiaoxiaoNeural` 会覆盖为晓晓

💡 适合临时测试不同配置，无需修改 Markdown 文件

::: notes
配置有三层优先级。
最底层是代码里的默认值，中间层是 Markdown 文件 frontmatter 里的设置，最高层是命令行参数。
高优先级会覆盖低优先级的同名配置。
这个设计很实用，比如你想临时换个语音试试效果，直接在命令行加参数就行，不用改文件。
:::

---

# 输出文件说明

| 文件 | 格式 | 说明 |
|------|------|------|
| 🎬 `output.mp4` | **H.264 + AAC** | 1920×1080, 30fps, 含硬字幕和水印 |
| 📝 `output.srt` | **SRT 字幕** | 逐句时间轴，可用于其他平台 |

**中间产物**（`--keep-temp` 时保留）：

| 文件 | 说明 |
|------|------|
| `notes.json` | 解析后的旁白数据 |
| `*_clean.md` | 去掉旁白的干净版 Markdown |
| `slides/*.png` | 渲染后的幻灯片图片 |
| `audio/*.mp3` | 每页的语音音频 |

::: notes
最终输出两个文件。
MP4 视频是 1080p 分辨率，30 帧，使用 H.264 编码，字幕和水印都已经烧录进去了。
SRT 字幕文件包含逐句的时间轴信息，如果你需要在其他平台单独上传字幕可以用到。
如果加了 keep-temp 参数，中间产物也会保留，包括旁白 JSON、干净版 Markdown、幻灯片图片和语音音频。
:::

---

# 注意事项与限制

使用前了解这些限制

- 🌐 需要网络连接（edge-tts 依赖微软在线 TTS 服务）
- ⏱️ 字幕时间轴按字数比例分配，非精确语音对齐
- 🎞️ 页间硬切，无过渡动画
- 🗣️ 不支持同一文件内不同页使用不同语音

::: notes
最后说几个需要注意的限制。
首先，语音合成需要网络连接，因为 edge-tts 调用的是微软的在线服务。
字幕的时间轴是按字数比例估算的，不是精确的语音对齐，偶尔会有轻微偏差。
页与页之间是硬切换，没有淡入淡出等过渡动画。
另外，整个视频只能使用一个语音角色，不能每页单独设置。
了解这些限制后，你就可以更好地规划你的视频内容了。
:::

---

# 快速上手总结

三步开始你的第一个视频

**1️⃣ 安装依赖**
```bash
brew install ffmpeg && npm i -g @marp-team/marp-cli && pip install edge-tts
```

**2️⃣ 编写 Markdown**（参考本文档格式）

**3️⃣ 一键生成**
```bash
python3 {SKILL_DIR}/scripts/run.py your_slides.md -o video.mp4 --theme dark-blue
```

🎉 就这么简单，开始制作你的教学视频吧！

::: notes
总结一下，上手只需要三步。
第一步安装三个依赖工具。
第二步按照 Marp 格式编写你的 Markdown 幻灯片，记得在 notes 块里写好讲解旁白。
第三步运行一键脚本，就能得到一个完整的教学视频。
就这么简单，现在就开始制作你的第一个视频吧！
:::
