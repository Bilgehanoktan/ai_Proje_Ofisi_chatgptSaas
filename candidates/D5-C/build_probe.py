"""Generate a test-only function from the exact original wrapper source.
Never write to product/ and never install the generated function in app/api.
"""
import ast
from hashlib import sha1

AUTHORITY_BLOB = 'fa47acd32adb309896f762ec50e47bf26641adbb'
WRAPPER = 'execute_authority_fenced_transition'


def probe_source(raw):
    if type(raw) is not bytes or sha1(f'blob {len(raw)}\0'.encode('ascii')+raw).hexdigest() != AUTHORITY_BLOB:
        raise ValueError('D5C_SOURCE_PIN_HOLD')
    source = raw.decode('utf-8')
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == WRAPPER]
    if len(nodes) != 1:
        raise ValueError('D5C_WRAPPER_SHAPE_HOLD')
    old = ast.get_source_segment(source, nodes[0])
    signature = 'result=None, result_reader=None):'
    fence = '    with authority.claim_and_fence(root, pin.scope_sha, pin.binding, pin.transaction_ref, pin.request_digest):\n'
    tail = '''        return execute_fenced_transition(intent, context, registry, witness, expected_binding,
            memory_path, reader, public_key, raw, journal, connect, clock, lambda: witness,
            company=company, expected_company_binding=expected_company_binding,
            result=result, result_reader=result_reader)'''
    if any(old.count(x) != 1 for x in (signature, fence, tail)) or not old.endswith(tail):
        raise ValueError('D5C_WRAPPER_SHAPE_HOLD')
    new = old.replace('def '+WRAPPER+'(', 'def probe_authority_fenced_transition(', 1)
    new = new.replace(signature, 'result=None, result_reader=None, initial_identity, identity_sha, read_latest):', 1)
    new = new.replace(fence, '    from fence_probe import check_before_claim, stop_inside_fence\n'
                      '    check_before_claim(intent, root, initial_identity, identity_sha, read_latest)\n'+fence, 1)
    new = new.replace(tail, '        stop_inside_fence(intent, root, initial_identity, identity_sha, read_latest)', 1)
    compile(new, '<D5-C diagnostic only>', 'exec')
    return new+'\n'
