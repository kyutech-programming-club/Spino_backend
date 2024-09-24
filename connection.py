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
while True:
    # Enterで送信を開始（入力内容は送信内容と関係ない）
    input_data = input()

    # Unityへ停止命令
    if input_data == "q":
        connector.stop_connection()
        break

    # 送るデータをdictionary形式で
    data = {
        "testValue0": 334,
        "testValue1": "test",
    }

    print(data)

    # Unityへ送る
    connector.send("test", data)
