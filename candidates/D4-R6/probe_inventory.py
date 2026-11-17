"""R6 exact R2 probe inventory; no SQL execution or acceptance authority."""
TABLES = ('events','outbox','fences','run_heads','run_leases','run_mutations','run_audit',
          'sample_budgets','run_admissions','sample_reservations','run_lease_renewals',
          'sample_settlements','terminal_command_anchors','company_run_membership',
          'company_stream_heads','company_event_order')
SCOPES = {
    'a':['synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY'],
    'b':['synthetic-tenant-b','synthetic-company','A0_SAMPLE_ONLY'],
    'c':['synthetic-tenant','synthetic-company-c','A0_SAMPLE_ONLY'],
    'd':['synthetic-tenant','synthetic-company','D4_ENV_ONLY'],
}
SCOPE_SUFFIXES = ('guc_ignored','cross_scope_insert','provision_denied',
                  'anchor_append_only','order_append_only','scope_column_immutable',
                  'scoped_fk','anchor_deferred_fk','role_switch_denied',
                  'cross_update_hidden','cross_delete_hidden')
A_EXTRA = ('a.fk_foreign_membership_only','a.positive_sequence_cas',
           'a.positive_anchor','a.positive_order','a.positive_rollback')
LOCK_IDS = ('distinct_sessions','stream_first_lock','stream_nowait_denied',
            'stale_cas_no_write','stream_rollback_unchanged')
EXPECTED_COUNT = 454


def expected_ids(scopes, tables):
    if (type(scopes) is not dict or list(scopes)!=list(SCOPES) or scopes!=SCOPES
            or type(tables) not in (tuple,list) or tuple(tables)!=TABLES):
        raise ValueError('D4_INVENTORY_PROFILE_HOLD')
    ids=[]
    for k,scope in scopes.items():
        for t in tables:
            p=f'{k}.{t}.'
            ids.extend((p+'visible',p+'force'))
            ids.extend(p+f'foreign.{v}' for v in scopes.values() if v!=scope)
            ids.append(p+'no_truncate')
        ids.extend(f'{k}.{suffix}' for suffix in SCOPE_SUFFIXES)
        if k=='a': ids.extend(A_EXTRA)
    ids.extend(f'unmapped.{t}' for t in tables)
    ids.extend(LOCK_IDS)
    if len(ids)!=EXPECTED_COUNT or len(set(ids))!=EXPECTED_COUNT:
        raise ValueError('D4_EXPECTED_INVENTORY_HOLD')
    return tuple(ids)


def verify_check_set(checks, scopes, tables):
    expected=expected_ids(scopes,tables)
    if type(checks) is not list or tuple(checks)!=expected:
        raise ValueError('D4_CHECK_SET_HOLD')
    return len(expected)
