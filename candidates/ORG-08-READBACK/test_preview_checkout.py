"""Prepared actual-source integration scenarios. Run only in exact disposable checkout.
Never auto-discover or rerun the parent 11 scenarios; explicit suite below.
"""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
import sys
import unittest


def main():
    root=Path(__file__).resolve().parents[2]
    from preview_reader import review_project, verify_checkout
    from preview_boundary import ReviewPins, Hold, hold_preview
    try:
        verify_checkout()
    except (Hold,OSError):
        print('CHECKOUT_HOLD: exact selected source/dependency verification unavailable',file=sys.stderr)
        return 2
    sys.path.insert(0,str(root/'candidates/ORG-06'))
    # This original module verifies 21 Git blob pins before importing owner code.
    import test_org_core_checkout as original
    from durable_ops import ReadSession, OfficePin, TaskPin
    from office_bridge import OfficeView, Room, Station, Avatar, RoomLink, PairProposal
    sys.path.insert(0,str(root/'candidates/ORG-07A'))
    from studio_router import build_router, ServerReadContext, ROUTE
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    class PreviewChecks(original.CheckoutTests):
        def setup_office(self):
            t,c,_=self.scope.key()
            self.office=OfficeView(t,c,'d0-world','layout-r1',
                (Room('d0-f1/work','d0-f1','WORK'),Room('d0-f1/meeting','d0-f1','MEETING')),
                (Station('d0-f1/lead','d0-f1/work','orchestrator'),),
                (Avatar('d0-visual-lead','d0-f1/lead','orchestrator'),))
            self.office_pin=OfficePin(self.scope,self.office.world,self.office.revision())
            self.links=(RoomLink('ops','d0-f1/work'),)
            self.pairs=(PairProposal('demo-agent-plan','lead','d0-visual-lead','d0-f1/lead'),)
            self.pins=ReviewPins(self.head,self.f.project,original.RESEARCH_REVISION,'plan','lead','orchestrator',self.history.count,self.history.head,self.office_pin.revision)

        def project_preview(self,**kwargs):
            args=dict(store=self.store,pins=self.pins,history_pin=self.history,office=self.office,office_pin=self.office_pin,
                plan=self.f.plan,run_pins=self.f.pins(),members=self.f.members,pool=self.f.pool,events=self.f.history,anchor=self.f.anchor,
                links=self.links,pairs=self.pairs,meeting_room='d0-f1/meeting')
            args.update(kwargs)
            with closing(sqlite3.connect(self.f.path)) as db:
                db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
                with original.SQLiteCursorShim(db) as cursor:
                    return review_project(cursor,**args)

        def test_existing_studio_transport_matches_internal_review(self):
            # Existing ORG-07A route only: a Studio read is not a project grant.
            self.setup_office()
            session=ReadSession(self.scope,'demo-reader',100,'org.preview.read')
            ctx=ServerReadContext(Path(self.path).resolve(),self.head,lambda _:session,lambda:99)
            app=FastAPI(); app.include_router(build_router(lambda:ctx,root/'candidates/ORG-05R3/studio.schema.json'))
            with TestClient(app) as client:
                response=client.get(ROUTE,headers={'Authorization':'Bearer opaque'})
                self.assertEqual(response.status_code,200,response.text)
                self.assertEqual(response.headers['Cache-Control'],'no-store')
                self.assertEqual(response.json()['revision'],self.head)
                self.assertFalse(response.json()['authoritative'])
                self.assertNotIn('principal',str(response.json()))
            out=self.project_preview()  # trusted fixture, not derived from the HTTP response or bearer
            self.assertTrue(out.get('structural_match'),out)
            self.assertEqual(out['org_revision'],response.json()['revision'])
            self.assertEqual(out['decision'],'HOLD'); self.assertFalse(out['dispatch_allowed'])
            self.assertIsNone(out['runtime_binding']); self.assertFalse(out['authoritative'])

        def test_project_office_preview(self):
            self.setup_office(); out=self.project_preview()
            self.assertTrue(out.get('structural_match'),out); self.assertEqual(out['office_pairs'],1); self.assertTrue(out['meeting_proposed'])
            self.assertEqual(out['decision'],'HOLD'); self.assertIsNone(out['runtime_binding']); self.assertFalse(out['atomic_cross_store'])
            for forbidden in ('demo-agent-plan','demo-principal','d0-visual-lead','d0-f1/lead'):
                self.assertNotIn(forbidden,str(out))

        def test_office_stale_pin(self):
            self.setup_office(); self.assertEqual(self.project_preview(office_pin=replace(self.office_pin,revision='f'*64)),hold_preview())

        def test_role_mismatch(self):
            self.setup_office(); self.assertEqual(self.project_preview(pins=replace(self.pins,role='qa')),hold_preview())

        def test_membership_mismatch(self):
            self.setup_office(); members=tuple(replace(m,principal_id='demo-forged') if m.task_id=='plan' else m for m in self.f.members)
            self.assertEqual(self.project_preview(members=members),hold_preview())

        def test_stale_head(self):
            self.setup_office(); self.store.record(replace(self.staffing,previous=self.staffing.revision()),self.head)
            self.assertEqual(self.project_preview(),hold_preview())

        def test_operation_history(self):
            self.setup_office(); task=TaskPin(self.scope,self.f.project,original.RESEARCH_REVISION,'research','research')
            self.history=self.store.append_proposal(self.head,task,task,'lead','worker','delegation',self.history)
            self.pins=replace(self.pins,history_count=self.history.count,history_head=self.history.head)
            out=self.project_preview(); self.assertEqual(out.get('history_count'),1,out); self.assertNotIn('proposals',out)
            with closing(sqlite3.connect(self.path)) as db,db:
                db.execute('DROP TRIGGER op_notice_update'); db.execute("UPDATE op_notice SET digest='bad'")
            self.assertEqual(self.project_preview(),hold_preview())

        def test_no_mutation(self):
            self.setup_office()
            def dump(path):
                with closing(sqlite3.connect(path)) as db: return tuple(db.iterdump())
            before=(dump(self.path),dump(self.f.path)); self.assertTrue(self.project_preview().get('structural_match'))
            self.assertEqual(before,(dump(self.path),dump(self.f.path)))

    names=('test_existing_studio_transport_matches_internal_review','test_project_office_preview','test_office_stale_pin',
           'test_role_mismatch','test_membership_mismatch','test_stale_head','test_operation_history','test_no_mutation')
    suite=unittest.TestSuite(PreviewChecks(n) for n in names)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun==len(names) and not result.skipped else 1

if __name__=='__main__': sys.exit(main())
