#!/usr/bin/env python3
"""Synthetic fixtures only, isolated TemporaryDirectory. Never touches live history."""
import copy
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import interview_store as store


def catalog(position):
    return {'position':{'id':position,'employer':'TEST employer','title':'TEST role'},
            'questions':[{'id':f'Q{i:02}','text':f'TEST question {i}?','category':'TEST','intent':'TEST only','criteria':['TEST criterion'],'sources':[]} for i in range(1,21)]}


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='interview-store-test-')
        self.path=Path(self.tmp.name)/'test.sqlite3'
        self.db=store.connect(self.path)
        self.call('import',catalog('A')); self.call('import',catalog('B'))

    def tearDown(self):
        self.db.close(); self.tmp.cleanup()

    def call(self,command,data):
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            return store.run(self.db,command,data)

    def start(self,p='A'):
        return self.call('start',{'position':p,'mode':'coaching'})['session']

    def next(self,s,p='A'):
        return self.call('next',{'position':p,'session':s})['turn']

    def answer(self,t,p='A',text='SYNTHETIC TEST RESPONSE'):
        return self.call('answer',{'position':p,'turn':t['id'],'answer':text})['attempt']

    def score(self,a,score,p='A',override=None):
        values={k:score for k in store.DIMENSIONS}
        if override: values.update(override)
        return self.call('assess',{'position':p,'attempt':a,'rubric':'v1','scores':values,
             'rationales':{k:'Synthetic fixture rationale' for k in store.DIMENSIONS},
             'strength':'TEST strength','improvement':'TEST improvement','next_drill':'TEST drill','evidence_check':'SYNTHETIC fixture; no candidate facts'})

    def finish(self,s,p='A'):
        return self.call('finish',{'position':p,'session':s,'report':'SYNTHETIC TEST REPORT'})

    def test_default_realistic_and_explicit_coaching(self):
        s=self.call('start',{'position':'A'})['session']
        self.assertEqual(self.db.execute('SELECT mode FROM sessions WHERE id=?',(s,)).fetchone()[0],'realistic')
        other=self.call('start',{'position':'B','mode':'coaching'})['session']
        self.assertEqual(self.db.execute('SELECT mode FROM sessions WHERE id=?',(other,)).fetchone()[0],'coaching')

    def test_sqlite_backup_preserves_full_history(self):
        s=self.start(); a=self.answer(self.next(s)); self.score(a,1); self.score(a,3); self.finish(s)
        target=sqlite3.connect(Path(self.tmp.name)/'moved.sqlite3')
        self.db.backup(target)
        self.assertEqual(list(self.db.iterdump()),list(target.iterdump()))
        self.assertEqual(target.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        self.assertEqual(target.execute('PRAGMA foreign_key_check').fetchall(),[])
        target.close()

    def test_seed_contains_no_history(self):
        h=self.call('history',{'position':'A'})
        self.assertEqual(len(h['questions']),20)
        for table in ('sessions','attempts','assessments','completions'): self.assertEqual(h[table],[])

    def test_catalog_idempotent_and_atomic(self):
        self.assertFalse(self.call('import',catalog('A'))['imported'])
        bad=catalog('A'); bad['questions'][-1]['text']='Changed question'
        with self.assertRaises(ValueError): self.call('import',bad)
        self.assertEqual(len(self.call('history',{'position':'A'})['catalogs']),1)
        bad['questions'][-1]['id']='Q20-v2'
        self.call('import',bad)
        self.assertEqual(len(self.call('history',{'position':'A'})['questions']),21)

    def test_resume_pending_and_idempotent_answer(self):
        s=self.start(); t=self.next(s)
        self.assertEqual(self.start(),s)
        self.assertEqual(self.next(s)['id'],t['id'])
        a=self.answer(t); self.assertEqual(self.answer(t),a)
        with self.assertRaises(ValueError): self.answer(t,text='Different TEST response')
        self.assertNotEqual(self.next(s)['question'],t['question'])

    def test_position_isolation_and_foreign_keys(self):
        s=self.start(); t=self.next(s); a=self.answer(t)
        with self.assertRaises(ValueError): self.answer(t,p='B')
        with self.assertRaises(ValueError): self.score(a,2,p='B')
        with self.assertRaises(ValueError): self.next(s,p='B')
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db:
                self.db.execute('INSERT INTO attempts(id,position,turn,answer,source) VALUES (?,?,?,?,?)',('bad','B',t['id'],'TEST','text'))
        self.assertEqual(self.call('history',{'position':'B'})['attempts'],[])

    def test_weak_first_then_new(self):
        s=self.start(); self.score(self.answer(self.next(s)),4)
        self.score(self.answer(self.next(s)),1); self.finish(s)
        self.assertEqual(self.next(self.start())['question'],'Q02')
        self.assertEqual(self.next(self.start('B'),'B')['question'],'Q01')

    def test_single_weak_dimension_prioritised(self):
        s=self.start(); self.score(self.answer(self.next(s)),4)
        self.score(self.answer(self.next(s)),4,override={'evidence':1}); self.finish(s)
        self.assertEqual(self.next(self.start())['question'],'Q02')

    def test_latest_assessment_and_attempt_preserved(self):
        s=self.start(); t=self.next(s); a=self.answer(t)
        self.score(a,0); self.score(a,4); self.finish(s)
        s=self.start(); self.assertEqual(self.next(s)['question'],'Q02')
        self.assertEqual(len(self.call('history',{'position':'A'})['assessments']),2)
        # Same-session retry preserves actual attempts and latest attempt supersedes score.
        t=self.next(s); self.answer(t)
        rt=self.call('retry',{'position':'A','session':s,'turn':t['id']})['turn']
        self.assertNotEqual(rt['id'],t['id'])
        self.answer(rt,text='SECOND SYNTHETIC TEST RESPONSE')
        self.assertEqual(len(self.call('history',{'position':'A'})['attempts']),3)

    def test_unscored_is_not_zero(self):
        s=self.start(); self.answer(self.next(s))
        self.score(self.answer(self.next(s)),1); self.finish(s)
        self.assertEqual(self.next(self.start())['question'],'Q02')

    def test_append_only_and_invalid_scores(self):
        s=self.start(); a=self.answer(self.next(s))
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db: self.db.execute("DELETE FROM attempts")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db: self.db.execute("UPDATE attempts SET answer='overwrite'")
        for score in (-1,5,True,2.5):
            with self.assertRaises(ValueError): self.score(a,score)
        self.assertEqual(self.call('history',{'position':'A'})['assessments'],[])

    def test_empty_and_closed_sessions(self):
        s=self.start(); t=self.next(s)
        with self.assertRaises(ValueError): self.answer(t,text=' ')
        with self.assertRaises(ValueError): self.finish(s)
        self.answer(t); self.finish(s)
        with self.assertRaises(ValueError): self.next(s)
        with self.assertRaises(ValueError): self.answer(t)

    def test_latest_attempt_improvement_changes_selection(self):
        s=self.start(); self.score(self.answer(self.next(s)),0); self.finish(s)
        s=self.start(); t=self.next(s); self.assertEqual(t['question'],'Q01')
        a=self.answer(t,text='IMPROVED SYNTHETIC TEST RESPONSE')
        first=self.score(a,4); again=self.score(a,4)
        self.assertEqual(first['assessment'],again['assessment'])
        self.finish(s)
        self.assertEqual(self.next(self.start())['question'],'Q02')
        h=self.call('history',{'position':'A'})
        self.assertEqual(len(h['attempts']),2)
        self.assertEqual(len(h['assessments']),2)

    def test_retired_question_keeps_history_but_is_not_selected(self):
        s=self.start(); self.score(self.answer(self.next(s)),0); self.finish(s)
        revised=catalog('A'); revised['questions'][0]['id']='Q01-v2'
        revised['questions'][0]['text']='NEW SYNTHETIC QUESTION'
        self.call('import',revised)
        self.assertEqual(self.next(self.start())['question'],'Q01-v2')
        self.assertEqual(len(self.call('history',{'position':'A'})['attempts']),1)

    def test_restart_persistence_and_cli(self):
        s=self.start(); self.answer(self.next(s)); self.db.close()
        self.db=store.connect(self.path)
        self.assertEqual(len(self.call('history',{'position':'A'})['attempts']),1)
        request=Path(self.tmp.name)/'request.json'; request.write_text(json.dumps({'position':'B'}))
        result=subprocess.run([sys.executable,str(Path(store.__file__)), '--db',str(self.path),'history','--input',str(request)],capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout)['attempts'],[])

    def test_block_freezes_eight_and_selects_only_once(self):
        from unittest.mock import patch
        state=self.call('start',{'position':'A'}); s=state['session']
        self.assertEqual(state['planned'],8)
        self.assertEqual(self.db.execute('SELECT count(*) FROM turns WHERE session=?',(s,)).fetchone()[0],1)
        plan=[r[0] for r in self.db.execute('SELECT question FROM block_items WHERE session=? ORDER BY ordinal',(s,))]
        revised=catalog('A'); revised['questions'][1]['id']='Q02-v2'; revised['questions'][1]['text']='CHANGED TEST QUESTION'
        self.call('import',revised)
        with patch.object(store,'ranked',side_effect=AssertionError('No re-ranking during block')):
            self.assertEqual(self.call('start',{'position':'A','size':3})['session'],s)
            for i in range(8):
                self.assertEqual(state['turn']['question'],plan[i])
                state=self.call('answer_next',{'position':'A','turn':state['turn']['id'],'answer':f'SYNTHETIC {i}'})
        self.assertTrue(state['done']); self.assertEqual(state['phase'],'review')
        self.assertEqual(self.db.execute('SELECT count(*) FROM assessments').fetchone()[0],0)

    def test_capture_does_not_read_scores_or_question_evidence(self):
        state=self.call('start',{'position':'A'})
        statements=[]; self.db.set_trace_callback(statements.append)
        result=self.call('answer_next',{'position':'A','turn':state['turn']['id'],'answer':'TEST actual words','source':'voice_transcript','transcript_note':'Unclear word; clarify after block'})
        self.db.set_trace_callback(None)
        self.assertEqual(result['phase'],'capture')
        for query in statements:
            self.assertNotIn('assessments',query.lower())
            self.assertNotIn('select payload from questions',query.lower())
        with self.assertRaises(ValueError): self.score(result['attempt'],3)
        with self.assertRaises(ValueError): self.call('review',{'position':'A','session':state['session']})

    def test_answer_next_retry_resume_and_early_stop(self):
        st=self.call('start',{'position':'A'})
        data={'position':'A','turn':st['turn']['id'],'answer':'SYNTHETIC first'}
        first=self.call('answer_next',data)
        self.db.close(); self.db=store.connect(self.path)
        repeated=self.call('answer_next',data)
        self.assertEqual(repeated['attempt'],first['attempt'])
        self.assertEqual(repeated['turn']['id'],first['turn']['id'])
        resumed=self.call('start',{'position':'A'})
        self.assertEqual(resumed['turn']['id'],first['turn']['id'])
        with self.assertRaises(ValueError): self.call('answer_next',{**data,'answer':'Conflicting TEST'})
        stop=self.call('end_block',{'position':'A','session':st['session']})
        self.assertTrue(stop['done'])
        review=self.call('review',{'position':'A','session':st['session']})
        self.assertEqual(review['actual_answers'],1)
        self.score(first['attempt'],2)
        self.call('finish',{'position':'A','session':st['session'],'report':'TEST final report'})
        self.assertTrue(self.call('answer_next',data)['done'])
        with self.assertRaises(ValueError): self.call('answer_next',{'position':'A','turn':first['turn']['id'],'answer':'Late TEST response'})

    def test_answer_next_rolls_back_if_next_fails(self):
        from unittest.mock import patch
        st=self.call('start',{'position':'A'})
        data={'position':'A','turn':st['turn']['id'],'answer':'ATOMIC TEST'}
        with patch.object(store,'block_next',side_effect=ValueError('Injected TEST failure')):
            with self.assertRaises(ValueError): self.call('answer_next',data)
        self.assertEqual(self.db.execute('SELECT count(*) FROM attempts').fetchone()[0],0)
        self.assertEqual(self.call('next',{'position':'A','session':st['session']})['turn']['id'],st['turn']['id'])
        self.assertTrue(self.call('answer_next',data)['saved'])

    def test_final_answer_retry_and_clarification(self):
        st=self.call('start',{'position':'A','size':1})
        data={'position':'A','turn':st['turn']['id'],'answer':'UNCLEAR SYNTHETIC TRANSCRIPT','transcript_note':'Unclear TEST word'}
        result=self.call('answer_next',data)
        self.assertTrue(result['done'])
        self.assertFalse(self.call('answer_next',data)['saved'])
        clarification={'position':'A','attempt':result['attempt'],'text':'USER TEST CLARIFICATION'}
        first=self.call('clarify',clarification); again=self.call('clarify',clarification)
        self.assertEqual(first,again)
        review=self.call('review',{'position':'A','session':st['session']})
        self.assertEqual(review['answers'][0]['answer'],data['answer'])
        self.assertEqual(len(review['answers'][0]['clarifications']),1)
        self.score(result['attempt'],2)

    def test_legacy_open_session_adopted_without_rewriting(self):
        with self.db:
            self.db.execute("INSERT INTO sessions(id,position,mode) VALUES ('legacy','A','realistic')")
            self.db.execute("INSERT INTO turns(id,position,session,question,prompt) VALUES ('old1','A','legacy','Q03','Original TEST prompt')")
            self.db.execute("INSERT INTO attempts(id,position,turn,answer,source) VALUES ('answer1','A','old1','Original TEST answer','text')")
            self.db.execute("INSERT INTO turns(id,position,session,question,prompt) VALUES ('old2','A','legacy','Q05','Pending TEST prompt')")
        before=[tuple(r) for r in self.db.execute('SELECT * FROM attempts')]
        state=self.call('start',{'position':'A'})
        self.assertEqual(state['session'],'legacy'); self.assertEqual(state['turn']['id'],'old2')
        self.assertEqual(state['planned'],8)
        self.assertEqual(before,[tuple(r) for r in self.db.execute('SELECT * FROM attempts')])
        plan=[r[0] for r in self.db.execute("SELECT question FROM block_items WHERE session='legacy' ORDER BY ordinal")]
        self.assertEqual(plan[:2],['Q03','Q05'])
        self.assertEqual(len(set(plan)),8)

    def test_blocks_and_review_are_position_scoped(self):
        st=self.call('start',{'position':'A','size':1})
        with self.assertRaises(ValueError): self.call('answer_next',{'position':'B','turn':st['turn']['id'],'answer':'TEST'})
        with self.assertRaises(ValueError): self.call('end_block',{'position':'B','session':st['session']})
        with self.assertRaises(ValueError): self.call('review',{'position':'B','session':st['session']})
        result=self.call('answer_next',{'position':'A','turn':st['turn']['id'],'answer':'TEST','stop':True})
        with self.assertRaises(ValueError): self.call('clarify',{'position':'B','attempt':result['attempt'],'text':'TEST'})
        self.assertEqual(self.db.execute("SELECT count(*) FROM blocks WHERE position='B'").fetchone()[0],0)

    def test_batch_assessment_atomic_and_idempotent(self):
        st=self.call('start',{'position':'A','size':1})
        result=self.call('answer_next',{'position':'A','turn':st['turn']['id'],'answer':'TEST'})
        self.score(result['attempt'],3)
        payload=json.loads(self.db.execute('SELECT payload FROM assessments').fetchone()[0])
        with self.assertRaises(ValueError): self.call('assess_many',{'position':'A','assessments':[{**payload,'strength':'changed TEST'}, {**payload,'attempt':'invalid'}]})
        self.assertEqual(self.db.execute('SELECT count(*) FROM assessments').fetchone()[0],1)
        response=self.call('assess_many',{'position':'A','assessments':[payload]})
        self.assertFalse(response['assessments'][0]['saved'])


    def test_concurrent_identical_capture_is_exactly_once(self):
        from concurrent.futures import ThreadPoolExecutor
        state=self.call('start',{'position':'A'})
        request={'position':'A','turn':state['turn']['id'],'answer':'CONCURRENT SYNTHETIC TEST'}
        def worker():
            db=store.connect(self.path)
            try:
                with db:
                    db.execute('BEGIN IMMEDIATE')
                    return store.run(db,'answer_next',request)
            finally:
                db.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:worker(),range(2)))
        self.assertEqual(results[0]['attempt'],results[1]['attempt'])
        self.assertEqual(results[0]['turn']['id'],results[1]['turn']['id'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM attempts').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM turns').fetchone()[0],2)

    def test_stop_without_any_answers_has_no_fake_report(self):
        state=self.call('start',{'position':'A'})
        self.call('end_block',{'position':'A','session':state['session']})
        self.assertEqual(self.call('review',{'position':'A','session':state['session']})['answers'],[])
        with self.assertRaises(ValueError): self.finish(state['session'])
        self.assertNotEqual(self.call('start',{'position':'A'})['session'],state['session'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM completions').fetchone()[0],0)


    def test_candidate_databases_isolate_identical_position_ids(self):
        from unittest.mock import patch
        a=Path(self.tmp.name)/'candidate-a'; b=Path(self.tmp.name)/'candidate-b'
        a.mkdir();b.mkdir()
        with patch.object(store,'DATA_ROOT',Path(self.tmp.name)/'private-data'):
            paths=[store.candidate_database(x) for x in (a,b)]
        self.assertNotEqual(*paths)
        for i,path in enumerate(paths):
            db=store.connect(path)
            try:
                with db:
                    store.run(db,'import',catalog('same-role'))
                    if i==0:
                        state=store.run(db,'start',{'position':'same-role'})
                        store.run(db,'answer_next',{'position':'same-role','turn':state['turn']['id'],'answer':'SYNTHETIC candidate A answer'})
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],1 if i==0 else 0)
            finally:
                db.close()

    def test_candidate_path_is_canonical_and_validated(self):
        path=Path(self.tmp.name)/'knowledge';path.mkdir()
        alias=Path(self.tmp.name)/'alias';alias.symlink_to(path,target_is_directory=True)
        self.assertEqual(store.candidate_database(path),store.candidate_database(alias))
        with self.assertRaises(ValueError):store.candidate_database('relative-path')
        with self.assertRaises(ValueError):store.candidate_database(Path(self.tmp.name)/'missing')

    def test_cli_requires_candidate_or_explicit_database(self):
        request=Path(self.tmp.name)/'req.json';request.write_text('{"position":"A"}')
        result=subprocess.run([sys.executable,'-B',str(Path(store.__file__)),'history','--input',str(request)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('--candidate is required',result.stderr)



if __name__=='__main__':
    unittest.main()
