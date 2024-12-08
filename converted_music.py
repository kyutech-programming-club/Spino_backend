from music21 import *
import json
import copy

# C, D, E, F, G, A, B の音符をドレミファソラシドに対応させる辞書
note_to_doremi = {
    'C': 'ド',
    'D': 'レ',
    'E': 'ミ',
    'F': 'ファ',
    'G': 'ソ',
    'A': 'ラ',
    'B': 'シ'
}

# 音符をドレミファソラシドに変換する関数
def note_to_doremi_converter(note):
    pitch = note.name[0]  # 音符の最初の文字が C, D, E などの音名
    return note_to_doremi.get(pitch, pitch)  # 対応するドレミファソラシドを返す

# 音符のオクターブを取得する関数
def get_octave(note):
    return note.pitch.octave if note.isNote else None

# 楽譜をドレミファソラシドとオクターブのリストに変換する関数
def score_to_doremi_list(score):
    notes_list = []

    # パートがあるかを確認
    if hasattr(score, 'parts'):
        # 複数のパートがある場合
        for part in score.parts:  # 楽譜の各パートをループ
            for note in part.flat.notes:  # 各音符をループ
                if note.isNote:  # 音符であるかを確認
                    note_doremi = note_to_doremi_converter(note)  # 音符をドレミファソラシドに変換
                    octave = get_octave(note)  # オクターブを取得
                    # 'ド4'のように音符とオクターブを結合してリストに追加
                    notes_list.append(f"{note_doremi}{octave}")
    else:
        # 単一のパートまたはフラット化されたスコア
        for note in score.flat.notes:
            if note.isNote:
                note_doremi = note_to_doremi_converter(note)
                octave = get_octave(note)
                notes_list.append(f"{note_doremi}{octave}")

    # リスト形式で返す
    return notes_list

# 楽譜の全音符を8分音符に変換する関数
def convert_to_eighth_notes(score):
    new_score = stream.Stream()  # 新しい楽譜を作成
    for part in score.parts:  # 楽譜が複数のパートで構成されている場合
        new_part = stream.Part()
        for note in part.flat.notes:  # 各音符を8分音符に変換
            if note.quarterLength > 0.5:  # 4分音符より長い場合
                num_eighth_notes = int(note.quarterLength / 0.5)
                for _ in range(num_eighth_notes):
                    new_note = copy.deepcopy(note)  # 元の音符をディープコピー
                    new_note.quarterLength = 0.5  # 8分音符の長さに設定
                    new_part.append(new_note)
            else:
                # そのまま8分音符として追加
                new_note = copy.deepcopy(note)  # ディープコピー
                new_note.quarterLength = 0.5  # 8分音符に調整
                new_part.append(new_note)
        new_score.append(new_part)
    return new_score

# メイン処理部分
def main():
    # 楽譜の読み込み
    score = converter.parse('music_score.mxl')

    # 楽譜を8分音符に変換
    new_score = convert_to_eighth_notes(score)

    # 楽譜をドレミファソラシドとオクターブのリストに変換
    doremi_list = score_to_doremi_list(new_score)

    # 結果をファイルに保存（リストをJSON形式に変換して保存）
    with open('doremi_notes_list.json', 'w', encoding='utf-8') as f:
        json.dump(doremi_list, f, ensure_ascii=False, indent=2)

    # コンソールに出力
    print(doremi_list)

# 実行
if __name__ == '__main__':
    main()