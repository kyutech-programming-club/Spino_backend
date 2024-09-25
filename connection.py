import json
from UnityConnector import UnityConnector

# タイムアウト時のコールバック
def on_timeout():
    print("timeout")

# Unityから停止命令が来たときのコールバック
def on_stopped():
    print("stopped")

# インスタンス
connector = UnityConnector(on_timeout=on_timeout, on_stopped=on_stopped)

# データが飛んできたときのコールバック
def on_data_received(data_type, data):
    print(data_type, data)

print("connecting...")

# Unity側の接続を待つ
connector.start_listening(on_data_received)

print("connected")

# デモ用のループ
def send_data_loop(data):
        # 送るデータをJSON形式に変換
        json_data = json.dumps(data)
        print(f"send_data: {data}")

        # Unityへ送る
        connector.send("test", data)

if __name__ == "__main__":
    send_data_loop({"test": "test"})
