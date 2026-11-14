"""Immutable in-memory DEMO ledger, no persistence, I/O or event authority."""
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class Event:
    event_id: str
    seq: int
    kind: str
    floor_id: str
    station_id: str | None
    tenant_id: str
    world_id: str
    environment_id: str
    stream_id: str
    layout_revision: str

@dataclass(frozen=True)
class Ledger:
    events: tuple[Event, ...] = ()
    freshness: Literal["SAMPLE", "RESYNC_REQUIRED"] = "SAMPLE"

@dataclass(frozen=True)
class AppendResult:
    ledger: Ledger
    status: str

def append_preview(ledger: Ledger, event: Event, floors: dict[str, frozenset[str]]) -> AppendResult:
    def reject(reason: str) -> AppendResult:
        return AppendResult(Ledger(ledger.events, "RESYNC_REQUIRED"), reason)
    if ledger.freshness != "SAMPLE":
        return AppendResult(ledger, "SNAPSHOT_REQUIRED")
    if (event.tenant_id,event.world_id,event.environment_id,event.stream_id,event.layout_revision) != (
        "synthetic-tenant","demo-world","A0_SAMPLE_ONLY","demo-ui-stream","layout-d3-demo"):
        return reject("SCOPE_OR_LAYOUT_MISMATCH")
    if type(event.seq) is not int or event.seq < 1 or not event.event_id:
        return reject("ENVELOPE_INVALID")
    if event.floor_id not in floors or event.kind not in {"DEMO_FLOOR_SELECTED","DEMO_STATION_SELECTED"}:
        return reject("PAYLOAD_INVALID")
    if event.kind == "DEMO_FLOOR_SELECTED" and event.station_id is not None:
        return reject("PAYLOAD_INVALID")
    if event.kind == "DEMO_STATION_SELECTED" and event.station_id not in floors[event.floor_id]:
        return reject("PAYLOAD_INVALID")
    for prior in ledger.events:
        if prior.event_id == event.event_id:
            return AppendResult(ledger, "DUPLICATE_IGNORED") if prior == event else reject("EVENT_ID_CONFLICT")
        if prior.seq == event.seq:
            return reject("SEQUENCE_CONFLICT")
    if event.seq != len(ledger.events)+1:
        return reject("SEQUENCE_GAP_OR_OLD")
    return AppendResult(Ledger(ledger.events+(event,)), "SAMPLE_APPENDED")

def replay_preview(events: list[dict], layout: dict) -> dict:
    floors = {f["id"]:frozenset(s["id"] for s in f["stations"]) for f in layout["floors"]}
    ledger = Ledger()
    results = []
    for raw in events:
        try:
            result = append_preview(ledger, Event(**raw), floors)
        except (TypeError, ValueError):
            result = AppendResult(Ledger(ledger.events,"RESYNC_REQUIRED"), "ENVELOPE_INVALID")
        ledger = result.ledger
        results.append(result.status)
    last = ledger.events[-1] if ledger.events else None
    # A stale sample must not present an authoritative current selection.
    return {"mode":"D0_REPLAY_PREVIEW","freshness":ledger.freshness,"last_seq":len(ledger.events),
            "selected_floor":last.floor_id if last and ledger.freshness=="SAMPLE" else None,
            "selected_station":last.station_id if last and ledger.freshness=="SAMPLE" else None,
            "results":results,"persistent":False,"verified":False}
