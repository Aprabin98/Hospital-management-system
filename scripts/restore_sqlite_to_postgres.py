import sqlite3
from typing import List, Dict, Tuple

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

# Keep migration metadata untouched so Django migration state remains valid.
EXCLUDED_TABLES = {
    'django_migrations',
    # Schema changed with strict non-null workflow fields; skip legacy incompatible rows.
    'appointments_waitinglist',
}


def get_sqlite_tables(cur) -> List[str]:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    return [row[0] for row in cur.fetchall()]


def get_postgres_tables(cur) -> List[str]:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_type='BASE TABLE'
        ORDER BY table_name
        """
    )
    return [row[0] for row in cur.fetchall()]


def sqlite_columns(cur, table: str) -> List[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]


def postgres_columns(cur, table: str) -> List[str]:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
        """,
        (table,),
    )
    return [row[0] for row in cur.fetchall()]


def build_transfer_plan(sqlite_cur, pg_cur) -> Dict[str, List[str]]:
    s_tables = set(get_sqlite_tables(sqlite_cur))
    p_tables = set(get_postgres_tables(pg_cur))
    common_tables = sorted((s_tables & p_tables) - EXCLUDED_TABLES)

    plan: Dict[str, List[str]] = {}
    for table in common_tables:
        s_cols = sqlite_columns(sqlite_cur, table)
        p_cols = postgres_columns(pg_cur, table)
        cols = [c for c in p_cols if c in s_cols]
        if cols:
            plan[table] = cols
    return plan


def truncate_target_tables(pg_cur, tables: List[str]) -> None:
    if not tables:
        return
    quoted = ', '.join([f'"{t}"' for t in tables])
    pg_cur.execute(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")


def copy_table(sqlite_cur, pg_cur, table: str, cols: List[str]) -> int:
    col_sql = ', '.join([f'"{c}"' for c in cols])
    sqlite_cur.execute(f"SELECT {', '.join(cols)} FROM {table}")
    raw_rows = sqlite_cur.fetchall()
    rows = []
    for row in raw_rows:
        cleaned = []
        for value in row:
            if isinstance(value, str):
                # Current PostgreSQL cluster encoding is WIN1252, so normalize text safely.
                value = value.encode('cp1252', errors='replace').decode('cp1252')
            cleaned.append(value)
        rows.append(tuple(cleaned))
    if not rows:
        return 0

    insert_sql = f"INSERT INTO \"{table}\" ({col_sql}) VALUES %s"
    execute_values(pg_cur, insert_sql, rows, page_size=1000)
    return len(rows)


def reset_sequences(pg_cur, tables: List[str]) -> None:
    for table in tables:
        pg_cur.execute(
            """
            SELECT c.column_name
            FROM information_schema.columns c
            WHERE c.table_schema='public' AND c.table_name=%s AND c.column_name='id'
            """,
            (table,),
        )
        has_id = pg_cur.fetchone()
        if not has_id:
            continue

        pg_cur.execute("SELECT pg_get_serial_sequence(%s, 'id')", (f'public.{table}',))
        seq = pg_cur.fetchone()[0]
        if not seq:
            continue

        pg_cur.execute(f'SELECT COALESCE(MAX(id), 1) FROM "{table}"')
        max_id = pg_cur.fetchone()[0]
        pg_cur.execute("SELECT setval(%s, %s, true)", (seq, max_id))


def main() -> None:
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(**PG_CONN)
    pg_conn.autocommit = False
    pg_cur = pg_conn.cursor()

    try:
        plan = build_transfer_plan(sqlite_cur, pg_cur)
        tables = list(plan.keys())

        truncate_target_tables(pg_cur, tables)

        total_rows = 0
        failed_tables: List[Tuple[str, str]] = []
        for table in tables:
            try:
                pg_cur.execute('SAVEPOINT table_restore')
                inserted = copy_table(sqlite_cur, pg_cur, table, plan[table])
                total_rows += inserted
                print(f'{table}: inserted {inserted} rows')
                pg_cur.execute('RELEASE SAVEPOINT table_restore')
            except Exception as table_error:
                pg_cur.execute('ROLLBACK TO SAVEPOINT table_restore')
                pg_cur.execute('RELEASE SAVEPOINT table_restore')
                failed_tables.append((table, str(table_error)))
                print(f'{table}: skipped due to error: {table_error}')

        reset_sequences(pg_cur, tables)
        pg_conn.commit()
        print(f'RESTORE_OK total_rows={total_rows} tables={len(tables)} failed={len(failed_tables)}')
        for table, err in failed_tables:
            print(f'FAILED_TABLE {table}: {err}')
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        sqlite_cur.close()
        sqlite_conn.close()
        pg_cur.close()
        pg_conn.close()


if __name__ == '__main__':
    main()
