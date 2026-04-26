"""Centralized default configuration for Slide Video skill."""

# TTS defaults
DEFAULT_VOICE = "zh-CN-YunxiNeural"
DEFAULT_SILENCE_DURATION = 3  # seconds

# Video defaults
DEFAULT_RESOLUTION = "1920:1080"
DEFAULT_FPS = 30
DEFAULT_VIDEO_CODEC = "libx264"
DEFAULT_AUDIO_CODEC = "aac"
DEFAULT_AUDIO_BITRATE = "192k"

# Subtitle style (ASS format)
# Colors: &HAABBGGRR (AA=alpha 00=opaque FF=transparent, then BGR)
DEFAULT_SUBTITLE_STYLE = {
    "font": "PingFang SC",
    "fontsize": 48,
    "primary_color": "&H20FFFFFF",   # white, slightly transparent
    "outline_color": "&H60000000",   # black, semi-transparent
    "back_color": "&H80000000",      # black, 50% transparent
    "bold": True,
    "outline": 2,
    "shadow": 1,
    "margin_v": 60,
}

# Watermark style
DEFAULT_WATERMARK = {
    "text": "",
    "font": "PingFang SC",
    "fontsize": 28,
    "color": "white",
    "opacity": 0.15,
    "position": "top_right",
    "margin": 30,
}

# Watermark position → ffmpeg x:y expressions ({m} = margin)
WATERMARK_POSITIONS = {
    "top_right": ("w-tw-{m}", "{m}"),
    "top_left": ("{m}", "{m}"),
    "bottom_right": ("w-tw-{m}", "h-th-{m}"),
    "bottom_left": ("{m}", "h-th-{m}"),
}

# Frontmatter key → config key mappings
SUBTITLE_FRONTMATTER_KEYS = {
    "subtitle_font": "font",
    "subtitle_fontsize": "fontsize",
    "subtitle_color": "primary_color",
    "subtitle_outline_color": "outline_color",
    "subtitle_back_color": "back_color",
    "subtitle_outline": "outline",
    "subtitle_shadow": "shadow",
    "subtitle_margin_v": "margin_v",
    "subtitle_bold": "bold",
}

WATERMARK_FRONTMATTER_KEYS = {
    "watermark_text": "text",
    "watermark_font": "font",
    "watermark_fontsize": "fontsize",
    "watermark_color": "color",
    "watermark_opacity": "opacity",
    "watermark_position": "position",
    "watermark_margin": "margin",
}
