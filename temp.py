import sounddevice as sd
import numpy as np
import librosa
import os
import json
from connection import send_data_loop

# 音声ファイルのパス
current_dir = os.path.dirname(os.path.abspath(__file__))
audio_file_path = os.path.join(current_dir, "audio_files", "hole_new_world.mp3")

# ms_dictのパス
ms_dict_path = os.path.join(current_dir, "ms_dict")

# サンプリングレートを設定
sr = 22050  # サンプリングレート

# 英語音階名をドレミファソラシドに変換する辞書
note_to_doremi = {
    'C': 'ド',
    'C♯': 'ド',
    'D': 'レ',
    'D♯': 'レ',
    'E': 'ミ',
    'F': 'ファ',
    'F♯': 'ファ',
    'G': 'ソ',
    'G♯': 'ソ',
    'A': 'ラ',
    'A♯': 'ラ',
    'B': 'シ'
}

# 音声データを指定された時間毎に分割
def split_audio(audio_data, split_time, sr=22050):
    split_index = int(sr * split_time)
    split_audio_data = [audio_data[i:i+split_index] for i in range(0, len(audio_data), split_index)]
    return split_audio_data

# ファイル名の連番を作成する
def get_next_filename(base_filename, extension, i):
    filename = f"{base_filename}_{i}.{extension}"
    return filename

# バイオリンの音階を判定する
def ms_recognition(indata, sr=22050, hop_length=512):
    # 入力された音声データを取得 
    audio_data = indata  # 1チャンネル分の音声
    
    # ピッチ推定（基本周波数を取得）
    f0, _, _  = librosa.pyin(audio_data, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr, hop_length=hop_length)
    
    # 基本周波数が存在するかを確認
    if f0 is not None:
        # nanを除いた周波数の平均を取得
        valid_f0 = f0[~np.isnan(f0)]
        if len(valid_f0) > 0:
            dominant_f0 = np.mean(valid_f0)
            note = librosa.hz_to_note(dominant_f0)  # 周波数を対応する音階名に変換する
            # 音階をドレミファソラシドに変換
            base_note = note[:-1]  # 音階（例: C, D#, E）
            octave = note[-1]      # オクターブ番号（例: 4）
            doremi_note = note_to_doremi.get(base_note, "不明") + octave  # ドレミファソラシド形式に変換
            
            return doremi_note
        else:
            return "休符"
    else:
        return "検知失敗"

# 音声ファイルを読み込み、リアルタイムで音声を処理
audio_data, sr = librosa.load(audio_file_path, sr=sr)

# 音声ファイルを0.476秒ごとに分割(八部音符の秒数)
split_audio_data = split_audio(audio_data, split_time=0.476, sr=sr)

ms_list = []  # ms_dictの代わりにリストで音階を保存
current_i = 0
i = 0

# ms_dict以下のファイルを削除
for file in os.listdir(ms_dict_path):
    file_path = os.path.join(ms_dict_path, file)
    os.remove(file_path)

# 音声データをUnityに送信する
for audio_data in split_audio_data:
    note = ms_recognition(audio_data)
    ms_list.append(note)
    current_i += 1
    
    # 1小節分の音階を取得したらUnityに送信する
    if current_i == 8:
        filename = get_next_filename("ms_dict", "json", i)
        ms_save_path = os.path.join(ms_dict_path, filename)
        
        with open(ms_save_path, "w", encoding="utf-8") as f:
            json.dump(ms_list, f, ensure_ascii=False, indent=4)
        
        # Unityにデータを送信する場合は以下を有効化
        # send_data_loop(ms_save_path)
        
        # 次の小節に備えてリストをリセット
        ms_list = []
        current_i = 0
        i += 1