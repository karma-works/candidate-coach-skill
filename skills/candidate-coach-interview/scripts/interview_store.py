#!/usr/bin/env python3
"""Local append-only interview store. Python standard library only."""
import argparse
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[1] / 'data'

def candidate_database(knowledge_base):
    path = Path(knowledge_base).expanduser()
    if not path.is_absolute() or not path.is_dir():
        raise ValueError('Candidate knowledge base must be an existing absolute directory')
    key = hashlib.sha256(str(path.resolve()).encode()).hexdigest()
    return DATA_ROOT / key / 'interviews.sqlite3'

DIMENSIONS = ('relevance', 'structure', 'evidence', 'judgement', 'communication')
SCHEMA = '''
CREATE TABLE IF NOT EXISTS positions (
 id TEXT PRIMARY KEY, employer TEXT NOT NULL, title TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS catalogs (
 id INTEGER PRIMARY KEY, position TEXT NOT NULL REFERENCES positions(id),
 digest TEXT NOT NULL, payload TEXT NOT NULL,
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 UNIQUE(position,digest));
CREATE TABLE IF NOT EXISTS questions (
 position TEXT NOT NULL REFERENCES positions(id), id TEXT NOT NULL,
 payload TEXT NOT NULL, PRIMARY KEY(position,id));
CREATE TABLE IF NOT EXISTS catalog_questions (
 catalog INTEGER NOT NULL REFERENCES catalogs(id), position TEXT NOT NULL,
 question TEXT NOT NULL, ordinal INTEGER NOT NULL,
 FOREIGN KEY(position,question) REFERENCES questions(position,id),
 PRIMARY KEY(catalog,question));
CREATE TABLE IF NOT EXISTS sessions (
 id TEXT PRIMARY KEY, position TEXT NOT NULL REFERENCES positions(id),
 mode TEXT NOT NULL CHECK(mode IN ('coaching','realistic')),
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 UNIQUE(position,id));
CREATE TABLE IF NOT EXISTS turns (
 id TEXT PRIMARY KEY, position TEXT NOT NULL, session TEXT NOT NULL,
 question TEXT NOT NULL, prompt TEXT NOT NULL,
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 FOREIGN KEY(position,session) REFERENCES sessions(position,id),
 FOREIGN KEY(position,question) REFERENCES questions(position,id),
 UNIQUE(position,id));
CREATE TABLE IF NOT EXISTS attempts (
 id TEXT PRIMARY KEY, position TEXT NOT NULL, turn TEXT NOT NULL,
 answer TEXT NOT NULL, source TEXT NOT NULL CHECK(source IN ('text','voice_transcript')),
 transcript_note TEXT NOT NULL DEFAULT '',
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 FOREIGN KEY(position,turn) REFERENCES turns(position,id),
 UNIQUE(turn), UNIQUE(position,id));
CREATE TABLE IF NOT EXISTS assessments (
 id INTEGER PRIMARY KEY, position TEXT NOT NULL, attempt TEXT NOT NULL,
 rubric TEXT NOT NULL CHECK(rubric='v1'), label TEXT NOT NULL DEFAULT 'Coaching estimate',
 payload TEXT NOT NULL, total REAL NOT NULL CHECK(total BETWEEN 0 AND 4),
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 FOREIGN KEY(position,attempt) REFERENCES attempts(position,id));
CREATE TABLE IF NOT EXISTS completions (
 id INTEGER PRIMARY KEY, position TEXT NOT NULL, session TEXT NOT NULL UNIQUE,
 report TEXT NOT NULL,
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 FOREIGN KEY(position,session) REFERENCES sessions(position,id));

CREATE TABLE IF NOT EXISTS blocks (
 session TEXT PRIMARY KEY, position TEXT NOT NULL, requested_size INTEGER NOT NULL,
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 FOREIGN KEY(position,session) REFERENCES sessions(position,id), UNIQUE(position,session));
CREATE TABLE IF NOT EXISTS block_items (
 session TEXT NOT NULL, position TEXT NOT NULL, ordinal INTEGER NOT NULL,
 question TEXT NOT NULL, prompt TEXT NOT NULL, turn TEXT NOT NULL UNIQUE,
 selection TEXT NOT NULL,
 FOREIGN KEY(position,session) REFERENCES blocks(position,session),
 FOREIGN KEY(position,question) REFERENCES questions(position,id), PRIMARY KEY(session,ordinal));
CREATE TABLE IF NOT EXISTS block_ends (
 session TEXT PRIMARY KEY, position TEXT NOT NULL, reason TEXT NOT NULL,
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 FOREIGN KEY(position,session) REFERENCES blocks(position,session));
CREATE TABLE IF NOT EXISTS clarifications (
 id INTEGER PRIMARY KEY, position TEXT NOT NULL, attempt TEXT NOT NULL,
 text TEXT NOT NULL, source TEXT NOT NULL CHECK(source IN ('text','voice_transcript')),
 created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
 FOREIGN KEY(position,attempt) REFERENCES attempts(position,id), UNIQUE(position,attempt,text,source));
CREATE INDEX IF NOT EXISTS turns_session ON turns(position,session);
CREATE INDEX IF NOT EXISTS assessments_attempt ON assessments(position,attempt);
'''


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def connect(path):
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    if db.execute('PRAGMA user_version').fetchone()[0] >= 2:
        return db
    db.executescript(SCHEMA)
    for table in ('positions','catalogs','questions','catalog_questions','sessions','turns','attempts','assessments','completions','blocks','block_items','block_ends','clarifications'):
        for action in ('UPDATE','DELETE'):
            db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'append-only'); END")
    db.execute('PRAGMA user_version=2')
    db.commit()
    return db


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def session_open(db, position, session):
    require(db.execute('SELECT 1 FROM sessions WHERE position=? AND id=?', (position,session)).fetchone(), 'Unknown session for this position')
    require(not db.execute('SELECT 1 FROM completions WHERE session=?', (session,)).fetchone(), 'Session already finished')


def import_catalog(db, data):
    p = data['position']
    for k in ('id','employer','title'):
        require(nonempty(p[k]), f'Empty position {k}')
    qs = data['questions']
    require(20 <= len(qs) <= 30, 'Catalog must contain 20–30 questions')
    require(len({q['id'] for q in qs}) == len(qs), 'Duplicate question IDs')
    old = db.execute('SELECT * FROM positions WHERE id=?', (p['id'],)).fetchone()
    require(not old or (old['employer'],old['title']) == (p['employer'],p['title']), 'Position ID belongs to a different role')
    db.execute('INSERT OR IGNORE INTO positions VALUES (?,?,?)', (p['id'],p['employer'],p['title']))
    payload = encode(data)
    digest = hashlib.sha256(payload.encode()).hexdigest()
    old_catalog = db.execute('SELECT id FROM catalogs WHERE position=? AND digest=?', (p['id'],digest)).fetchone()
    if old_catalog:
        return {'catalog':old_catalog['id'], 'imported':False}
    cid = db.execute('INSERT INTO catalogs(position,digest,payload) VALUES (?,?,?)', (p['id'],digest,payload)).lastrowid
    for ordinal,q in enumerate(qs):
        for k in ('id','text','category','intent'):
            require(nonempty(q[k]), f'Empty question {k}')
        require(isinstance(q['criteria'],list) and bool(q['criteria']) and all(nonempty(x) for x in q['criteria']), 'Missing question criteria')
        qpayload = encode(q)
        prior = db.execute('SELECT payload FROM questions WHERE position=? AND id=?', (p['id'],q['id'])).fetchone()
        require(not prior or prior['payload']==qpayload, 'Changed question requires a new ID (e.g. Q01-v2); history is immutable')
        db.execute('INSERT OR IGNORE INTO questions VALUES (?,?,?)', (p['id'],q['id'],qpayload))
        db.execute('INSERT INTO catalog_questions VALUES (?,?,?,?)', (cid,p['id'],q['id'],ordinal))
    return {'catalog':cid,'imported':True,'questions':len(qs)}


def ranked(db, position, session):
    catalog = db.execute('SELECT id FROM catalogs WHERE position=? ORDER BY id DESC LIMIT 1',(position,)).fetchone()
    require(catalog, 'No catalog for this position')
    used = {r[0] for r in db.execute('SELECT question FROM turns WHERE position=? AND session=?',(position,session))}
    results = []
    for row in db.execute('SELECT q.payload,cq.ordinal FROM catalog_questions cq JOIN questions q ON q.position=cq.position AND q.id=cq.question WHERE cq.catalog=? ORDER BY cq.ordinal',(catalog['id'],)):
        q = json.loads(row['payload'])
        if q['id'] in used:
            continue
        latest = db.execute('''SELECT a.id FROM attempts a JOIN turns t ON t.id=a.turn
            WHERE a.position=? AND t.question=? ORDER BY a.rowid DESC LIMIT 1''',(position,q['id'])).fetchone()
        score = None
        assessment = None
        if latest:
            assessment = db.execute('SELECT total,payload FROM assessments WHERE position=? AND attempt=? ORDER BY id DESC LIMIT 1',(position,latest['id'])).fetchone()
            if assessment:
                score = assessment['total']
        weak = bool(assessment and (score < 2.5 or min(json.loads(assessment['payload'])['scores'].values()) < 2))
        group = 0 if weak else (1 if score is None else 2)
        q['selection'] = {'reason':'weak' if weak else ('unassessed' if latest and score is None else ('new' if score is None else 'refresh')), 'latest_score':score}
        results.append(((group,score if score is not None else 0,row['ordinal']),q))
    return [q for _,q in sorted(results,key=lambda x:x[0])]



def ended(db,p,s):
    return bool(db.execute('SELECT 1 FROM block_ends WHERE position=? AND session=?',(p,s)).fetchone() or
                db.execute('SELECT 1 FROM completions WHERE position=? AND session=?',(p,s)).fetchone())


def ensure_block(db,p,s,size=8):
    if db.execute('SELECT 1 FROM blocks WHERE position=? AND session=?',(p,s)).fetchone():
        return
    session_open(db,p,s)
    # Adopt old open sessions without rewriting a single turn or answer.
    prior = [dict(r) for r in db.execute('SELECT * FROM turns WHERE position=? AND session=? ORDER BY rowid',(p,s))]
    chosen = [(t['question'],t['prompt'],t['id'],{'reason':'legacy_turn'}) for t in prior]
    if len(chosen) < size:
        chosen.extend((q['id'],q['text'],str(uuid.uuid4()),q['selection']) for q in ranked(db,p,s)[:size-len(chosen)])
    db.execute('INSERT INTO blocks(session,position,requested_size) VALUES (?,?,?)',(s,p,size))
    for i,(q,prompt,turn,selection) in enumerate(chosen,1):
        db.execute('INSERT INTO block_items VALUES (?,?,?,?,?,?,?)',(s,p,i,q,prompt,turn,encode(selection)))


def seal_block(db,p,s,reason):
    db.execute('INSERT OR IGNORE INTO block_ends(session,position,reason) VALUES (?,?,?)',(s,p,reason))


def block_next(db,p,s):
    total = db.execute('SELECT count(*) FROM block_items WHERE position=? AND session=?',(p,s)).fetchone()[0]
    if ended(db,p,s):
        return {'done':True,'phase':'review','planned':total}
    # Includes an explicit coaching retry or a legacy pending turn.
    pending = db.execute('SELECT t.* FROM turns t LEFT JOIN attempts a ON a.turn=t.id WHERE t.position=? AND t.session=? AND a.id IS NULL ORDER BY t.rowid LIMIT 1',(p,s)).fetchone()
    if pending:
        return {'turn':{'id':pending['id'],'question':pending['question'],'prompt':pending['prompt']},'pending':True,'phase':'capture','planned':total}
    item = db.execute('SELECT bi.* FROM block_items bi LEFT JOIN attempts a ON a.turn=bi.turn WHERE bi.position=? AND bi.session=? AND a.id IS NULL ORDER BY bi.ordinal LIMIT 1',(p,s)).fetchone()
    if not item:
        seal_block(db,p,s,'completed')
        return {'done':True,'phase':'review','planned':total}
    db.execute('INSERT INTO turns(id,position,session,question,prompt) VALUES (?,?,?,?,?)',(item['turn'],p,s,item['question'],item['prompt']))
    return {'turn':{'id':item['turn'],'question':item['question'],'prompt':item['prompt']},'pending':False,'phase':'capture','planned':total}


def require_review(db,p,s):
    row = db.execute('SELECT mode FROM sessions WHERE position=? AND id=?',(p,s)).fetchone()
    require(row,'Unknown session for this position')
    require(row['mode']=='coaching' or ended(db,p,s), 'Analysis is deferred until end_block or all planned answers are captured')


def run(db, command, d):
    if command == 'import':
        return import_catalog(db,d)
    p = d['position']
    require(db.execute('SELECT 1 FROM positions WHERE id=?',(p,)).fetchone(), 'Unknown position')
    if command == 'start':
        require(db.execute('SELECT 1 FROM catalogs WHERE position=?',(p,)).fetchone(), 'No catalog')
        existing = db.execute('''SELECT id FROM sessions s WHERE position=? AND id NOT IN (SELECT session FROM completions)
            AND NOT (EXISTS (SELECT 1 FROM block_ends e WHERE e.session=s.id)
              AND NOT EXISTS (SELECT 1 FROM turns t JOIN attempts a ON a.turn=t.id WHERE t.session=s.id))
            ORDER BY rowid DESC LIMIT 1''',(p,)).fetchone()
        size = d.get('size',8)
        require(type(size) is int and 1 <= size <= 30, 'Block size must be 1–30')
        if existing:
            sid = existing['id']
        else:
            sid = str(uuid.uuid4())
            db.execute('INSERT INTO sessions(id,position,mode) VALUES (?,?,?)',(sid,p,d.get('mode','realistic')))
        ensure_block(db,p,sid,size)
        mode = db.execute('SELECT mode FROM sessions WHERE id=?',(sid,)).fetchone()[0]
        return {'session':sid,'resumed':bool(existing),'mode':mode,**block_next(db,p,sid)}
    if command == 'retry':
        s = d['session']; session_open(db,p,s)
        require(db.execute('SELECT mode FROM sessions WHERE id=?',(s,)).fetchone()[0]=='coaching', 'Immediate retry is only for explicit coaching mode; clarify after the realistic block')
        require(not ended(db,p,s), 'Block already ended')
        old = db.execute('SELECT t.* FROM turns t JOIN attempts a ON a.turn=t.id WHERE t.position=? AND t.session=? AND t.id=?',(p,s,d['turn'])).fetchone()
        require(old, 'Retry requires an answered turn in this position and session')
        pending = db.execute('SELECT t.* FROM turns t LEFT JOIN attempts a ON a.turn=t.id WHERE t.position=? AND t.session=? AND a.id IS NULL',(p,s)).fetchone()
        if pending:
            require(pending['question']==old['question'], 'Another question is pending')
            return {'turn':dict(pending),'pending':True}
        tid = str(uuid.uuid4())
        db.execute('INSERT INTO turns(id,position,session,question,prompt) VALUES (?,?,?,?,?)',(tid,p,s,old['question'],old['prompt']))
        return {'turn':{'id':tid,'question':old['question'],'prompt':old['prompt']},'pending':False}
    if command == 'next':
        session_open(db,p,d['session'])
        ensure_block(db,p,d['session'])
        return block_next(db,p,d['session'])
    if command == 'answer_next':
        require(type(d.get('stop',False)) is bool,'stop must be boolean')
        t = db.execute('SELECT * FROM turns WHERE position=? AND id=?',(p,d['turn'])).fetchone()
        require(t,'Unknown turn for this position')
        # An identical retry can recover after the final answer or a closed session.
        prior = db.execute('SELECT * FROM attempts WHERE turn=?',(d['turn'],)).fetchone()
        if prior:
            require((prior['answer'],prior['source'],prior['transcript_note']) ==
                    (d['answer'],d.get('source','text'),d.get('transcript_note','')), 'Conflicting retry; answer is immutable')
            result = {'attempt':prior['id'],'saved':False}
        else:
            result = run(db,'answer',d)
        ensure_block(db,p,t['session'])
        if d.get('stop',False):
            seal_block(db,p,t['session'],'early_stop')
        return {**result,**block_next(db,p,t['session'])}
    if command == 'end_block':
        session_open(db,p,d['session'])
        ensure_block(db,p,d['session'])
        seal_block(db,p,d['session'],'early_stop')
        return block_next(db,p,d['session'])
    if command == 'review':
        s = d['session']; require_review(db,p,s)
        answers = []
        for row in db.execute('SELECT a.*,t.question,t.prompt FROM attempts a JOIN turns t ON t.id=a.turn WHERE a.position=? AND t.session=? ORDER BY a.rowid',(p,s)):
            item = dict(row)
            item['question_context'] = json.loads(db.execute('SELECT payload FROM questions WHERE position=? AND id=?',(p,row['question'])).fetchone()[0])
            item['clarifications'] = [dict(r) for r in db.execute('SELECT * FROM clarifications WHERE position=? AND attempt=? ORDER BY id',(p,row['id']))]
            item['assessments'] = [dict(r) for r in db.execute('SELECT * FROM assessments WHERE position=? AND attempt=? ORDER BY id',(p,row['id']))]
            answers.append(item)
        return {'session':s,'answers':answers,'actual_answers':len(answers)}
    if command == 'clarify':
        row = db.execute('SELECT t.session FROM attempts a JOIN turns t ON t.id=a.turn WHERE a.position=? AND a.id=?',(p,d['attempt'])).fetchone()
        require(row,'Unknown attempt for this position'); require_review(db,p,row['session'])
        require(nonempty(d['text']),'Empty clarification')
        db.execute('INSERT OR IGNORE INTO clarifications(position,attempt,text,source) VALUES (?,?,?,?)',(p,d['attempt'],d['text'],d.get('source','text')))
        return {'clarification':db.execute('SELECT id FROM clarifications WHERE position=? AND attempt=? AND text=? AND source=?',(p,d['attempt'],d['text'],d.get('source','text'))).fetchone()[0]}
    if command == 'assess_many':
        require(isinstance(d['assessments'],list),'Assessments must be a list')
        return {'assessments':[run(db,'assess',{**a,'position':p}) for a in d['assessments']]}
    if command == 'answer':
        t = db.execute('SELECT * FROM turns WHERE position=? AND id=?',(p,d['turn'])).fetchone()
        require(t,'Unknown turn for this position'); session_open(db,p,t['session'])
        require(not ended(db,p,t['session']), 'Block already ended; use clarify for transcript corrections')
        require(nonempty(d['answer']), 'Empty answers cannot be scored; leave the turn pending')
        source = d.get('source','text'); note = d.get('transcript_note','')
        prior = db.execute('SELECT * FROM attempts WHERE turn=?',(d['turn'],)).fetchone()
        if prior:
            require((prior['answer'],prior['source'],prior['transcript_note']) == (d['answer'],source,note), 'Answer exists. Use a new session for another attempt; never replace it')
            return {'attempt':prior['id'],'saved':False}
        aid = str(uuid.uuid4())
        db.execute('INSERT INTO attempts(id,position,turn,answer,source,transcript_note) VALUES (?,?,?,?,?,?)',(aid,p,d['turn'],d['answer'],source,note))
        return {'attempt':aid,'saved':True}
    if command == 'assess':
        row = db.execute('SELECT t.session FROM attempts a JOIN turns t ON t.id=a.turn WHERE a.position=? AND a.id=?',(p,d['attempt'])).fetchone()
        require(row,'Unknown attempt for this position'); require_review(db,p,row['session'])
        scores = d['scores']
        require(set(scores)==set(DIMENSIONS), 'All five rubric dimensions are required')
        require(all(type(v) is int and 0 <= v <= 4 for v in scores.values()), 'Scores must be integers 0–4')
        require(d.get('rubric')=='v1', 'Unsupported rubric')
        require(set(d['rationales'])==set(DIMENSIONS) and all(nonempty(x) for x in d['rationales'].values()), 'Provide a rationale for every dimension')
        for k in ('strength','improvement','next_drill','evidence_check'):
            require(nonempty(d[k]), f'Missing {k}')
        require(db.execute('SELECT 1 FROM attempts WHERE position=? AND id=?',(p,d['attempt'])).fetchone(), 'Unknown attempt for this position')
        total = sum(scores.values())/len(DIMENSIONS)
        previous = db.execute('SELECT id,payload FROM assessments WHERE position=? AND attempt=? ORDER BY id DESC LIMIT 1',(p,d['attempt'])).fetchone()
        if previous and previous['payload']==encode(d):
            return {'assessment':previous['id'],'total':total,'saved':False}
        aid = db.execute('INSERT INTO assessments(position,attempt,rubric,payload,total) VALUES (?,?,?,?,?)',(p,d['attempt'],'v1',encode(d),total)).lastrowid
        return {'assessment':aid,'total':total,'label':'Coaching estimate','saved':True}
    if command == 'finish':
        s = d['session']; session_open(db,p,s)
        mode = db.execute('SELECT mode FROM sessions WHERE id=?',(s,)).fetchone()[0]
        if mode == 'coaching':
            ensure_block(db,p,s); seal_block(db,p,s,'early_stop')
        require_review(db,p,s)
        require(nonempty(d['report']), 'Provide concrete end-of-session coaching')
        count = db.execute('SELECT count(*) FROM attempts a JOIN turns t ON t.id=a.turn WHERE t.position=? AND t.session=?',(p,s)).fetchone()[0]
        require(count > 0, 'No real answers: do not create a training report')
        db.execute('INSERT INTO completions(position,session,report) VALUES (?,?,?)',(p,s,d['report']))
        return {'session':s,'finished':True,'attempts':count}
    if command == 'history':
        result = {}
        for table in ('catalogs','questions','sessions','turns','attempts','assessments','completions','blocks','block_items','block_ends','clarifications'):
            result[table] = [dict(r) for r in db.execute(f'SELECT * FROM {table} WHERE position=? ORDER BY rowid',(p,))]
        return result
    raise ValueError('Unknown command')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,help='Explicit database for isolated tests or approved migration')
    parser.add_argument('--candidate',type=Path,help='Configured absolute knowledge-base directory; required unless --db is given')
    parser.add_argument('command',choices=['import','start','next','retry','answer','answer_next','end_block','review','clarify','assess','assess_many','finish','history'])
    parser.add_argument('--input',type=Path,required=True,help='UTF-8 JSON request file; no shell interpolation of transcripts')
    args = parser.parse_args()
    if args.db is None and args.candidate is None:
        parser.error('--candidate is required unless an explicit --db is supplied')
    try:
        database = args.db if args.db is not None else candidate_database(args.candidate)
    except ValueError as exc:
        parser.error(str(exc))
    db = connect(database)
    try:
        with db:
            # Serialize selection and append operations, including concurrent retries.
            db.execute('BEGIN IMMEDIATE')
            result = run(db,args.command,json.loads(args.input.read_text()))
        print(encode(result))
    except (ValueError,KeyError,TypeError,sqlite3.Error) as exc:
        parser.exit(1, f'Interview store: {exc}\n')
    finally:
        db.close()


if __name__ == '__main__':
    main()
