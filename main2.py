from pybooru import Danbooru
import requests
import time
import io
import os

TAG = ""
WEBHOOK_URL = ""
LIMIT = 10
SLEEP = 1.2
LAST_ID_FILE = f"{TAG}official_artlast_id.txt"

client = Danbooru("danbooru")

# ===== 最後に投稿したIDを読む =====
last_id = None
if os.path.exists(LAST_ID_FILE):
    with open(LAST_ID_FILE, "r") as f:
        try:
            last_id = int(f.read().strip())
            print(f"再開: last_id = {last_id}")
        except:
            pass

# ===== タグ条件を組み立て =====
tags = f"{TAG} official_art"
if last_id:
    tags += f" id:<{last_id}"

page = 1
posted = 0

while True:
    posts = client.post_list(
        tags=tags,
        limit=LIMIT,
        page=page
    )

    if not posts:
        print("全投稿完了")
        break

    for post in posts:
        post_id = post["id"]
        #NSFW除外
        if post.get("rating") != "s":
          continue

        image_url = post.get("file_url")
        if not image_url:
            continue

        # ファイルサイズ制限（8MB）
        if post.get("file_size", 0) > 8 * 1024 * 1024:
            continue

        # ===== 画像ダウンロード =====
        res = requests.get(image_url, timeout=20)
        if res.status_code != 200:
            continue

        image_bytes = io.BytesIO(res.content)

        files = {
            "file": ("image.jpg", image_bytes)
        }

        r = requests.post(
            WEBHOOK_URL,
            data={"content":""},
            files=files
        )

        if r.status_code >= 300:
            print("Discord送信失敗、停止")
            break

        # ===== 成功したら last_id 更新 =====
        with open(LAST_ID_FILE, "w") as f:
            f.write(str(post_id))

        posted += 1
        print(f"投稿済み: {posted} (ID {post_id})")

        time.sleep(SLEEP)

    page += 1
