"use client";
import fixture from '../../fixtures/office.snapshot.json';
export default function SnapshotStrip(){
  return <div className="snapshot-strip" aria-label="Snapshot kaynak bilgileri"><span>Snapshot <strong>#{fixture.snapshot_seq}</strong></span><span>Tenant <strong>{fixture.tenant_id}</strong></span><span>World <strong>{fixture.world_id}</strong></span><span>Ortam <strong>{fixture.environment_id}</strong></span><span>Layout <strong>{fixture.layout_revision}</strong></span><span>As-of <time dateTime={fixture.as_of}>{fixture.as_of}</time></span><span>Policy / W-A <strong>{fixture.policy_epoch??'—'} / {fixture.wa_epoch??'—'}</strong></span><span>{fixture.data_status}</span></div>;
}
