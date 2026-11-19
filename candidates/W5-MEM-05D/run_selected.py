import sys, unittest, pathlib, sqlite3, cryptography
root = pathlib.Path(__file__).resolve().parent / 'stage'
sys.path[:0] = [str(root), str(root/'tests')]
print('PYTHON='+sys.version, flush=True)
print('SQLITE='+sqlite3.sqlite_version, flush=True)
print('CRYPTOGRAPHY='+cryptography.__version__, flush=True)
modules = ['test_memory_recovery_w5_mem05d','test_memory_history_w5_mem03','test_memory_checkpoint_w5_mem04','test_memory_gateway_05c_r2','test_memory_gateway_05c_r1','test_router_cost_review','test_memory_access_0194','test_memory_store_0196','test_runtime_memory_model_0207','test_joint_context_0208','test_memory_witness_0209']
suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
result=unittest.TextTestRunner(verbosity=2).run(suite)
print('TESTS_RUN='+str(result.testsRun),flush=True)
print('FAILURES='+str(len(result.failures)),flush=True)
print('ERRORS='+str(len(result.errors)),flush=True)
print('SKIPPED='+str(len(result.skipped)),flush=True)
print('EXIT_CODE='+str(int(not result.wasSuccessful())),flush=True)
sys.exit(not result.wasSuccessful())
