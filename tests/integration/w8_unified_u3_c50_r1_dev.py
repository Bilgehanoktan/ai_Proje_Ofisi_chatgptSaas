"""MI-01/W8: review-only C50 compatibility binding on the exact U3 runner.

This is NOT original C07/C08 acceptance.  It does not alter historical 0207
sources, runner, lock, or prior Windows stages.  It intentionally discards
formal W8 acceptance markers after a complete development test invocation.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ORIGINAL_U3_BLOB = '1609d857b46ea973180c45271d87fcc92083f0a6'
ORIGINAL_P24 = 'tests/integration/run_core_0207.py'
VERSIONED_RUNNER = 'tests/integration/core0207_crypto50_r1/run_core0207_c50_r1.py'
VERSIONED_CONTRACT = 'tests/integration/core0207_crypto50_r1/CONTRACT.json'
SOURCE_BLOBS = {
    VERSIONED_RUNNER: 'cc467843bf11857fbbd9df19e513626fb7de85bf',
    VERSIONED_CONTRACT: '537e0c35592ca7366a52ab87c08db7e419f18b71',
}
ORIGINAL_MANIFEST = '9660da1104617b4764d5f1e32009e4e3405b47f8'
APPROVED_REVIEW_SHA256 = '341e179afda3e344ac32b3f4643860e44c7dd350cfb66ac59ac5edc98c79a1b3'
DEV_REPORT_NAME = 'CORE0207_C50_R1_DEV_ONLY.json'
DEV_SUMMARY_NAME = 'W8_C50_R1_DEV_ONLY_NO_C07_ACCEPTANCE.json'
MARKERS = ('BUILD_TEST_OK', 'SMOKE_OK', 'HYBRID_NATIVE_OK')


def git_blob(path):
    data = Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()


def demand(condition, reason):
    if not condition:
        raise ValueError(reason)


def load_original(root):
    path = root / 'w8_unified_u3.py'
    demand(path.is_file() and not path.is_symlink() and git_blob(path) == ORIGINAL_U3_BLOB,
           'C50_R1_ORIGINAL_U3_BLOB_HOLD')
    spec = importlib.util.spec_from_file_location('mi01_u3_c50_original', path)
    demand(spec is not None and spec.loader is not None, 'C50_R1_IMPORT_HOLD')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.load_candidate()


def extend(w):
    demand(w.MANIFEST_BLOB == ORIGINAL_MANIFEST, 'C50_R1_SOURCE_MANIFEST_HOLD')
    original_aux, original_test = w.verify_aux, w.test

    def verify_aux(root):
        pins = original_aux(root)
        demand(not (set(pins) & set(SOURCE_BLOBS)), 'C50_R1_AUX_COLLISION_HOLD')
        for rel, expected in SOURCE_BLOBS.items():
            p = w.checked_path(root, rel)
            demand(p.is_file() and not p.is_symlink() and git_blob(p) == expected,
                   'C50_R1_SOURCE_PIN_HOLD: '+rel)
        return {**pins, **SOURCE_BLOBS}

    def test(stage, approval):
        stage = Path(stage)
        demand(approval == APPROVED_REVIEW_SHA256, 'C50_R1_C06_REVIEW_APPROVAL_HOLD')
        w.installed(stage, approval)
        verify_aux(stage)
        # A new stage is mandatory; do not overwrite failed or completed evidence.
        witness = stage.parent / DEV_REPORT_NAME
        summary = stage.parent / DEV_SUMMARY_NAME
        demand(not witness.exists() and not witness.is_symlink(), 'C50_R1_DEV_REPORT_EXISTS_HOLD')
        demand(not summary.exists() and not summary.is_symlink(), 'C50_R1_DEV_SUMMARY_EXISTS_HOLD')
        for marker in MARKERS:
            demand(not (stage / marker).exists(), 'C50_R1_NONFRESH_STAGE_MARKER_HOLD')
        invoked = 0
        old_run = w.run
        expected_original = stage / ORIGINAL_P24
        original_report = stage / 'core29-p10f.json'

        def bridge(args, cwd, env=None):
            nonlocal invoked
            argv = list(map(str, args))
            if len(argv) >= 2 and Path(argv[1]).name == 'run_core_0207.py':
                demand(len(argv) == 6 and argv[0] == str(w.python(stage)) and
                       argv[1] == str(expected_original) and
                       argv[2] == '--source' and argv[4] == '--report' and
                       argv[5] == str(original_report) and Path(cwd) == stage,
                       'C50_R1_LEGACY_RUNNER_INVOCATION_HOLD')
                historical = Path(argv[3])
                demand(historical.is_dir() and not historical.is_symlink() and
                       not historical.resolve().is_relative_to(stage.resolve()),
                       'C50_R1_HISTORICAL_SOURCE_HOLD')
                demand(invoked == 0 and not original_report.exists(),
                       'C50_R1_DUPLICATE_OR_LEGACY_REPORT_HOLD')
                invoked += 1
                verify_aux(stage)
                cmd = [w.python(stage), '-B', stage / VERSIONED_RUNNER,
                       '--stage', stage,
                       '--runner-root', stage/'tests/integration',
                       '--source', historical, '--report', witness]
                old_run(cmd, stage, env)
                demand(witness.is_file() and not witness.is_symlink(),
                       'C50_R1_REPORT_MISSING_HOLD')
                payload = json.loads(witness.read_text(encoding='utf-8'))
                demand(payload.get('status') == 'PASS' and payload.get('passed') == 29 and
                       payload.get('source_files_verified') == 55 and
                       payload.get('contract_pin') == SOURCE_BLOBS[VERSIONED_CONTRACT] and
                       payload.get('stage_review_sha256') == approval and
                       payload.get('immutable_stage_guards_preserved') is True and
                       payload.get('W8_C07') == 'HOLD' and
                       payload.get('suite_classification') == 'VERSIONED_LOCAL_D0_CANDIDATE_NOT_W8_C07' and
                       payload.get('dependency_versions', {}).get('cryptography') == '50.0.2',
                       'C50_R1_REPORT_CONTENT_HOLD')
                # Historical 46.0.4 result is deliberately NOT forged.
                demand(not original_report.exists(), 'C50_R1_LEGACY_REPORT_NOT_ALLOWED')
                return None
            return old_run(args, cwd, env)

        w.run = bridge
        try:
            result = original_test(stage, approval)
            demand(invoked == 1, 'C50_R1_MANDATORY_TEST_NOT_EXECUTED_HOLD')
            demand((stage/'BUILD_TEST_OK').read_text(encoding='utf-8') == approval,
                   'C50_R1_INHERITED_FULL_W8_NOT_COMPLETE_HOLD')
            w.reviewed(stage, approval)
            # Never publish historical W8 C07/C08 success markers from this review suite.
            for marker in MARKERS:
                (stage/marker).unlink(missing_ok=True)
            digest = hashlib.sha256(witness.read_bytes()).hexdigest()
            summary.write_text(json.dumps({
                'classification':'W8_DEVELOPMENT_COMPATIBILITY_ONLY_NOT_C07_ACCEPTANCE',
                'test_chain':'COMPLETE_INHERITED_W8_TEST_WITH_CORE0207_C50_R1',
                'versioned_core29':'PASS_29_OF_29', 'core_report_sha256':digest,
                'historical_core0207_46_0_4':'HOLD_UNCHANGED',
                'W8_C07':'HOLD_PENDING_OWNER_SECURITY_REVIEW',
                'W8_C08':'NOT_RUN','independent_C05':'HOLD',
                'original_acceptance_markers_written':False,
                'review_sha256':approval}, indent=2)+'\n', encoding='utf-8')
            return result
        except Exception:
            for marker in MARKERS:
                (stage/marker).unlink(missing_ok=True)
            raise
        finally:
            w.run = old_run

    def smoke(*_args, **_kw):
        raise ValueError('C50_R1_C08_FORBIDDEN_WITHOUT_OWNER_APPROVED_C07')

    w.verify_aux, w.test, w.smoke = verify_aux, test, smoke
    return w


def load_candidate():
    return extend(load_original(Path(__file__).resolve().parent))


if __name__ == '__main__':
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
