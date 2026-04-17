---
name: volcengine-image-generation
description: 使用火山引擎（火山方舟）生图大模型生成图片的技能，包含API调用格式和注意事项
version: 1.1.0
author: zealiao
tags: [image-generation, volcengine, doubao, ark]
---

# 火山引擎图像生成技能

## 使用要求
- 用户要求所有图片生成都使用火山引擎的生图大模型（已记录到记忆）
- 需要正确配置API密钥和Endpoint ID
- 生成图片后，直接输出图片链接，不要额外解释性内容和提示性内容

## API调用格式

### Endpoint URL
图像生成模型使用OpenAI兼容的images/generations接口：
```
https://ark.cn-beijing.volces.com/api/v3/images/generations
```

### 认证
- **Authorization**: Bearer {api_key}
- API Key格式: `ark-xxxx` (最新格式，旧格式是`sk-xxxx`)
- Access Key (`AKLT...`)用于其他火山引擎API，不是推理端点调用

### 请求格式
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": endpoint_id,
    "prompt": "[你的提示词]",
    "n": 1,
    "size": "2048x2048"  # 要求至少3686400像素，1024x1024太小不合法
}
```

### 示例代码
```python
import requests
import json

api_key = "your-ark-api-key"
endpoint_id = "your-endpoint-id"
prompt = "少女在河边自拍，青春靓丽，自然光线，河边柳树，清澈河水，清新风格，高清8k"

url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": endpoint_id,
    "prompt": prompt,
    "n": 1,
    "size": "2048x2048"
}

response = requests.post(url, headers=headers, json=payload, timeout=180)
result = response.json()
image_url = result['data'][0]['url']
print(f"生成图片URL: {image_url}")
```

## 常见错误
1. **401 Unauthorized / API key format incorrect**
   - 原因：使用了Access Key (AKLT开头)，API Key应该是 `ark-xxxx` 格式
   - 解决：在火山方舟控制台获取正确的API Key

2. **Endpoint not found / 404**
   - 原因：Endpoint ID不正确或URL路径错误
   - 解决：正确路径是 `https://ark.cn-beijing.volces.com/api/v3/images/generations`，在payload中指定model为endpoint id

3. **InvalidParameter: image size must be at least 3686400 pixels**
   - 原因：尺寸太小，1024×1024只有约100万像素，达不到368万像素最低要求
   - 解决：推荐使用 `2048×2048`，也可以使用 `1536×2560` 等满足像素要求的尺寸

## 提示词模板
正向模板（黑白水墨小猫示例）：
```
正向：小猫奔跑，黑白水墨风格，中国传统水墨画，简约，流畅笔触，黑白单色，动态运动，东方艺术，意境悠远
反向：彩色，模糊，低质量，扭曲，丑陋，解剖错误，照片写实，多余肢体，变形，噪点
```
