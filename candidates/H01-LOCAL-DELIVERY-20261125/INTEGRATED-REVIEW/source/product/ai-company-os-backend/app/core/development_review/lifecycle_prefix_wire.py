"""D0-only fixed-prefix wire profile; no I/O, authority or live clock."""
PLAN_REVISION = 'sha256:c75ec1070786538f38bdccdcf6a75de62a9e02e9bcb7e4a4bb9df5f7e96638a0'
STEPS = (('D0_RUN_ADMISSION','ADMITTED'),('D0_RUN_TRANSITION','RUNNING'),
         ('D0_LEASE_RENEWAL','RUNNING'),('D0_RUN_TRANSITION','VERIFYING'))


def prefix_wire(version):
    """Only call after exact persisted prefix checks. Never infer live freshness."""
    if type(version) is not int or not 1 <= version <= len(STEPS):
        raise ValueError('D0_PREFIX_VERSION_HOLD')
    renewed = version >= 3
    return {
        'schema_version':'lifecycle.prefix.v1-D0', 'mode':'D0_0196L_HISTORICAL_PREFIX',
        'tenant':'synthetic-tenant','company':'synthetic-company','environment':'A0_SAMPLE_ONLY',
        'plan_revision':PLAN_REVISION,'task_id':'a','run_id':'demo-a',
        'agent_instance_id':'demo-agent','principal_id':'demo-principal','attempt':0,
        'head_version':version,'state':STEPS[version-1][1],
        'timeline':[{'version':i,'kind':kind,'state':state} for i,(kind,state) in enumerate(STEPS[:version],1)],
        'lease_present':True,'lease_version':2 if renewed else 1,'heartbeat_revision':1 if renewed else 0,
        'fence':1,'heartbeat_tick':11 if renewed else 10,'expires_tick':31 if renewed else 20,
        'policy_epoch':2,'witness_epoch':3,'sample_budget_revision':2 if renewed else 1,
        'sample_outstanding_minor':20,'sample_recognized_minor':0,'currency':'USD',
        'freshness':'HISTORICAL_SAMPLE','lease_freshness':'UNKNOWN','causality':'EXACT_FIXED_PREFIX_ONLY',
        'geometry_join':'HOLD','model_binding':'HOLD','memory_acl':'HOLD','independent_acceptance':'HOLD',
        'decision':'HOLD','dispatch_allowed':False,'provider_called':False,'spend_allowed':False,
        'release_ready':False,'authoritative':False,'real_run_count':None,
    }
