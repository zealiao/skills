# TikHub Douyin API Reference (minimal)

- Base URL: `https://api.tikhub.io`
- Endpoint: `GET /api/v1/douyin/app/v3/fetch_one_video_by_share_url`
- Query param: `share_url` (Douyin share URL)
- Header: `Authorization: Bearer <API_KEY>`

Example:

```bash
curl -X GET \
  'https://api.tikhub.io/api/v1/douyin/app/v3/fetch_one_video_by_share_url?share_url=https%3A%2F%2Fv.douyin.com%2Fi5W8G25X%2F' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <API_KEY>'
```

Common response envelope:

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "aweme_id": "...",
    "desc": "...",
    "author": {},
    "video": {},
    "statistics": {}
  }
}
```
