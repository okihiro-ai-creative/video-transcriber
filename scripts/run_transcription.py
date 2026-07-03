#!/usr/bin/env python3
"""
文字起こし実行スクリプト (Transcriber Runner)
- プロジェクトフォルダを受け取り、任意の動画ファイル（*.mp4）を探す
- 日本語パストラブルを避けるため、スキル内の workspace にコピーして処理を実行する
- <動画ファイル名>.srt と transcript.txt を元のプロジェクトフォルダに書き戻す
"""
import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Skill Root Logic
SCRIPT_DIR = Path(__file__).parent
SKILL_ROOT = SCRIPT_DIR.parent
WORKSPACE_DIR = SKILL_ROOT / "workspace"

def _enforce_venv():
    # 簡易的なVenvチェック
    executable_path = Path(sys.executable).resolve()
    # 予想されるVenvパス
    expected_venv_python = (SKILL_ROOT / ".venv/Scripts/python.exe").resolve()
    
    # パスが一致しない、かつ VIRTUAL_ENV 環境変数もない場合は警告（実行は止めないが推奨）
    if executable_path != expected_venv_python and os.environ.get("VIRTUAL_ENV") is None:
        print(f"[WARN] Running with {executable_path}")
        print(f"   Recommended: {expected_venv_python}")

_enforce_venv()

def run_transcription(project_path, target_file_name=None):
    project_dir = Path(project_path).resolve()
    
    # 1. 指定ファイルがあればそれを使用。なければ探索。
    valid_extensions = [".mp4", ".mp3", ".m4a", ".wav", ".mkv", ".mov"]
    inputs_dir = project_dir / "02_Inputs"
    
    if target_file_name:
        # まず project_dir で探す
        source_file = project_dir / target_file_name
        if not source_file.exists():
            # 次に 02_Inputs で探す
            source_file = inputs_dir / target_file_name
            
        if not source_file.exists():
            print(f"[ERROR] Specified file '{target_file_name}' not found in {project_dir} or {inputs_dir}")
            sys.exit(1)
        
        # 実際に書き出し先を決定するために inputs_dir を調整
        if not (inputs_dir / target_file_name).exists() and (project_dir / target_file_name).exists():
            inputs_dir = project_dir
    else:
        # 自動探索順序: 02_Inputs -> ./*. (mp4, mp3, m4a, wav 等)
        input_files = []
        
        if inputs_dir.exists():
            for ext in valid_extensions:
                input_files.extend(list(inputs_dir.glob(f"*{ext}")))
        
        if not input_files:
            # Fallback to root
            for ext in valid_extensions:
                input_files.extend(list(project_dir.glob(f"*{ext}")))
            
            if not input_files:
                print(f"[ERROR] No valid media files ({', '.join(valid_extensions)}) found in {inputs_dir} or {project_dir}")
                sys.exit(1)
            inputs_dir = project_dir # 便宜上 inputs_dir をルートにする
            
        source_file = input_files[0]

    print(f"[INFO] Target file found: {source_file.name}")

    # 2. Workspaceの準備 (日本語パス回避)
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    file_ext = source_file.suffix
    temp_input = WORKSPACE_DIR / f"input{file_ext}"
    temp_srt = WORKSPACE_DIR / "output.srt"
    
    # 既存のキャッシュクリア
    if temp_input.exists(): temp_input.unlink()
    if temp_srt.exists(): temp_srt.unlink()

    # 安全な場所にコピー
    print(f"[INFO] Preparing: copying {source_file} to workspace...")
    shutil.copy2(source_file, temp_input)

    # 出力パス設定 (最終書き戻し用)
    final_srt = inputs_dir / f"{source_file.stem}.srt"
    final_txt = inputs_dir / "transcript.txt"
    
    transcribe_engine = SCRIPT_DIR / "transcribe_engine.py"
    
    print(f"[INFO] Transcription started (Safe Mode): {temp_input}")
    
    # transcribe_engine.py をサブプロセスで実行 (英語のみの安全なパスで)
    try:
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        subprocess.run([sys.executable, str(transcribe_engine), str(temp_input), str(temp_srt)], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Transcription failed: {e}")
        sys.exit(1)
    
    # 3. 処理完了後、結果を移動＆抽出
    if temp_srt.exists():
        print(f"[INFO] Copying results back to {inputs_dir}...")
        shutil.copy2(temp_srt, final_srt)
        
        # SRT -> TXT 変換（タイムコード除去）
        try:
            with open(final_srt, 'r', encoding='utf-8') as f:
                # タイムコード行と空行、数字のみの行を除外
                lines = []
                for l in f:
                    clean_l = l.strip()
                    if not clean_l: continue
                    if clean_l.isdigit(): continue
                    if "-->" in clean_l: continue
                    lines.append(clean_l)
            
            with open(final_txt, "w", encoding="utf-8") as f:
                f.write(" ".join(lines))
            print(f"[OK] TXT generated: {final_txt}")
        except Exception as e:
            print(f"[WARN] TXT conversion failed: {e}")
            
    # 4. クリーンアップ
    print("[INFO] Cleaning workspace...")
    if temp_input.exists(): temp_input.unlink()
    if temp_srt.exists(): temp_srt.unlink()
            
    print("[OK] Transcription process completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run transcription on a project")
    parser.add_argument("--project", required=True, help="Path to the project directory")
    parser.add_argument("--file", help="Specific file name to transcribe (optional)")
    args = parser.parse_args()
    
    run_transcription(args.project, args.file)
