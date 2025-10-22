# 🐹 Daily Hamster Bot

毎日1回、自動でハムスターの画像を Slack に投稿してくれる癒しBot
Flickrの公開フィードからランダムで画像を取得し、GitHub Actionsで毎朝実行されます。
被り防止機能つきで、同じハムちゃんが連投されることもありません。

---

## 🧩 仕組み

1. GitHub Actions が毎日 09:00（JST）に実行
2. Flickr の「hamster」タグ付き画像を取得
3. 未使用の画像を選んで Slack に投稿
4. 投稿済みURLを `used.json` に記録してコミット
5. 次回以降は被りをスキップして新しいハムスターを投下！