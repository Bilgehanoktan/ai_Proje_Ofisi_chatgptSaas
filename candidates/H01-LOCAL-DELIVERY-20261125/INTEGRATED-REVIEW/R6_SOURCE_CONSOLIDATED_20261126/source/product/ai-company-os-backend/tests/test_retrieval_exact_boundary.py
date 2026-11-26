"""R10: exact lineage values, current tombstones and D0 deny boundaries."""
from dataclasses import replace
import unittest
from app.core.runtime_preview import Scope
from app.engines.memory_engine.retrieval import Node, TombstoneView, inspect_retrieval

class EqualScope(Scope):
    def __eq__(self, other): return True
    def __ne__(self, other): return False

class EqualView(TombstoneView):
    def __eq__(self, other): return True
    def __ne__(self, other): return False

class EqualText(str):
    def __eq__(self, other): return True
    def __ne__(self, other): return False
    __hash__ = str.__hash__

class DerivedNode(Node): pass
class DerivedTuple(tuple): pass

class LineageTests(unittest.TestCase):
    def setUp(self):
        self.scope = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY','sha256:'+'a'*64,'research','demo-run','demo-agent','demo-principal')
        self.nodes = (Node(self.scope,'source','v1','b'*64,()),Node(self.scope,'cache','v1','c'*64,('source',)),Node(self.scope,'other','v1','d'*64,()))
        self.view = TombstoneView(self.scope,3,5,(),True)
    def review(self, **changes):
        args = dict(scope=self.scope,nodes=self.nodes,target='cache',view=self.view,current=self.view)
        args.update(changes)
        r = inspect_retrieval(**args)
        self.assertFalse(r.retrieval_allowed)
        self.assertFalse(r.release_allowed)
        self.assertIsNone(r.deletion_receipt)
        return r
    def test_valid_graph(self):
        self.assertEqual(self.review().reason,'D0_LINEAGE_MATCH_ONLY')
    def test_tombstone_propagates(self):
        v=replace(self.view,keys=('source',))
        r=self.review(view=v,current=v)
        self.assertEqual((r.reason,r.stale_nodes),('STALE_HOLD',('cache','source')))
    def test_other_node_remains_structural_only(self):
        v=replace(self.view,keys=('source',))
        self.assertEqual(self.review(view=v,current=v,target='other').reason,'D0_LINEAGE_MATCH_ONLY')
    def test_plain_stale_view(self):
        self.assertEqual(self.review(current=replace(self.view,sequence=6)).reason,'TOMBSTONE_VIEW_UNKNOWN_HOLD')
    def test_view_subclass_cannot_hide_new_tombstone(self):
        v=EqualView(self.scope,3,6,('source',),True)
        self.assertEqual(self.review(current=v).reason,'TOMBSTONE_VIEW_UNKNOWN_HOLD')
    def test_scope_subclass_cannot_cross_tenant(self):
        s=EqualScope(**{**self.scope.__dict__,'tenant_id':'other-tenant'})
        self.assertEqual(self.review(nodes=(replace(self.nodes[0],scope=s),*self.nodes[1:])).reason,'LINEAGE_SCOPE_OR_PIN_HOLD')
    def test_scope_field_cannot_cross_principal(self):
        s=replace(self.scope,principal_id=EqualText('demo-other'))
        self.assertEqual(self.review(nodes=(replace(self.nodes[0],scope=s),*self.nodes[1:])).reason,'LINEAGE_SCOPE_OR_PIN_HOLD')
    def test_requested_scope_subclass(self):
        s=EqualScope(**self.scope.__dict__)
        self.assertEqual(self.review(scope=s).reason,'MEMORY_SCOPE_HOLD')
    def test_target_subclass(self):
        self.assertEqual(self.review(target=EqualText('cache')).reason,'MEMORY_SCOPE_HOLD')
    def test_node_subclass(self):
        self.assertEqual(self.review(nodes=(DerivedNode(**self.nodes[0].__dict__),*self.nodes[1:])).reason,'LINEAGE_SCOPE_OR_PIN_HOLD')
    def test_node_digest_subclass(self):
        self.assertEqual(self.review(nodes=(replace(self.nodes[0],digest=EqualText('b'*64)),*self.nodes[1:])).reason,'LINEAGE_SCOPE_OR_PIN_HOLD')
    def test_parent_subclass(self):
        self.assertEqual(self.review(nodes=(self.nodes[0],replace(self.nodes[1],parents=(EqualText('source'),)),self.nodes[2])).reason,'LINEAGE_SCOPE_OR_PIN_HOLD')
    def test_graph_tuple_subclass(self):
        self.assertEqual(self.review(nodes=DerivedTuple(self.nodes)).reason,'LINEAGE_GRAPH_HOLD')
    def test_tombstone_key_subclass(self):
        v=replace(self.view,keys=(EqualText('other'),))
        self.assertEqual(self.review(view=v,current=v).reason,'TOMBSTONE_VIEW_UNKNOWN_HOLD')
    def test_cycle_orphan_duplicate(self):
        for ns,reason in [(self.nodes[1:],'LINEAGE_ORPHAN_OR_DUPLICATE_HOLD'),((self.nodes[0],self.nodes[0],self.nodes[1]),'LINEAGE_ORPHAN_OR_DUPLICATE_HOLD'),((replace(self.nodes[0],parents=('cache',)),*self.nodes[1:]),'LINEAGE_CYCLE_HOLD')]:
            self.assertEqual(self.review(nodes=ns).reason,reason)
    def test_epoch_bool_rejected(self):
        self.assertEqual(self.review(current=replace(self.view,epoch=True)).reason,'TOMBSTONE_VIEW_UNKNOWN_HOLD')

if __name__ == '__main__': unittest.main()
