# lmt

自治会総会の出欠確認・議決権行使を管理する Flask アプリです。

## 機能
- 総会への参加 / 不参加を登録
- 不参加者は「議長に一任」または「本人で議決権行使」を選択
- 本人行使の場合、5議案それぞれに賛成/反対を入力
- 議長一任の場合は全議案を自動で「賛成」扱い
- 部屋番号・氏名・記入日を保存
- 同一の「部屋番号 + 氏名」の重複登録を防止（1回のみ登録）
- 管理画面で以下を確認
  - 出欠集計
  - 不参加者の個別行使状況
  - 議案ごとの総計

## セットアップ
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 起動
```bash
python app.py
```

- フォーム画面: http://127.0.0.1:5000/
- 管理画面: http://127.0.0.1:5000/admin

`responses.db` にデータが保存されます。

## ファイルを一括ダウンロード（圧縮）
以下のコマンドで、主要ファイルを `tar.gz` にまとめられます。

```bash
./scripts/create_archive.sh
```

出力された `lmt_files_YYYYMMDD_HHMMSS.tar.gz` をダウンロードして利用してください。
