try:
  import sqlite3
except Exception:
  import pysqlite3 as sqlite3 # type: ignore

from typing import TypedDict, cast


db_path = "db/JazzStandardBible.db"

class Song:
  def __init__(self, id:int, book_num: int, song_name: str, composer: str, M_m: str, key: str, beat: str, type: str):
    self.id = id
    self.book_num = book_num
    self.song_name = song_name
    self.composer = composer
    self.M_m = M_m
    self.key = key
    self.beat = beat
    self.type = type


def get_songs(condition_dict: dict[str, list[str]], limit: int = 3) -> list[Song]:
  with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    base_query = "SELECT id, book_num, song_name, composer, M_m, key, beat, type FROM songs"
    conditions = []
    params = []

    for key, condition_list in condition_dict.items():
      if condition_list and not "全て" in condition_list:
        placeholders = ", ".join(["?"] * len(condition_list))
        conditions.append(f"{key} IN ({placeholders})")
        params.extend(condition_list)

    query = base_query
    if conditions:
      query += " WHERE " + " AND ".join(conditions)

    # ランダムに並び替えて、指定された数だけ取得
    query += " ORDER BY RANDOM() LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    result_data = cursor.fetchall()

  # 取得したデータをSongオブジェクトのリストに変換
  songs = [
    Song(
      id=item[0],
      book_num=item[1],
      song_name=item[2],
      composer=item[3],
      M_m=item[4],
      key=item[5],
      beat=item[6],
      type=item[7]
    ) for item in result_data
  ]

  return songs


class Choices(TypedDict):
  book_num: list[int]
  M_m: list[str]
  key: list[str]
  beat: list[str]
  type: list[str]


def get_choices() -> Choices:
  choices: Choices = {
    "book_num": [],
    "M_m": [],
    "key": [],
    "beat": [],
    "type": []
  }

  target_columns = list(choices.keys())

  with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()

    for column in target_columns:
      query = f"SELECT DISTINCT {column} FROM songs ORDER BY {column}"
      cursor.execute(query)

      results_in_tuple = cursor.fetchall()

      unique_values = [item[0] for item in results_in_tuple if item[0] is not None]
      unique_values.insert(0, "全て")

      choices[cast(str, column)] = unique_values

  return choices