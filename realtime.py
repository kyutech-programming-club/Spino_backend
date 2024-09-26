import sounddevice as sd
import numpy as np
import librosa
import json
import os

from connection import send_data_loop

# 定数の設定
SR = 22050  # サンプリングレート(Hz)
DURATION = 0.0086  # 110BPMの場合の八分音符の秒数
BLOCK_SIZE = int(SR * DURATION)  # 0.27秒分のサンプル数

# 音階名を保存するフォルダのパス
current_dir = os.path.dirname(os.path.abspath(__file__))
ms_dict_path = os.path.join(current_dir, "ms_dict")

# 答えの音階が書いてあるjsonのパス
ans_json_path = os.path.join(current_dir, "doremi_notes_list.json")

# UTF-8 エンコーディングでJSONファイルを読み込む
with open(ans_json_path, 'r', encoding='utf-8') as json_file:
    json_load = json.load(json_file)
    print("正解ファイルの読み取りに成功!!")

ans_json_path_length = len(json_load)
print(f"正解ファイルの長さ: {ans_json_path_length}")
print("-----------------------------------------------------")

# 音階変換用の辞書
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

# フラグやグローバル変数の初期化
found_fa5 = False
ms_dict = {}
ms_list = []
previous_doremi_note = "不明"
doremi_note = "不明"
current_i = 0
i = 0

# ファイル名の連番を作成する
def get_next_filename(base_filename, extension, i):
    return f"{base_filename}_{i}.{extension}"

# 音声データの処理（基本周波数と音階を推定）
def ms_recognition(audio_data):
    global previous_doremi_note, doremi_note
    f0, _, _ = librosa.pyin(audio_data, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=SR, hop_length=256)
    
    if f0 is not None:
        valid_f0 = f0[~np.isnan(f0)]
        if len(valid_f0) > 0:
            # nanを除いた周波数の平均を取得
            dominant_f0 = np.mean(valid_f0)
            note = librosa.hz_to_note(dominant_f0) # 周波数を対応する音階に変換する
            
            base_note = note[:-1]
            octave = note[-1]
            
            if octave in ["4", "5", "6"]:
                doremi_note = note_to_doremi.get(base_note, "不明") + octave
            else:
                print("音階が4, 5, 6の範囲外です")
                doremi_note = previous_doremi_note
            print(f"基本周波数: {dominant_f0:.2f} Hz, 音階: {doremi_note}")
            previous_doremi_note = doremi_note
            return doremi_note
        else:
            print("休符判定")
            return "休符"
    else:
        print("ピッチ検知に失敗した!!")
        return "検知失敗"

# ファイルにJSONデータを保存
def save_to_json(ms_dict, i):
    filename = get_next_filename("ms_dict", "json", i)
    ms_save_path = os.path.join(ms_dict_path, filename)
    with open(ms_save_path, "w", encoding="utf-8") as f:
        json.dump(ms_dict, f, ensure_ascii=False, indent=4)
    print(f"JSONファイルを保存しました: {ms_save_path}")

# Unityにデータを送信
def send_data_to_unity(ms_list):
    data = {"key": ','.join(ms_list)}
    print(f"Unityにデータを送信: {data}")
    send_data_loop(data)  # 実際のデータ送信処理

# コールバック関数
def audio_callback(indata, frames, time, status):
    global found_fa5, current_i, i, ms_dict, ms_list
    
    if status:
        print(status)
    
    # 音声データの処理
    audio_data = indata[:, 0]  # 1チャンネル分の音声
    doremi_note = ms_recognition(audio_data)
    print(f"検出された音階: {doremi_note}")
    print("----------------------------------------------------")
    # "ファ5"検出フラグの確認
    if not found_fa5 and doremi_note == "ファ5":
        print("ファ5が検知されました。JSONファイルを生成開始。")
        found_fa5 = True

    # "ファ5"が検出された後の処理
    if found_fa5:
        ms_dict[current_i] = doremi_note
        ms_list.append(ms_dict[current_i])
        current_i += 1

        # 1小節分の音階を処理
        if current_i == 8:
            print(f"{i + 1}小節目のデータを保存します。-------------------------------")
            save_to_json(ms_dict, i)
            send_data_to_unity(ms_list)
            print("------------------------------------------------------------")
            # 次の小節のためにリセット
            ms_dict = {}
            current_i = 0
            i += 1

# ms_dict以下のファイルを削除
for file in os.listdir(ms_dict_path):
    file_path = os.path.join(ms_dict_path, file)
    os.remove(file_path)

# ストリームを開始し、リアルタイムで音声を処理
def start_stream():
    global ms_list
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=SR, blocksize=BLOCK_SIZE):
        print("リアルタイム音声処理中... Ctrl+C で終了")
        sd.sleep(60000)  # 1分間録音（任意の時間に設定可能）
        
    print(ms_list)
    print(f"音符の数: {len(ms_list)}")
    
    # 8個未満の音符を保存
    if current_i > 0 and ms_dict:
        test = {"key": ','.join(ms_list)}
        filename = get_next_filename("ms_dict", "json", i)
        ms_save_path = os.path.join(ms_dict_path, filename)
        print(f"Sending remaining data (less than 8 notes): {current_i} notes.")
        
        # Save remaining notes to a JSON file
        with open(ms_save_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(ms_dict, ensure_ascii=False, indent=4))
        # Send the remaining data to Unity
        send_data_loop(test)

    # Unityに送信する音階の数を、正解の数と同数にする処理
    sub_ms = ans_json_path_length - len(ms_list)
    print(sub_ms)
    # 正解の音階の数よりも推定された音階の数が少なかったら
    if sub_ms > 0:
        # ms_listが空でない場合に末尾の要素を複製
        if ms_list:
            last_note = ms_list[-1]  # 最後の要素を取得
            for _ in range(sub_ms):
                ms_list.append(last_note)  # 末尾の要素を複製して追加
        else:
            print("ms_listが空です。")
            # 必要に応じてデフォルト値を設定
            for _ in range(sub_ms):
                ms_list.append("休符")  # 休符で埋めるなど
    elif sub_ms < 0:
        ms_list = ms_list[:ans_json_path_length]
    else:
        pass
    
    if len(ms_list) == ans_json_path_length:
        print("同数に調整できました")
    test = {"key": ','.join(ms_list)}
    send_data_loop(test)
    print(test)
    
if __name__ == "__main__":
    start_stream()
