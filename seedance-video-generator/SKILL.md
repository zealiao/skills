---
name: seedance-video-generator
description: 使用火山方舟内容生成任务接口管理豆包视频生成模型 Seedance 2.0 的视频任务。当用户提到 Seedance、豆包视频生成、文生视频、图生视频、参考视频生成、带参考音频生成视频，或需要创建、查询、列出、取消/删除该 API 任务时使用。
---

# Seedance Video Generator

使用这个 skill 时，优先复用 `scripts/seedance_video.py`，不要手写 HTTP 请求。

## 前提

- 需要环境变量 `ARK_API_KEY`
- 可选环境变量：
  - `ARK_API_BASE`，默认 `https://ark.cn-beijing.volces.com/api/v3`
  - `SEEDANCE_MODEL`，默认需要显式传入；也可写进本 skill 目录下的 `.env`
- 如果用户只给了本地文件而不是公网 URL，先说明当前文档只覆盖 URL 型引用素材；不要擅自假设支持本地直传

## 快速用法

### 纯文本生成视频

```bash
python3 scripts/seedance_video.py \
  create \
  --model ep-xxxxxxxxxxxxxxxx \
  --prompt "第一视角果茶广告，快切，明亮商业质感" \
  --ratio 16:9 \
  --duration 8
```

### 带参考图/视频/音频

```bash
python3 scripts/seedance_video.py \
  create \
  --model ep-xxxxxxxxxxxxxxxx \
  --prompt "第一视角果茶广告" \
  --image-url https://example.com/ref-1.jpg \
  --image-url https://example.com/ref-2.jpg \
  --video-url https://example.com/ref.mp4 \
  --audio-url https://example.com/bg.mp3 \
  --generate-audio \
  --ratio 16:9 \
  --duration 11 \
  --no-watermark
```

### 用 JSON 文件提交复杂请求

```bash
python3 scripts/seedance_video.py \
  create \
  --payload /absolute/path/to/payload.json
```

`payload.json` 应直接对应接口请求体结构。只有在参数很多、或者需要手工控制 `content` 数组时再用它。

### 查询单个任务

```bash
python3 scripts/seedance_video.py \
  get task_xxxxxxxxxxxxxxxx
```

### 查询任务列表

```bash
python3 scripts/seedance_video.py \
  list \
  --page-index 1 \
  --page-size 20
```

可选过滤：

```bash
python3 scripts/seedance_video.py \
  list \
  --status completed \
  --task-id task_1 \
  --task-id task_2
```

### 取消或删除任务

```bash
python3 scripts/seedance_video.py \
  delete task_xxxxxxxxxxxxxxxx
```

## 工作流

1. 先判断用户是要创建、查询详情、查询列表，还是取消/删除任务。
2. 优先运行脚本，不要在回复里重写整段 curl，除非用户明确要示例代码。
3. 创建任务时，简单请求优先用命令行参数；复杂多模态请求再用 `--payload`。
4. 查询任务时，直接返回接口 JSON；必要时再摘要 `id`、`status`、`model`、时间字段。
5. 如果用户要核对字段或扩展请求体，再读参考文档。

## 参数约定

- `--prompt` 会生成一个 `{"type":"text","text":...}` 的内容项
- `--image-url` 会追加 `role=reference_image`
- `--video-url` 会追加 `role=reference_video`
- `--audio-url` 会追加 `role=reference_audio`
- `--no-watermark` 会把 `watermark` 设为 `false`
- `--generate-audio` 会把 `generate_audio` 设为 `true`
- `get <task_id>` 查询单个任务
- `list` 查询任务列表，支持分页和简单过滤
- `delete <task_id>` 对应官方“取消或删除视频生成任务”接口

## 参考

- 需要核对 API 字段时，读 [references/api.md](references/api.md)
