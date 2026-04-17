---
name: tikhub-douyin-video
description: 使用 TikHub 抖音 API 将“抖音分享文案/分享链接”解析为视频相关数据（aweme_id、desc、author、播放地址、封面、统计数据等）。当用户要求输入抖音分享链接并直接返回视频 JSON 数据时使用。
---

# TikHub Douyin Video

## Quick start

```bash
python3 scripts/fetch_douyin_video.py \
  --share-url "https://v.douyin.com/i5W8G25X/" \
  --pretty
```

支持直接传入整段分享文案（脚本会自动提取 URL）：

```bash
python3 scripts/fetch_douyin_video.py \
  --share-text "3.45 复制打开抖音，看看【用户名】的视频#抖音 https://v.douyin.com/i5W8G25X/"
```

## Workflow

1. 接收用户输入的抖音分享链接或分享文案。
2. 运行 `scripts/fetch_douyin_video.py`，由脚本自动提取 URL 并调用 TikHub API。
3. 默认输出 `data` 字段（即视频相关核心数据）；如需完整返回体，加 `--raw`。
4. 如果接口报错，原样输出错误 JSON，便于排查。

## Parameters

- `--share-url`: 抖音分享链接（可直接传链接）
- `--share-text`: 抖音分享文案（可包含链接，脚本自动提取）
- `--api-key`: 可选，默认使用内置 key；建议通过 `TIKHUB_API_KEY` 覆盖
- `--base-url`: 默认 `https://api.tikhub.io`
- `--timeout`: HTTP 超时秒数，默认 `20`
- `--retries`: 自动重试次数，默认 `3`
- `--retry-delay`: 初始重试间隔秒，默认 `1.0`（线性退避）
- `--user-agent`: 请求头 UA，默认浏览器风格 UA（可通过 `TIKHUB_USER_AGENT` 覆盖）
- `--pretty`: 格式化 JSON 输出
- `--raw`: 输出完整响应（默认只输出 `data`）

## Output contract

- 成功（默认展示）: 使用**中文 Markdown 表格**输出核心字段，字段顺序如下：
  - `视频ID（aweme_id）`
  - `文案（desc）`
  - `作者昵称`
  - `作者UID`
  - `发布时间戳（create_time）`
  - `点赞数（digg_count）`
  - `评论数（comment_count）`
  - `分享数（share_count）`
  - `收藏数（collect_count）`
  - `封面链接（cover）`（使用可点击链接）
  - `播放地址（play_addr）`（使用可点击链接）
- 获取无水印视频链接：只输出**最高清晰度**的链接（包含主线路和备用线路），不输出低清晰度多个链接
- 成功（按需）: 若用户明确要求 `JSON` / `原始数据` / `所有清晰度`，再返回完整信息（默认为视频 `data` 对象；`--raw` 返回完整响应）。
- 失败: 输出错误信息到 stderr，退出码非 0；若为网络抖动，优先通过 `--retries` 与 `--retry-delay` 自动重试。

## Reference

接口说明见 [references/tikhub_douyin_api.md](references/tikhub_douyin_api.md)。
