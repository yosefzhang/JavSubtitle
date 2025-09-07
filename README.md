# 字幕爬虫工具

这是一个用于从 subtitlecat.com 搜索和下载中文字幕的命令行工具。

## 功能特点

- 从 subtitlecat.com 搜索字幕
- 自动识别视频文件并提取关键词
- 优先下载简体中文字幕，备选繁体中文字幕
- 支持单个视频文件、文件夹批量处理
- 自动跳过隐藏文件

## 安装依赖

在使用之前，请确保安装了所需的 Python 包：

```bash
pip install requests beautifulsoup4
```

## 使用方法

### 搜索特定关键词的字幕

```bash
python3 subtitle_scraper.py NIMA-014
```

### 为单个视频文件下载字幕

```bash
python3 subtitle_scraper.py "/path/to/NIMA-014.mp4"
```

### 为文件夹中的所有视频文件下载字幕

```bash
python3 subtitle_scraper.py "/path/to/videos/"
```

### 指定字幕下载目录

```bash
python3 subtitle_scraper.py "/path/to/videos/" --output-dir "/path/to/subtitles/"
```

## 支持的视频格式

- .mp4
- .avi
- .mkv
- .mov
- .wmv
- .flv
- .webm
- .m4v
- .ts

## 工作原理

1. 当输入为文件夹时，程序会扫描文件夹中的所有视频文件
2. 自动跳过隐藏文件（以`.`开头的文件或具有隐藏属性的文件）
3. 从视频文件名中提取关键词（如 NIMA-014）
4. 在 subtitlecat.com 上搜索该关键词
5. 查找中文字幕（优先简体中文，备选繁体中文）
6. 下载并保存字幕文件

## 注意事项

- 确保网络连接正常
- 某些字幕可能需要网站会员权限才能下载
- 下载的字幕文件将保存为 .srt 格式
- 程序会自动创建输出目录（如果不存在）

## 许可
此项目的所有权利与许可受 GPL-3.0 License 与 Anti 996 License 共同限制。此外，如果你使用此项目，表明你还额外接受以下条款：

- 本软件仅供学习 Python 和技术交流使用
- 请勿在微博、微信等墙内的公共社交平台上宣传此项目
- 用户在使用本软件时，请遵守当地法律法规
- 禁止将本软件用于商业用途