from flask import Flask, render_template, request, redirect
import sqlite3, os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "auto.db")


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def safe_int(v):
    try:
        return int(v)
    except:
        return None


def has_observatii(db):
    cols = db.execute("PRAGMA table_info(masini)").fetchall()
    return "observatii" in [c[1] for c in cols]


def init_db():
    db = get_db()

    db.execute("""
    CREATE TABLE IF NOT EXISTS masini(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT,
        model TEXT,
        numar TEXT,
        km INTEGER,
        next_service INTEGER,
        next_oil INTEGER
    )
    """)

    db.commit()
    db.close()


# 🔴 MOD LUNAR
def calc_status(m):
    km = m["km"] or 0

    if m["next_service"] and km >= m["next_service"]:
        return 0
    if m["next_oil"] and km >= m["next_oil"]:
        return 0

    if m["next_service"] and (m["next_service"] - km) <= 3000:
        return 1
    if m["next_oil"] and (m["next_oil"] - km) <= 3000:
        return 1

    return 2


@app.route("/", methods=["GET", "POST"])
def index():

    q = ""

    if request.method == "POST":
        q = request.form.get("q", "").strip()
    else:
        q = request.args.get("q", "").strip()

    db = get_db()

    masini = db.execute("SELECT * FROM masini").fetchall()

    # 🔴 FILTRARE PYTHON (100% sigur)
    if q:
        q_lower = q.lower()
        masini = [
            m for m in masini
            if (m["marca"] and q_lower in m["marca"].lower())
            or (m["model"] and q_lower in m["model"].lower())
            or (m["numar"] and q_lower in m["numar"].lower())
        ]

    # status + sortare
    status_list = []
    rosu = portocaliu = verde = 0

    for m in masini:
        s = calc_status(m)

        if s == 0:
            rosu += 1
        elif s == 1:
            portocaliu += 1
        else:
            verde += 1

        status_list.append((m, s))

    status_list.sort(key=lambda x: x[1])
    masini = [m[0] for m in status_list]

    db.close()

    return render_template(
        "index.html",
        masini=masini,
        rosu=rosu,
        portocaliu=portocaliu,
        verde=verde,
        cautare=q
    )


@app.route("/add", methods=["POST"])
def add():
    db = get_db()

    km = safe_int(request.form.get("km"))
    s = safe_int(request.form.get("next_service"))
    o = safe_int(request.form.get("next_oil"))

    if has_observatii(db):
        db.execute("""
        INSERT INTO masini (marca, model, numar, km, next_service, next_oil, observatii)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("marca"),
            request.form.get("model"),
            request.form.get("numar"),
            km,
            km + s if km and s else None,
            km + o if km and o else None,
            request.form.get("observatii")
        ))
    else:
        db.execute("""
        INSERT INTO masini (marca, model, numar, km, next_service, next_oil)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("marca"),
            request.form.get("model"),
            request.form.get("numar"),
            km,
            km + s if km and s else None,
            km + o if km and o else None
        ))

    db.commit()
    db.close()
    return redirect("/")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    db = get_db()
    m = db.execute("SELECT * FROM masini WHERE id=?", (id,)).fetchone()

    if request.method == "POST":

        km = safe_int(request.form.get("km"))
        s = safe_int(request.form.get("next_service"))
        o = safe_int(request.form.get("next_oil"))

        if has_observatii(db):
            db.execute("""
            UPDATE masini
            SET marca=?, model=?, numar=?, km=?, next_service=?, next_oil=?, observatii=?
            WHERE id=?
            """, (
                request.form.get("marca"),
                request.form.get("model"),
                request.form.get("numar"),
                km,
                km + s if km and s else None,
                km + o if km and o else None,
                request.form.get("observatii"),
                id
            ))
        else:
            db.execute("""
            UPDATE masini
            SET marca=?, model=?, numar=?, km=?, next_service=?, next_oil=?
            WHERE id=?
            """, (
                request.form.get("marca"),
                request.form.get("model"),
                request.form.get("numar"),
                km,
                km + s if km and s else None,
                km + o if km and o else None,
                id
            ))

        db.commit()
        db.close()
        return redirect("/")

    db.close()
    return render_template("edit.html", m=m)


@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    db.execute("DELETE FROM masini WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)