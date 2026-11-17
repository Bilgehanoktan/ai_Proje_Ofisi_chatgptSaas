"""D0 exact fixture/schema diagnostics; not API, runtime or product acceptance."""
import argparse
import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path
import unittest

import jsonschema

CASES = {
    'company.catalog.demo': ('company.catalog', '11b688e725933075ced435aba0d283c8a2b2df78896f7c5129a2cc673e9523a3', 'f27745df5af32a68d1bf3aed6ec4c014d5047fa6ac70bb3e498ce86a2f0c5059', [('authority', 'code_effective', True), ('authority', 'real_test', 'PASS')]),
    'core.preview.demo': ('core.preview', '7bda9468606128af2acbd0616556c47ce91b69806af1e739122919ec3ba6d74c', '3f06282142ca685f21cce6a83ebb6341fe3b8c470027b912662c6d879f15256b', [('authority', 'decision', 'ALLOW'), ('authority', 'release_ready', True)]),
    'office.snapshot.demo': ('office.snapshot', 'f7191fa16fdfad020dcdf7cec0506f874b398c6afba6d25a734a0440c6e5ce9d', '313b8072ec1e4bdc1feb945540c31e0a762be4151f616bd6a25e4772a790baa5', [('authority', 'production', 'AUTHORIZED'), ('authority', 'security_acceptance', 'PASS')]),
    'core.plan.projection': ('core.plan.projection', '4e1b26ae8a122807351d7d6cbe6ba0e051de9171a93a0248070b22869c828421', 'e564bed4f4edfb5dd94488b08cbba3205b6f018491fadd8d200d884a85e1f4bb', [(None, 'dispatch_allowed', True), (None, 'release_ready', True)]),
}


def read_pinned(root, relative, expected):
    p = root / relative
    if p.is_symlink() or not p.is_file() or p.resolve() != p.absolute():
        raise ValueError('SOURCE_PATH_HOLD: ' + relative)
    data = p.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('SOURCE_PIN_HOLD: ' + relative)
    return data


def load_pairs(root):
    if importlib.metadata.version('jsonschema') != '4.26.0':
        raise ValueError('JSONSCHEMA_PIN_HOLD')
    pairs = {}
    for schema_name, (fixture_name, sh, fh, changes) in CASES.items():
        a = read_pinned(root, f'product/ai-company-os-backend/contracts/source/{schema_name}.schema.json', sh)
        b = read_pinned(root, f'product/ai-company-os-frontend/contracts/generated/{schema_name}.schema.json', sh)
        x = read_pinned(root, f'product/ai-company-os-backend/fixtures/{fixture_name}.json', fh)
        y = read_pinned(root, f'product/ai-company-os-frontend/fixtures/{fixture_name}.json', fh)
        if a != b or x != y:
            raise ValueError('SHARED_PAIR_HOLD: ' + schema_name)
        schema, fixture = json.loads(a), json.loads(x)
        cls = jsonschema.validators.validator_for(schema)
        cls.check_schema(schema)
        pairs[schema_name] = (cls(schema), fixture, changes)
    return pairs


def suite_for(pairs):
    suite = unittest.TestSuite()
    for name, (validator, fixture, changes) in pairs.items():
        def valid(v=validator, f=fixture):
            v.validate(f)
        suite.addTest(unittest.FunctionTestCase(valid, description=name + ' original fixture valid'))
        for parent, key, value in changes:
            def rejected(v=validator, f=fixture, p=parent, k=key, val=value):
                bad = copy.deepcopy(f)
                target = bad if p is None else bad[p]
                target[k] = val
                with unittest.TestCase().assertRaises(jsonschema.ValidationError):
                    v.validate(bad)
            suite.addTest(unittest.FunctionTestCase(rejected, description=name + ' rejects ' + key))
    return suite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    pairs = load_pairs(args.repo.resolve())
    print('16 exact source pins; eight shared schema/fixture pairs; jsonschema 4.26.0', flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite_for(pairs))
    return 0 if result.wasSuccessful() and result.testsRun == 12 else 1


if __name__ == '__main__':
    raise SystemExit(main())
