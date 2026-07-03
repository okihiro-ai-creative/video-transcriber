import sys
import argparse
import gc
import time
from datetime import timedelta
import os

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def _enforce_venv():
    """仮想環境下での実行を強制する"""
    is_venv = (sys.prefix != sys.base_prefix) or (os.environ.get("VIRTUAL_ENV") is not None)
    if not is_venv:
        print("[ERROR] 仮想環境(.venv)が有効になっていません。")
        print("システム保護のため、実行を中止します。")
        print("対策: '.venv\\Scripts\\Activate.ps1' (Win) または 'source .venv/bin/activate' (Mac/Linux) を実行してください。")
        sys.exit(1)

_enforce_venv()

def detect_device():
    """CUDAが安全に利用可能かテストし、デバイスとcompute_typeを返す。GPU必須。"""
    try:
        import ctranslate2
        supported_types = ctranslate2.get_supported_compute_types("cuda")
        if "int8" in supported_types or "float16" in supported_types:
            print("[OK] CUDAテスト成功。GPUモードで実行します。")
            return "cuda", "int8"
    except Exception as e:
        print(f"[ERROR] CUDAテスト失敗: {e}")
    
    print("[ERROR] GPU(CUDA)が利用できません。このスキルはGPU必須です。")
    print("対策: NVIDIA GPUドライバーおよびCUDA Toolkit 12.xがインストールされていることを確認してください。")
    sys.exit(1)

def seconds_to_srt_time(seconds):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    millis = int(td.microseconds / 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def write_to_srt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = seconds_to_srt_time(segment.start)
            end = seconds_to_srt_time(segment.end)
            f.write(f"{i}\n{start} --> {end}\n{segment.text.strip()}\n\n")

def cleanup_memory(model=None):
    """メモリとVRAMの解放を試みる (Windows CTranslate2バグ回避のため何もしない)"""
    pass

def run_transcribe(video_path, output_srt):
    from faster_whisper import WhisperModel

    # デバイスの安全な自動検出（GPU必須）
    device, compute_type = detect_device()
    
    model = None

    # 1st Attempt: Medium Model (High Accuracy)
    try:
        print(f"[INFO] [試行 1/2] '{device.upper()}' で 'medium' モデルをロードしています...")
        model = WhisperModel("medium", device=device, compute_type=compute_type)
        
        print("[OK] モデルロード成功 (medium)。文字起こしを開始します...")
        segments, info = model.transcribe(str(video_path), beam_size=5, language="ja")
        
        result_segments = list(segments)
        
        write_to_srt(result_segments, output_srt)
        print("[OK] 文字起こし完了 (medium)")
        return

    except Exception as e:
        print(f"[WARN] 'medium' モデルでの実行に失敗しました:\n{e}")
        print("-" * 30)
        
    finally:
        cleanup_memory(model)
        model = None

    # 2nd Attempt: Small Model (Same Device)
    try:
        print(f"[INFO] [試行 2/2] '{device.upper()}' で 'small' モデルに切り替えて再試行します...")
        model = WhisperModel("small", device=device, compute_type=compute_type)
        
        print("[OK] モデルロード成功 (small)。文字起こしを開始します...")
        segments, info = model.transcribe(str(video_path), beam_size=5, language="ja")
        
        result_segments = list(segments)
        write_to_srt(result_segments, output_srt)
        print("[OK] 文字起こし完了 (small)")
        return

    except Exception as e:
        print(f"[ERROR] すべてのGPU試行に失敗しました:\n{e}")
        sys.exit(1)

    finally:
        cleanup_memory(model)
        model = None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video_path")
    parser.add_argument("output_srt")
    args = parser.parse_args()
    
    run_transcribe(args.video_path, args.output_srt)

    # Windows環境でGPU(CUDA)を利用した際、Python終了時の CTranslate2 (C++) デストラクタが
    # STATUS_STACK_BUFFER_OVERRUN (0xC0000409 / 3221226505) でクラッシュする既知のバグを回避するため、
    # 例外的かつ安全な手段として、プロセスを強制正常終了(0)させます。
    import os
    os._exit(0)
