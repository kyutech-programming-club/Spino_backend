import sounddevice as sd
import numpy as np
import librosa

# サンプリングレートとバッファサイズを設定
sr = 22050  # サンプリングレート
buffer_size = 2048  # バッファサイズ

# 英語音階名をドレミファソラシドに変換する辞書
note_to_doremi = {
    'C': 'ド',
    'C#': 'ド#',
    'D': 'レ',
    'D#': 'レ#',
    'E': 'ミ',
    'F': 'ファ',
    'F#': 'ファ#',
    'G': 'ソ',
    'G#': 'ソ#',
    'A': 'ラ',
    'A#': 'ラ#',
    'B': 'シ'
}

# 音声データをリアルタイムで処理するコールバック関数
def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    
    # 入力された音声データを取得
    audio_data = indata[:, 0]  # 1チャンネル分の音声
    
    # ピッチ推定（基本周波数を取得）
    f0, voiced_flag, voiced_probs = librosa.pyin(audio_data, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr)
    
    # 基本周波数が存在するかを確認
    if f0 is not None:
        # nanを除いた周波数の平均を取得
        valid_f0 = f0[~np.isnan(f0)]
        if len(valid_f0) > 0:
            dominant_f0 = np.mean(valid_f0)
            note = librosa.hz_to_note(dominant_f0)
            
            # 音階をドレミファソラシドに変換
            base_note = note[:-1]  # 音階（例: C, D#, E）
            octave = note[-1]      # オクターブ番号（例: 4）
            doremi_note = note_to_doremi.get(base_note, "不明") + octave  # ドレミファソラシド形式に変換
            
            print(f"基本周波数: {dominant_f0:.2f} Hz, 音階: {doremi_note}")
        else:
            print("音が判別できませんでした")
    else:
        print("音が判別できませんでした")

# ストリームを開始し、リアルタイムで音声を処理
with sd.InputStream(callback=audio_callback, channels=1, samplerate=sr, blocksize=buffer_size):
    print("リアルタイム音声処理中... Ctrl+C で終了")
    sd.sleep(100000)  # 100秒間録音（任意の時間に設定可能）