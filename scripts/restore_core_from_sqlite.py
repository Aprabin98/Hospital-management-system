import sqlite3
from typing import Dict, List, Tuple

import psycopg2
from psycopg2.extras import execute_values


SQLITE_DB = 'db.sqlite3'
PG_CONN = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'hms_db',
    'user': 'hms_user',
    'password': 'StrongPassword123!',
}

TABLE_ORDER = [
    'users_user',
    'users_patientprofile',
    'clinical_specialization',
    'clinical_doctor',
    'clinical_shift',
    'clinical_doctorschedule',
    'clinical_doctorleave',
    'appointments_appointment',
    'prescriptions_prescription',
    'prescriptions_prescriptionitem',
    'payments_payment',
    'payments_refund',
    'lab_testtemplate',
    'lab_testfield',
    'lab_testschedule',
    'lab_testbooking',
    'lab_testresult',
    'lab_testresultitem',
    'rooms_room',
    'rooms_roombed',
    'rooms_roomassignment',
    'rooms_admissionrequest',
    'reviews_review',
    'notifications_notification',
]

TABLE_COLUMN_EXCLUDE = {
    'payments_payment': {
        'amount_paid',
        'due_date',
        'reminder_sent_count',
        'last_reminder_sent',
        'is_overdue',
        'overdue_days',
    },
    'prescriptions_prescription': {
        'refill_status',
        'total_refills_allowed',
        'refills_used',
        'refills_remaining',
        'expiry_date',
        'is_expired',
        'low_stock_alert_sent',
        'last_refill_request_date',
    },
}


def get_sqlite_tables(cur) -> set:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return {row[0] for row in cur.fetchall()}


def pg_columns(cur, table: str) -> List[Tuple[str, str, str, str]]:
    cur.execute(
        """
        SELECT column_name, data_type, udt_name, is_nullable
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    return cur.fetchall()


def sqlite_columns(cur, table: str) -> List[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def sanitize_value(value, data_type: str, udt_name: str, is_nullable: str):
    if value is None:
        if is_nullable == 'YES':
            return None
        if data_type in ('boolean',) or udt_name == 'bool':
            return False
        if data_type in ('smallint', 'integer', 'bigint', 'numeric', 'real', 'double precision'):
            return 0
        return ''

    if data_type == 'boolean' or udt_name == 'bool':
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ('1', 't', 'true', 'y', 'yes'):
                return True
            if v in ('0', 'f', 'false', 'n', 'no', ''):
                return False
        return bool(value)

    if isinstance(value, str):
        return value.encode('cp1252', errors='replace').decode('cp1252')

    return value


def transfer_table(sql_cur, pg_cur, table: str) -> int:
    s_cols = sqlite_columns(sql_cur, table)
    p_meta = pg_columns(pg_cur, table)
    p_cols = [m[0] for m in p_meta]
    excluded_cols = TABLE_COLUMN_EXCLUDE.get(table, set())
    common_cols = [c for c in p_cols if c in s_cols and c not in excluded_cols]

    if not common_cols:
        return 0

    sqlite_cols = ', '.join([f'"{c}"' for c in common_cols])
    sql_cur.execute(f'SELECT {sqlite_cols} FROM "{table}"')
    source_rows = sql_cur.fetchall()
    if not source_rows:
        return 0

    meta_by_col: Dict[str, Tuple[str, str, str]] = {m[0]: (m[1], m[2], m[3]) for m in p_meta}
    rows = []
    for row in source_rows:
        out = []
        for i, col in enumerate(common_cols):
            data_type, udt_name, is_nullable = meta_by_col[col]
            out.append(sanitize_value(row[i], data_type, udt_name, is_nullable))
        rows.append(tuple(out))

    cols_sql = ', '.join([f'"{c}"' for c in common_cols])
    insert_sql = f'INSERT INTO "{table}" ({cols_sql}) VALUES %s'
    execute_values(pg_cur, insert_sql, rows, page_size=500)
    return len(rows)


def set_sequence(cur, table: str):
    cur.execute("SELECT pg_get_serial_sequence(%s, 'id')", (f'public.{table}',))
    seq = cur.fetchone()[0]
    if not seq:
        return
    cur.execute(f'SELECT COALESCE(MAX(id), 1) FROM "{table}"')
    mx = cur.fetchone()[0]
    cur.execute('SELECT setval(%s, %s, true)', (seq, mx))


def main():
    s_conn = sqlite3.connect(SQLITE_DB)
    s_cur = s_conn.cursor()

    p_conn = psycopg2.connect(**PG_CONN)
    p_conn.autocommit = False
    p_cur = p_conn.cursor()

    sqlite_tables = get_sqlite_tables(s_cur)

    targets = [t for t in TABLE_ORDER if t in sqlite_tables]

    if targets:
        quoted = ', '.join([f'"{t}"' for t in targets])
        p_cur.execute(f'TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE')
        p_conn.commit()

    total = 0
    failed: List[Tuple[str, str]] = []

    for table in targets:
        try:
            inserted = transfer_table(s_cur, p_cur, table)
            set_sequence(p_cur, table)
            p_conn.commit()
            total += inserted
            print(f'{table}: inserted {inserted}')
        except Exception as e:
            p_conn.rollback()
            failed.append((table, str(e)))
            print(f'{table}: FAILED {e}')

    print(f'RESTORE_CORE_DONE total_rows={total} failed_tables={len(failed)}')
    for t, e in failed:
        print(f'FAILED {t}: {e}')

    s_cur.close()
    s_conn.close()
    p_cur.close()
    p_conn.close()


if __name__ == '__main__':
    main()
