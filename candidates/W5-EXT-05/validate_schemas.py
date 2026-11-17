"""Optional local verification using preinstalled jsonschema, not a product dependency."""
import json
from dataclasses import asdict
from importlib.metadata import version
from jsonschema import Draft202012Validator
from test_catalog_review import setup, LOCK
from catalog_review import review_candidate


def main():
    cases=[]
    for e in LOCK['entries']:
        sid=e['skill_id'];b=setup(sid)[0];m=json.loads(b.manifest)
        inp,out=map(json.loads,(b.input_schema,b.output_schema))
        for name,schema in [('input',inp),('output',out)]:
            Draft202012Validator.check_schema(schema);cases.append(f'{sid}: {name} schema valid')
        iv,ov=Draft202012Validator(inp),Draft202012Validator(out)
        for role in m['role_hints']:
            a=setup(sid,role);iv.validate(a[2]);cases.append(f'{sid}: {role} request valid')
            data=json.loads(json.dumps(asdict(review_candidate(*a))));ov.validate(data);cases.append(f'{sid}: {role} output valid')
        a=setup(sid,m['role_hints'][0]);request={**a[2],'enable':True};assert not iv.is_valid(request);cases.append(f'{sid}: extra enable request rejected')
        data=json.loads(json.dumps(asdict(review_candidate(*a))));data['enabled']=True;assert not ov.is_valid(data);cases.append(f'{sid}: enabled output rejected')
        data['enabled']=False;data['effective_tools']=['network-upload'];assert not ov.is_valid(data);cases.append(f'{sid}: effective tool injection rejected')
    print(json.dumps({'validator':'jsonschema '+version('jsonschema'),'draft':'2020-12','passed':len(cases),'cases':cases},indent=2))

if __name__=='__main__':main()
