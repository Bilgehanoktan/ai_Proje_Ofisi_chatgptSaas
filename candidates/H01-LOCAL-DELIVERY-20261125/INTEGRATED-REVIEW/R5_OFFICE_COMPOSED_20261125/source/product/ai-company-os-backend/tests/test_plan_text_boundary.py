"""NW07: existing pure DAG/plan validation, no dispatch or external effects."""
from copy import deepcopy
from unittest import TestCase

from app.core.orchestrator.engine import canonical_plan, parse_plan, preview_plan
from app.core.task_engine.dag import GraphError, Task, topological_waves
from test_pinned_schedule_0220 import PLAN


class PlanTextBoundaryTests(TestCase):
    def test_invalid_unicode_label_is_graph_error(self):
        for label in ('\ud800', '\udfff', 'valid\ud800text', '\ud83d\ude00'):
            for compiler in (parse_plan, canonical_plan, preview_plan):
                with self.subTest(label=repr(label), compiler=compiler.__name__):
                    plan = deepcopy(PLAN)
                    plan['tasks'][0]['label'] = label
                    with self.assertRaisesRegex(GraphError, '^TASK_FIELD_INVALID$'):
                        compiler(plan)

    def test_direct_graph_validation_rejects_surrogate(self):
        task = Task('x', '\ud800', 'research', ())
        with self.assertRaisesRegex(GraphError, '^TASK_FIELD_INVALID$'):
            topological_waves((task,))

    def test_valid_unicode_projection_identity(self):
        plan = deepcopy(PLAN)
        plan['tasks'][0]['label'] = 'Araştırma — çığ 🌍'
        projection = canonical_plan(plan)
        self.assertEqual(projection['digest'], '5bfff1a4be1a15b3f4f5488749698522d0fd5170ee9e662cd375c32c08bd447c')
        self.assertEqual(projection['tasks'][0]['label'], plan['tasks'][0]['label'])
        self.assertEqual(projection['admission'], 'DENY')
        self.assertFalse(projection['dispatch_allowed'] or projection['release_ready'])

    def test_original_projection_identity(self):
        self.assertEqual(canonical_plan(PLAN)['digest'], '206e971dc5b4c31a16888654381382eaa4bc49baffb7def57f6bcec835b0c876')

    def test_exact_task_limit_preserved(self):
        tasks = (Task('t'+str(i), 'Task', 'research', ()) for i in range(100))
        self.assertEqual(topological_waves(tasks), (tuple(sorted('t'+str(i) for i in range(100))),))

    def test_oversize_iterator_stops_at_limit(self):
        seen = []
        def tasks():
            for i in range(101):
                seen.append(i)
                yield Task('t'+str(i), 'Task', 'research', ())
            self.fail('Oversize iterator was consumed beyond rejection boundary')
        with self.assertRaisesRegex(GraphError, '^TASK_COUNT_INVALID$'):
            topological_waves(tasks())
        self.assertEqual(len(seen), 101)
