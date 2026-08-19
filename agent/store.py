import sqlite3
from .config import DATA
DB = DATA / "atlas-lite.db"
def connect():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; return con
def customer(cid):
    with connect() as con:
        r = con.execute("select id,name,email,plan,balance,status from customers where id=?", (cid,)).fetchone()
        return dict(r) if r else None
def refunds():
    with connect() as con: return [dict(r) for r in con.execute("select * from refunds order by id")]
def notes():
    with connect() as con: return [dict(r) for r in con.execute("select * from notes order by id")]
