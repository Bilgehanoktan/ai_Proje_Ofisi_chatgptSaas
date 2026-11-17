"""ORG-08 candidate: reuse R3 and ORG-06; not installed as a product HTTP route."""
from dataclasses import asdict
from pathlib import Path
import importlib.metadata
import json
from preview_boundary import (COMMON_SCOPE, ReviewPins, blob, require,
                              join_historical, hold_preview)

ROOT = Path(__file__).resolve().parents[2]
R3 = ROOT/'candidates'/'ORG-05R3'
ORG06 = ROOT/'candidates'/'ORG-06'
PINS = Path(__file__).with_name('SOURCE_PINS.json')


def verify_checkout():
    pins=json.loads(PINS.read_text(encoding='utf-8'))['local_git_blobs']
    for relative, expected in pins.items():
        p=ROOT/relative
        require(p.is_file() and not p.is_symlink() and p.resolve()==p,'SOURCE_MISSING')
        require(blob(p.read_bytes())==expected,'SOURCE_PIN_HOLD')
    require(importlib.metadata.version('jsonschema')=='4.26.0','VALIDATOR_PIN_HOLD')
    return len(pins)


def owners():
    """Caller configures original import paths; verify selected bytes before import.
    Trusted checkout and full dependency closure still required; this is not sandboxing.
    """
    verify_checkout()
    import durable_ops, persistence, office_bridge, org_core_bridge
    for module, directory in ((durable_ops,R3),(persistence,R3),(office_bridge,R3),(org_core_bridge,ORG06)):
        require(Path(module.__file__).resolve()==directory/(module.__name__+'.py'),'OWNER_IMPORT_HOLD')
    return durable_ops, persistence, office_bridge, org_core_bridge


def review_project(cursor, *, store, pins, history_pin, office, office_pin,
                   plan, run_pins, members, pool, events, anchor,
                   links=(), pairs=(), meeting_room=None, evidence=None):
    """Internal synthetic fixture review, NOT a public API or project permission check.
    The server owner supplies the existing consistent Core cursor, trusted retained
    pins, exact R3 store, and Office metadata. No project access inferred from
    org.preview.read. All three reads are historical; no cross-store atomicity.
    """
    try:
        ops, storage, office_owner, bridge=owners()
        require(type(pins) is ReviewPins,'PIN_SHAPE'); pins.check()
        require(type(store) is ops.OperationsStore and store._key==COMMON_SCOPE,'ORG_SCOPE_HOLD')
        require(type(history_pin) is ops.HistoryPin and (history_pin.count,history_pin.head)==(pins.history_count,pins.history_head),'HISTORY_PIN_HOLD')
        ops.check_pin(history_pin)
        require(type(office_pin) is ops.OfficePin and type(office_pin.scope) is storage.Scope and office_pin.scope.key()==COMMON_SCOPE and office_pin.revision==pins.office_revision,'OFFICE_PIN_HOLD')
        require(type(office) is office_owner.OfficeView and office.world==office_pin.world and office.revision()==pins.office_revision,'OFFICE_REFERENCE_HOLD')
        binding=bridge.review_research_binding(cursor,plan=plan,expected_revision=pins.plan_revision,project_id=pins.project_id,
            pins=run_pins,members=members,pool=pool,events=events,anchor=anchor,store=store,org_head=pins.org_revision,
            history_pin=history_pin,task_id=pins.task_id,seat_id=pins.seat_id,evidence=evidence)
        require(type(binding) is bridge.BindingReview and binding.structural_match is True,'RUNTIME_READ_HOLD')
        studio=store.studio_view(pins.org_revision)
        combined=store.combined(pins.org_revision,pins.project_id,history_pin,office,office_pin,links,pairs,meeting_room)
        return join_historical(R3,pins,studio,combined,asdict(binding))
    except Exception:
        return hold_preview()
