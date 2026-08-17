# -*- coding: utf-8 -*-
import sqlite3,json
from datetime import datetime,timezone
from .config import DB_FILES

def connect_db(path):
    c=sqlite3.connect(str(path)); c.row_factory=sqlite3.Row; c.execute('PRAGMA journal_mode=WAL'); return c

def init_db(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY AUTOINCREMENT, issue_no TEXT UNIQUE, draw_date TEXT, numbers_json TEXT, special INTEGER, source TEXT, created_at TEXT, updated_at TEXT)'); conn.commit()

def save_draw(conn,issue,date,numbers,special,source='api'):
    now=datetime.now(timezone.utc).isoformat(); payload=json.dumps(numbers,ensure_ascii=False)
    old=conn.execute('SELECT id,numbers_json,special FROM draws WHERE issue_no=?',(str(issue),)).fetchone()
    if old:
        if old['numbers_json']==payload and int(old['special'])==int(special): return 'unchanged'
        conn.execute('UPDATE draws SET draw_date=?,numbers_json=?,special=?,source=?,updated_at=? WHERE issue_no=?',(date,payload,special,source,now,str(issue))); conn.commit(); return 'updated'
    conn.execute('INSERT INTO draws(issue_no,draw_date,numbers_json,special,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?)',(str(issue),date,payload,special,source,now,now)); conn.commit(); return 'inserted'

def load_rows(conn):
    rs=conn.execute('SELECT issue_no,draw_date,numbers_json,special,source FROM draws ORDER BY draw_date DESC,issue_no DESC').fetchall(); out=[]
    for r in rs:
        try: out.append({'issue_no':r['issue_no'],'draw_date':r['draw_date'] or '','numbers':json.loads(r['numbers_json']),'special':int(r['special']),'source':r['source'] or ''})
        except: pass
    return out
