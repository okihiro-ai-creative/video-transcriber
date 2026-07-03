---
name: video-transcriber
description: 動画・音声ファイルからSRT/TXTの文字起こしを生成する単機能スキル。
---

# Video Transcriber Skill

## 目的

ローカルの `faster-whisper` で動画・音声ファイルを文字起こしし、`<元ファイル名>.srt` と `transcript.txt` を生成する。

## 前提条件

- Python 3.10+
- `pip install -r requirements.txt`
- NVIDIA GPU + CUDA 12.x 推奨。現在の同梱エンジンはGPU実行を前提にしている。
- 外部APIキーは不要。初回モデル取得時にネットワーク接続が必要になる場合がある。

## 実行例

```powershell
python scripts/run_transcription.py --project "<project folder>"
```

特定ファイルを指定する場合:

```powershell
python scripts/run_transcription.py --project "<project folder>" --file "input.mp4"
```

## 入力

`<project folder>/02_Inputs/` またはプロジェクト直下にある `.mp4`, `.mp3`, `.m4a`, `.wav`, `.mkv`, `.mov`。

## 出力

- `<元ファイル名>.srt`
- `transcript.txt`

## 禁止

- 配布物に音声・動画素材を含めない。
- `workspace/` の一時ファイルを成果物として扱わない。
- 文字起こし結果に個人情報が含まれる可能性がある場合、チャットへ全文貼り付けない。

## 完了条件

- [ ] 入力ファイルが存在する。
- [ ] SRTが生成された。
- [ ] transcript.txtが生成された。
- [ ] 一時ファイルが残っていない。
