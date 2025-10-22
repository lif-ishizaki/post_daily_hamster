import os
import json
import random
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

FLICKR_FEED = "https://www.flickr.com/services/feeds/photos_public.gne?format=json&nojsoncallback=1&tags=hamster"
USED_FILE = Path("used.json")
USED_LIMIT = 500  # 履歴の最大保持数（超えたら古い順に削る）

def jst_now_str():
	jst = timezone(timedelta(hours=9))
	return datetime.now(jst).strftime("%Y-%m-%d %H:%M")

def load_used():
	if USED_FILE.exists():
		try:
			with USED_FILE.open("r", encoding="utf-8") as f:
				data = json.load(f)
				if isinstance(data, list):
					return data
		except Exception:
			pass
	return []

def save_used(used_list):
	# 上限超えたら古い方から間引く
	if len(used_list) > USED_LIMIT:
		used_list = used_list[-USED_LIMIT:]
	with USED_FILE.open("w", encoding="utf-8") as f:
		json.dump(used_list, f, ensure_ascii=False, indent=2)

def fetch_candidates():
	resp = requests.get(FLICKR_FEED, timeout=20)
	resp.raise_for_status()
	data = resp.json()
	items = data.get("items", [])
	cands = []
	for it in items:
		media = it.get("media", {})
		img = media.get("m")
		if not img:
			continue
		title = it.get("title") or "Hamster"
		page = it.get("link") or img
		key = page.strip() or img.strip()
		cands.append({
			"image_url": img,
			"title": title,
			"page_url": page,
			"key": key
		})
	random.shuffle(cands)
	return cands

def pick_unique(candidates, used_keys):
	for c in candidates:
		if c["key"] not in used_keys:
			return c, False  # False = 再利用ではない
	# すべて使用済みなら、被りを許容して1枚返す（フィードが少ない日用のフォールバック）
	return random.choice(candidates) if candidates else (None, None), True

def build_payload(image_url, title, page_url):
	jst_time = jst_now_str()
	text = f"今日のハムスター ({jst_time} JST)"
	return {
		"text": text,
		"blocks": [
			{
				"type": "section",
				"text": {"type": "mrkdwn", "text": f"*{text}*\n{title}\n<{page_url}|Flickr page>"}
			},
			{
				"type": "image",
				"image_url": image_url,
				"alt_text": title or "hamster"
			}
		]
	}

def post_to_slack(payload):
	webhook = os.environ.get("SLACK_WEBHOOK_URL")

	print("DEBUG: posting to slack")
	print("DEBUG: payload:", json.dumps(payload)[:500])
	r = requests.post(webhook, json=payload, timeout=20)
	print("DEBUG: response:", r.status_code, r.text)

	if not webhook:
		raise RuntimeError("環境変数 SLACK_WEBHOOK_URL が未設定")
	r = requests.post(webhook, json=payload, timeout=20)
	r.raise_for_status()

def main():
	used = load_used()
	used_keys = set(used)

	candidates = fetch_candidates()
	if not candidates:
		raise RuntimeError("画像候補が見つかりませんでした")

	choice, reused = pick_unique(candidates, used_keys)
	if choice is None:
		raise RuntimeError("選択に失敗しました")

	payload = build_payload(choice["image_url"], choice["title"], choice["page_url"])
	post_to_slack(payload)

	# 再利用でなければ履歴に追加
	if not reused:
		used.append(choice["key"])
		save_used(used)

if __name__ == "__main__":
	main()
