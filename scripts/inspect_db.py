import sqlite3


def main():
    con = sqlite3.connect("sofew.db")
    cur = con.cursor()
    cur.execute(
        "select recording_id,status,error_code,error_message from recording_meta where recording_id=?",
        ("local-test-device_20260106_200309",),
    )
    row = cur.fetchone()
    print(row)


if __name__ == "__main__":
    main()


