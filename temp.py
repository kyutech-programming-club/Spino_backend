import sounddevice as sd
import numpy as np
import librosa
import os
import json
# from connection import send_data_loop

# 音声ファイルのパス
current_dir = os.path.dirname(os.path.abspath(__file__))
audio_file_path = os.path.join(current_dir, "audio_files", "IMG_3570.mp3")

# ms_dictのパス
ms_dict_path = os.path.join(current_dir, "ms_dict")

# サンプリングレートを設定
sr = 22050  # サンプリングレート
previous_doremi_note = "不明"

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
    split_audio_data = [audio_data[i:i+split_index] for i in range(2*split_index, len(audio_data), split_index)]
    return split_audio_data

# ファイル名の連番を作成する
def get_next_filename(base_filename, extension, i):
    filename = f"{base_filename}_{i}.{extension}"
    return filename

# バイオリンの音階を判定する
def ms_recognition(indata, sr=22050, hop_length=512):
    global previous_doremi_note
    
    # 入力された音声データを取得
    audio_data = indata # 1チャンネル分の音声
    
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
            
            # オクターブが4, 5, 6の範囲内の音階のみを取得
            if octave == "4" or octave == "5" or octave == "6":
                doremi_note = note_to_doremi.get(base_note, "不明") + octave  # ドレミファソラシド形式に変換
            else:
                print("音階が4, 5, 6の範囲外です")
                doremi_note = previous_doremi_note # 直前の音階を返す
            
            print(f"基本周波数: {dominant_f0:.2f} Hz, 音階: {doremi_note}")
            print("------------------------------------------------------------------")
            previous_doremi_note = doremi_note
            return doremi_note
        else:
            print("休符判定")
            print("------------------------------------------------------------------")
            return "休符"
    else:
        print("ピッチ検知に失敗した!!")
        return "検知失敗"

# 音声ファイルを読み込み、リアルタイムで音声を処理
audio_data, sr = librosa.load(audio_file_path, sr=sr)

# 音声ファイルを0.27秒ごとに分割(八部音符の秒数)
split_audio_data = split_audio(audio_data, split_time=0.27, sr=sr)

ms_dict = {}
ms_list = []
current_i = 0
i = 0
previous_note = None

# ms_dict以下のファイルを削除
for file in os.listdir(ms_dict_path):
    file_path = os.path.join(ms_dict_path, file)
    os.remove(file_path)

# フラグ: "ファ5"が検出されたかどうかを追跡
found_fa5 = False

# 音声データをUnityに送信する
for audio_data in split_audio_data:
    detected_note = ms_recognition(audio_data)
    
    # "ファ5"が見つかっていないかつ"ファ5"が検知された場合、フラグをTrueにする
    if not found_fa5 and detected_note == "ファ5":
        print("ファ5が検知されました。ここからJSONファイルを生成します。")
        found_fa5 = True

    # "ファ5"を検知した後のみ、処理を進める
    if found_fa5:
        ms_dict[current_i] = detected_note
        ms_list.append(ms_dict[current_i])
        current_i += 1

        # 1小節分の音階を取得したらUnityに送信する
        if current_i == 8:
            filename = get_next_filename("ms_dict", "json", i)
            ms_save_path= os.path.join(ms_dict_path, filename)
            print("******************************************************************")
            print(f"{i + 1}小節目終了")
            print("******************************************************************")
            
            # Save the data for the measure into a JSON file
            with open(ms_save_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(ms_dict, ensure_ascii=False, indent=4))
            
            # Send the data to Unity
            test = {"key": ','.join(ms_list)}
            print(test)
            # send_data_loop(test)
            print(ms_dict)
            
            # Reset for the next measure
            ms_dict = {}
            current_i = 0
            i += 1

# After the loop, check if there's any leftover data (less than 8 notes)
if current_i > 0 and ms_dict:
    test = {"key": ','.join(ms_list)}
    filename = get_next_filename("ms_dict", "json", i)
    ms_save_path = os.path.join(ms_dict_path, filename)
    print(f"Sending remaining data (less than 8 notes): {current_i} notes.")
    
    # Save remaining notes to a JSON file
    with open(ms_save_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(ms_dict, ensure_ascii=False, indent=4))
    
    # Send the remaining data to Unity
    # send_data_loop(test)

# Print the full list of notes
print(ms_list)