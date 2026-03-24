import sqlite3

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


def clean_text(value):
    if value is None:
        return ''
    if isinstance(value, str):
        return value.encode('cp1252', errors='replace').decode('cp1252')
    return value


def main():
    s_conn = sqlite3.connect(SQLITE_DB)
    s_cur = s_conn.cursor()

    p_conn = psycopg2.connect(**PG_CONN)
    p_cur = p_conn.cursor()

    try:
        p_cur.execute(
            'TRUNCATE TABLE "payments_refund", "payments_payment", '
            '"prescriptions_prescriptionitem", "prescriptions_prescription" '
            'RESTART IDENTITY CASCADE'
        )

        s_cur.execute(
            'SELECT id, payment_type, amount, status, payment_method, paid_at, receipt_file, notes, '
            'created_at, updated_at, appointment_id, doctor_id, lab_booking_id, patient_id '
            'FROM payments_payment ORDER BY id'
        )
        payment_rows_src = s_cur.fetchall()
        payment_rows = []
        for r in payment_rows_src:
            payment_rows.append((
                r[0],
                clean_text(r[1] or 'APPOINTMENT'),
                r[2] if r[2] is not None else 0,
                clean_text(r[3] or 'UNPAID'),
                clean_text(r[4] or 'CASH'),
                r[5],
                clean_text(r[6]) if r[6] else None,
                clean_text(r[7]),
                r[8],
                r[9],
                r[10],
                r[11],
                r[12],
                r[13],
                0,
                None,
                False,
                None,
                0,
                0,
            ))

        if payment_rows:
            execute_values(
                p_cur,
                'INSERT INTO "payments_payment" '
                '(id,payment_type,amount,status,payment_method,paid_at,receipt_file,notes,created_at,updated_at,'
                'appointment_id,doctor_id,lab_booking_id,patient_id,amount_paid,due_date,is_overdue,last_reminder_sent,overdue_days,reminder_sent_count) '
                'VALUES %s',
                payment_rows,
            )

        s_cur.execute(
            'SELECT id, payment_id, reason, status, refunded_at, notes, created_at FROM payments_refund ORDER BY id'
        )
        refund_rows_src = s_cur.fetchall()
        refund_rows = []
        for r in refund_rows_src:
            refund_rows.append((
                r[0], r[1], clean_text(r[2]), clean_text(r[3] or 'PENDING'), r[4], clean_text(r[5]), r[6]
            ))

        if refund_rows:
            execute_values(
                p_cur,
                'INSERT INTO "payments_refund" (id,payment_id,reason,status,refunded_at,notes,created_at) VALUES %s',
                refund_rows,
            )

        s_cur.execute(
            'SELECT id, notes, advice, follow_up_date, pdf_file, created_at, updated_at, appointment_id, doctor_id, patient_id '
            'FROM prescriptions_prescription ORDER BY id'
        )
        rx_rows_src = s_cur.fetchall()
        rx_rows = []
        for r in rx_rows_src:
            rx_rows.append((
                r[0],
                clean_text(r[1]),
                clean_text(r[2]),
                r[3],
                clean_text(r[4]) if r[4] else None,
                r[5],
                r[6],
                r[7],
                r[8],
                r[9],
                None,
                False,
                None,
                False,
                'ACTIVE',
                0,
                0,
                0,
            ))

        if rx_rows:
            execute_values(
                p_cur,
                'INSERT INTO "prescriptions_prescription" '
                '(id,notes,advice,follow_up_date,pdf_file,created_at,updated_at,appointment_id,doctor_id,patient_id,'
                'expiry_date,is_expired,last_refill_request_date,low_stock_alert_sent,refill_status,refills_remaining,refills_used,total_refills_allowed) '
                'VALUES %s',
                rx_rows,
            )

        s_cur.execute(
            'SELECT id, medicine_name, dosage, frequency, duration, timing, instructions, prescription_id '
            'FROM prescriptions_prescriptionitem ORDER BY id'
        )
        item_rows_src = s_cur.fetchall()
        item_rows = []
        for r in item_rows_src:
            item_rows.append((
                r[0], clean_text(r[1]), clean_text(r[2]), clean_text(r[3] or 'OD'),
                clean_text(r[4]), clean_text(r[5] or 'AFTER_MEAL'), clean_text(r[6]), r[7]
            ))

        if item_rows:
            execute_values(
                p_cur,
                'INSERT INTO "prescriptions_prescriptionitem" '
                '(id,medicine_name,dosage,frequency,duration,timing,instructions,prescription_id) VALUES %s',
                item_rows,
            )

        p_cur.execute("SELECT setval(pg_get_serial_sequence('payments_payment','id'), COALESCE(MAX(id),1), true) FROM payments_payment")
        p_cur.execute("SELECT setval(pg_get_serial_sequence('payments_refund','id'), COALESCE(MAX(id),1), true) FROM payments_refund")
        p_cur.execute("SELECT setval(pg_get_serial_sequence('prescriptions_prescription','id'), COALESCE(MAX(id),1), true) FROM prescriptions_prescription")
        p_cur.execute("SELECT setval(pg_get_serial_sequence('prescriptions_prescriptionitem','id'), COALESCE(MAX(id),1), true) FROM prescriptions_prescriptionitem")

        p_conn.commit()
        print(f'RESTORED payments={len(payment_rows)} refunds={len(refund_rows)} prescriptions={len(rx_rows)} prescription_items={len(item_rows)}')
    finally:
        s_cur.close()
        s_conn.close()
        p_cur.close()
        p_conn.close()


if __name__ == '__main__':
    main()
