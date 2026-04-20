# Seedance 2.0 API Notes

来源：本地整理的 Seedance 2.0 接口文档与火山引擎官方文档链接。

## 已确认信息

- Base URL: `https://ark.cn-beijing.volces.com/api/v3`
- 创建任务接口：`POST /contents/generations/tasks`
- 查询单个任务接口：官方文档对应 `GET /contents/generations/tasks/{id}` 的任务详情模式
- 查询任务列表接口：官方文档对应 `GET /contents/generations/tasks`
- 取消或删除任务接口：官方文档对应 `DELETE /contents/generations/tasks/{id}`
- 鉴权头：`Authorization: Bearer $ARK_API_KEY`
- 请求体核心字段：
  - `model`
  - `content`
  - `generate_audio`
  - `ratio`
  - `duration`
  - `watermark`

## content 数组示例

- 文本：
  - `{"type":"text","text":"..."}`
- 参考图：
  - `{"type":"image_url","image_url":{"url":"https://..."}, "role":"reference_image"}`
- 参考视频：
  - `{"type":"video_url","video_url":{"url":"https://..."}, "role":"reference_video"}`
- 参考音频：
  - `{"type":"audio_url","audio_url":{"url":"https://..."}, "role":"reference_audio"}`

## 当前 skill 的实现边界

- 已实现创建、查询详情、查询列表、取消或删除
- 只对 URL 型参考素材提供一等支持
- 不在仓库中保存文档内出现的明文 API Key；统一改用环境变量

## 说明

- 详情、列表、删除路径是依据官方文档标题与同一资源命名体系做的实现对齐
- 如果后续文档给出更细的筛选字段或返回结构，再按文档继续补充脚本参数

## 原始示例特征

- 模型值看起来是 endpoint ID，例如 `ep-20260420162858-phzmr`
- 支持同时混合 text、image、video、audio
- 示例里 `generate_audio=true` 且 `watermark=false`
