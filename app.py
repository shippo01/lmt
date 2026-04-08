from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "responses.db"

AGENDA_ITEMS = [
    "第１号議案 令和７年度活動報告の件",
    "第２号議案 令和７年度決算報告の件",
    "第３号議案 令和８年度予算（案）の件",
    "第４号議案 令和８年度役員紹介の件",
    "第５号議案 自治会会則変更の件",
]

app = Flask(__name__)
app.secret_key = "local-dev-secret"


@dataclass
class ResponseRecord:
    attendance: str
    proxy_type: str | None
    votes: List[str | None]
    room_number: str
    full_name: str
    submitted_on: str


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_: object) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attendance TEXT NOT NULL CHECK(attendance IN ('attend', 'absent')),
                proxy_type TEXT CHECK(proxy_type IN ('chair', 'self') OR proxy_type IS NULL),
                vote_1 TEXT CHECK(vote_1 IN ('agree', 'disagree') OR vote_1 IS NULL),
                vote_2 TEXT CHECK(vote_2 IN ('agree', 'disagree') OR vote_2 IS NULL),
                vote_3 TEXT CHECK(vote_3 IN ('agree', 'disagree') OR vote_3 IS NULL),
                vote_4 TEXT CHECK(vote_4 IN ('agree', 'disagree') OR vote_4 IS NULL),
                vote_5 TEXT CHECK(vote_5 IN ('agree', 'disagree') OR vote_5 IS NULL),
                room_number TEXT NOT NULL,
                full_name TEXT NOT NULL,
                submitted_on TEXT NOT NULL,
                UNIQUE(room_number, full_name)
            )
            """
        )


def parse_form(form: Dict[str, str]) -> ResponseRecord:
    attendance = form.get("attendance", "")
    room_number = form.get("room_number", "").strip()
    full_name = form.get("full_name", "").strip()
    submitted_on = form.get("submitted_on", "")

    if attendance not in {"attend", "absent"}:
        raise ValueError("総会への参加可否を選択してください。")
    if not room_number:
        raise ValueError("部屋番号を入力してください。")
    if not full_name:
        raise ValueError("名前を入力してください。")
    if not submitted_on:
        raise ValueError("記入日を入力してください。")

    proxy_type = None
    votes: List[str | None] = [None] * 5

    if attendance == "absent":
        proxy_type = form.get("proxy_type", "")
        if proxy_type not in {"chair", "self"}:
            raise ValueError("不参加の場合は、議決権の行使方法を選択してください。")

        if proxy_type == "chair":
            votes = ["agree"] * 5
        else:
            for idx in range(1, 6):
                key = f"vote_{idx}"
                vote = form.get(key, "")
                if vote not in {"agree", "disagree"}:
                    raise ValueError(f"第{idx}号議案の賛否を選択してください。")
                votes[idx - 1] = vote

    return ResponseRecord(
        attendance=attendance,
        proxy_type=proxy_type,
        votes=votes,
        room_number=room_number,
        full_name=full_name,
        submitted_on=submitted_on,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            record = parse_form(request.form)
            db = get_db()
            db.execute(
                """
                INSERT INTO responses (
                    attendance, proxy_type, vote_1, vote_2, vote_3, vote_4, vote_5,
                    room_number, full_name, submitted_on
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.attendance,
                    record.proxy_type,
                    record.votes[0],
                    record.votes[1],
                    record.votes[2],
                    record.votes[3],
                    record.votes[4],
                    record.room_number,
                    record.full_name,
                    record.submitted_on,
                ),
            )
            db.commit()
            flash("登録しました。", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash("同じ部屋番号・名前ですでに登録されています。", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("index.html", agenda_items=AGENDA_ITEMS, today=date.today().isoformat())


@app.route("/admin")
def admin():
    db = get_db()
    rows = db.execute(
        """
        SELECT attendance, proxy_type, vote_1, vote_2, vote_3, vote_4, vote_5,
               room_number, full_name, submitted_on
        FROM responses
        ORDER BY room_number, full_name
        """
    ).fetchall()

    attendance_summary = {
        "attend": sum(1 for row in rows if row["attendance"] == "attend"),
        "absent": sum(1 for row in rows if row["attendance"] == "absent"),
    }

    vote_totals = []
    for idx in range(1, 6):
        agree = sum(1 for row in rows if row[f"vote_{idx}"] == "agree")
        disagree = sum(1 for row in rows if row[f"vote_{idx}"] == "disagree")
        vote_totals.append({"agenda": AGENDA_ITEMS[idx - 1], "agree": agree, "disagree": disagree})

    absent_details = [row for row in rows if row["attendance"] == "absent"]

    return render_template(
        "admin.html",
        agenda_items=AGENDA_ITEMS,
        attendance_summary=attendance_summary,
        absent_details=absent_details,
        vote_totals=vote_totals,
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
