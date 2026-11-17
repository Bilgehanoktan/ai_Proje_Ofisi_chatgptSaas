"""Developer-only deterministic catalog builder; not a runtime loader."""
import json
from hashlib import sha1, sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = '384093218b88465bb9b804d43af10e576755b2bc'
SPECS = (
    ('superpowers', 'review_packet.mjs', 'W5-EXT-02', 'ba450067f54f09d3d5dd670aa96da8aa7becd435', '22f0b463e7a5e579904dd6211a520321035526f7', ['engineer', 'qa'], 'engineering-guidance-review'),
    ('ui-ux-pro-max', 'contrast_review.mjs', 'W5-EXT-03', '94c0f0965d17b488c306c233de4dffb29b9fc773', 'e59ff376a41f7ca47b7541ad5c116495cbade3ee', ['engineer', 'research'], 'eds-contrast-review'),
    ('watch', 'local_video.py', 'W5-EXT-04', '85855a5c4278c061ec0d0a63916ad7668a998e30', '03ceb42f7fa2c4439aca01752118044baabffb8f', ['research'], 'synthetic-video-review'),
)
VERSION = '0.1.0-ext05'

def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('ascii')

def sha(raw):
    return sha256(raw).hexdigest()

def git_blob(raw):
    return sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical(obj)
    path.write_bytes(raw)
    return sha(raw)

def build():
    entries = []
    for sid, name, rev, blob, upstream, roles, capability in SPECS:
        artifact = (ROOT / 'artifacts' / name).read_bytes()
        if git_blob(artifact) != blob:
            raise ValueError('ARTIFACT_GIT_PIN')
        directory = ROOT / 'catalog' / sid
        inp = {'$schema':'https://json-schema.org/draft/2020-12/schema', 'title':sid+' catalog review request (not execution)', 'type':'object', 'additionalProperties':False, 'required':['skill_id','version','role'], 'properties':{'skill_id':{'const':sid},'version':{'const':VERSION},'role':{'enum':roles}}}
        props = {'reason':{'type':'string'}, 'structural_match':{'type':'boolean'}, 'diagnostic_overlap':{'type':'array','items':{'const':capability},'uniqueItems':True,'maxItems':1}, 'status':{'const':'QUARANTINED'}, 'decision':{'const':'HOLD'}, 'enabled':{'const':False}, 'effective_tools':{'const':[]}, 'grant_created':{'const':False}, 'dispatch_allowed':{'const':False}, 'independent_verified':{'const':False}}
        out = {'$schema':'https://json-schema.org/draft/2020-12/schema','title':sid+' catalog review result (not execution)','type':'object','additionalProperties':False,'required':sorted(props),'properties':props}
        ins, outs = write(directory/'input.schema.json', inp), write(directory/'output.schema.json', out)
        manifest = {'profile':'EXT05_CATALOG_REVIEW_ONLY','skill_id':sid,'version':VERSION,'source':{'path':'candidates/'+rev+'/'+name,'commit':PARENT,'git_blob':blob,'sha256':sha(artifact),'bytes':len(artifact),'upstream_commit':upstream},'input_schema_sha256':ins,'output_schema_sha256':outs,'role_hints':roles,'tool_ids':[capability],'tool_ids_semantics':'DIAGNOSTIC_ONLY_NOT_REGISTERED','enabled':False,'g7_ref':None,'g8_ref':None,'license_ref':'upstream-root-mit-review-only','custody_ref':'ext05-local-byte-review-only'}
        md = write(directory/'manifest.json', manifest)
        entries.append({'skill_id':sid,'version':VERSION,'manifest_sha256':md,'input_schema_sha256':ins,'output_schema_sha256':outs,'artifact_sha256':sha(artifact),'artifact_git_blob':blob,'artifact_file':name,'source_path':manifest['source']['path'],'source_commit':PARENT})
    write(ROOT/'CATALOG_LOCK.json', {'profile':'EXT05_LOCAL_REFERENCE_NOT_INDEPENDENT','parent':PARENT,'entries':entries})

if __name__ == '__main__':
    build()
