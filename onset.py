import numpy as np
import sounddevice as sd
import librosa
import queue
from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt

# 設定
samplerate = 22050  # サンプリングレート
blocksize = 1024    # ブロックサイズ
onset_threshold = 0.01  # オンセット検出の閾値
noise_gate_threshold = 0.02  # ノイズゲートの閾値

# バンドパスフィルタを作成（ファ#4の範囲にフィルタ）
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs):
    b, a = butter_bandpass(lowcut, highcut, fs)
    return lfilter(b, a, data)

def noise_gate(data, threshold):
    # ノイズゲートを適用
    return np.where(np.abs(data) < threshold, 0, data)

# 音声データを格納するキュー
audio_queue = queue.Queue()
onset_detected = False  # オンセット検知フラグ
audio_buffer = []  # 音声データを蓄積するバッファ

# 音声データ取得のコールバック関数
def callback(indata, frames, time, status):
    if status:
        print(status)
    # キューに音声データを追加
    audio_queue.put(indata.copy())

# オンセット検出用関数
def detect_onset(y):
    # オンセットを検出
    onsets = librosa.onset.onset_detect(y=y, sr=samplerate, hop_length=512, units='time')
    return onsets

# ファ#4の周波数範囲に設定（約368.29Hz〜371.69Hz）
lowcut = 368.29
highcut = 371.69

# ストリーミングの開始
with sd.InputStream(samplerate=samplerate, channels=1, blocksize=blocksize, callback=callback):
    print("リアルタイム音声検知を開始します...")
    
    while True:
        # キューからデータを取得
        if not audio_queue.empty():
            # 音声データを取得
            audio_data = audio_queue.get()
            audio_buffer.append(audio_data.flatten())  # 1次元配列に変換し、バッファに追加

            # バッファのサイズが一定以上になったら処理
            if len(audio_buffer) * blocksize >= 2048:  # バッファのサンプル数が2048以上
                # バッファの音声データを結合
                combined_audio = np.concatenate(audio_buffer)
                
                # ノイズゲートを適用
                gated_audio = noise_gate(combined_audio, noise_gate_threshold)
                
                # ファ#4の範囲にフィルタリング
                filtered_audio = bandpass_filter(gated_audio, lowcut, highcut, samplerate)
                
                # 音声データの振幅を正規化（ゼロ除算を避ける）
                max_value = np.max(np.abs(filtered_audio))
                if max_value > 0:
                    filtered_audio = filtered_audio / max_value
                
                # オンセットを検出
                onsets = detect_onset(filtered_audio)

                if len(onsets) > 0 and not onset_detected:
                    print(f'演奏が始まった時間: {onsets[0]:.2f}秒')
                    onset_detected = True  # 最初のオンセットを検知したのでフラグを立てる
                    
                    # 波形を表示
                    plt.figure(figsize=(10, 4))
                    plt.plot(filtered_audio)
                    plt.title("Filtered Audio Waveform (F#4 Range)")
                    plt.xlabel("Samples")
                    plt.ylabel("Amplitude")
                    plt.show()
                    
                    break  # ループを終了

    print("プログラムを終了します。")