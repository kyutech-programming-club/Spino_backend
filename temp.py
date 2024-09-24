import sounddevice as sd
import numpy as np
import librosa
import os
import json

# 音声ファイルのパス
current_dir = os.path.dirname(os.path.abspath(__file__))
audio_file_path = os.path.join(current_dir, "audio_files", "hole_new_world.mp3")

# ms_dictのパス
ms_dict_path = os.path.join(current_dir, "ms_dict")

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

# 音声データを指定された時間毎に分割
def split_audio(audio_data, sr=22050, split_time=0.3):
    split_index = int(sr * split_time)
    split_audio_data = [audio_data[i:i+split_index] for i in range(0, len(audio_data), split_index)]
    return split_audio_data

# バイオリンの音階を判定する
def ms_recognition(indata, sr=22050, hop_length=256):
    # 入力された音声データを取得 
    audio_data = indata # 1チャンネル分の音声
    
    # ピッチ推定（基本周波数を取得）
    f0, voiced_flag, voiced_probs = librosa.pyin(audio_data, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr, hop_length=hop_length)
    
    # 基本周波数が存在するかを確認
    if f0 is not None:
        # nanを除いた周波数の平均を取得
        valid_f0 = f0[~np.isnan(f0)]
        if len(valid_f0) > 0:
            dominant_f0 = np.mean(valid_f0)
            note = librosa.hz_to_note(dominant_f0) # 周波数を対応する音階名に変換する
            
            # 音階をドレミファソラシドに変換
            base_note = note[:-1]  # 音階（例: C, D#, E）
            octave = note[-1]      # オクターブ番号（例: 4）
            doremi_note = note_to_doremi.get(base_note, "不明") + octave  # ドレミファソラシド形式に変換
            
            print(f"基本周波数: {dominant_f0:.2f} Hz, 音階: {doremi_note}")
            return doremi_note
        else:
            print("音が判別できませんでした")
    else:
        print("無音")
    return "無音"        

# ファイル名の連番を作成する
def get_next_filename(base_filename, extension):
    i = 1
    while True:
        filename = f"{base_filename}_{i}.{extension}"
        if not os.path.exists(filename):
            return filename
        i += 1

# 音声ファイルを読み込み、リアルタイムで音声を処理
audio_data, sr = librosa.load(audio_file_path, sr=sr)
print([type(audio_data), audio_data.shape], [type(sr), sr])
print("音声ファイルの形式：", audio_data.shape)
print("音声ファイルの長さ：", len(audio_data))

split_audio_data = split_audio(audio_data, sr, split_time=0.3)
# print("分割した音声ファイルの形式：", split_audio_data)
print("分割した音声ファイルの形：", split_audio_data[0].shape)
print("分割した音声ファイルの長さ：", len(split_audio_data))

ms_dict = {}
current_i = 0
previous_note = None

for audio_data in split_audio_data:
    current_note = ms_recognition(audio_data)
    
    # 前回の音階と同じでない場合のみ、ディクショナリに追加する
    if current_note != previous_note:
        ms_dict[current_i] = current_note
        current_i += 1
        previous_note = current_note
        
with open("ms_dict.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(ms_dict, ensure_ascii=False, indent=4))

# 音声データをリアルタイムで処理
# for audio_data in split_audio_data:
#     # print(i, audio_data)
#     ms_dict[current_i] = ms_recognition(audio_data)
#     current_i += 1
    
#     # 8音節ごとに音階データを保存
#     if current_i == 8:
#         print(ms_dict) # 確認用
#         filename = get_next_filename("ms_dict", "json")

#         with open(filename, "w", encoding="utf-8") as f:
#             f.write(json.dumps(ms_dict, ensure_ascii=False, indent=4))
#         print(f"音階データを {filename} に保存しました")
#         current_i = 0
#         ms_dict = {}


