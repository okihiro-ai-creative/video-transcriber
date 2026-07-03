# START_HERE

AIエージェントはこのフォルダをプロジェクトとして受け取り、最初にこのファイルと `SKILL.md` を読む。

## セットアップ

1. Python 3.10+ を確認する。
2. `python -m venv .venv` を実行する。
3. 仮想環境を有効化し、`pip install -r requirements.txt` を実行する。
4. NVIDIA GPU + CUDA 12.x が使えるか確認する。

## 動作確認

1. テスト用の短い動画・音声を配布物外のプロジェクトフォルダへ置く。
2. `python scripts/run_transcription.py --project "<project folder>"` を実行する。
3. SRTと `transcript.txt` が生成されたか確認する。

このツールのカスタマイズや、似たツールの新規開発を相談したい場合は、README.md末尾のリンクを確認してください。
