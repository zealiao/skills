---
name: bitiful-s4
description: 使用缤纷云 Bitiful 的 S4（S3 兼容对象存储）进行文件上传、下载、列举、删除和预签名链接生成。当用户提到 Bitiful、缤纷云、S4、S3 兼容存储、对象存储上传下载、aishipin 桶，或要用 Python boto3 连接 `s3.bitiful.net` 时使用。
---

# Bitiful S4

使用这个 skill 时，优先复用脚本 `/Users/imac/Documents/OBKU-Bill-v1/skills/bitiful-s4/scripts/bitiful_s4.py`，不要重新手写 boto3 连接代码，除非用户明确要求示例代码。

## 默认连接配置

- bucket: `aishipin`
- SDK endpoint URL: `https://s3.bitiful.net`
- bucket 访问域名: `https://aishipin.s3.bitiful.net`
- service endpoint: `s3.bitiful.net`
- region: `cn-east-1`

出于安全考虑，脚本不内置明文密钥。运行前需要设置：

- `BITIFUL_ACCESS_KEY`
- `BITIFUL_SECRET_KEY`
- `BITIFUL_BUCKET`
- `BITIFUL_ENDPOINT_URL`
- `BITIFUL_REGION`
- `BITIFUL_PUBLIC_BASE_URL`（可选，默认 `https://aishipin.s3.bitiful.net`）

## 前提

先安装依赖：

```bash
python3 -m pip install -r /Users/imac/Documents/OBKU-Bill-v1/skills/bitiful-s4/requirements.txt
```

设置环境变量：

```bash
export BITIFUL_ACCESS_KEY="your_access_key"
export BITIFUL_SECRET_KEY="your_secret_key"
```

## 快速用法

### 上传文件

```bash
python3 /Users/imac/Documents/OBKU-Bill-v1/skills/bitiful-s4/scripts/bitiful_s4.py upload /absolute/path/to/file.png uploads/file.png
```

### 下载文件

```bash
python3 /Users/imac/Documents/OBKU-Bill-v1/skills/bitiful-s4/scripts/bitiful_s4.py download uploads/file.png /absolute/path/to/file.png
```

### 列举对象

```bash
python3 /Users/imac/Documents/OBKU-Bill-v1/skills/bitiful-s4/scripts/bitiful_s4.py list --prefix uploads/
```

### 删除对象

```bash
python3 /Users/imac/Documents/OBKU-Bill-v1/skills/bitiful-s4/scripts/bitiful_s4.py delete uploads/file.png
```

### 生成预签名下载链接

```bash
python3 /Users/imac/Documents/OBKU-Bill-v1/skills/bitiful-s4/scripts/bitiful_s4.py presign uploads/file.png --expires-in 3600
```

## 工作流

1. 判断用户是要上传、下载、列举、删除，还是生成链接。
2. 优先执行脚本，不重复手写 boto3 初始化代码。
3. 如果只是临时验证连通性，优先用 `list` 或 `presign`。
4. 上传成功后，从 JSON 输出里读取 `bucket`、`key`、`url`。
5. 若用户要求示例代码，再基于本脚本结构给最小 boto3 示例。
6. 连接 S4 时默认走 `https://s3.bitiful.net`，并使用 path-style 寻址。

## 输出约定

- 脚本统一打印 JSON，便于后续自动化消费。
- 出错时返回非 0 退出码，并打印带 `error` 字段的 JSON。
