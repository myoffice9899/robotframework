import os
import xml.etree.ElementTree as ET
from datetime import datetime
import mysql.connector
import sys

db_config = {
    "host": "ps03.zwhhosting.com",
    "port": 3306,
    "user": "zeddpszw_testtorial",
    "password": "Bb@iFmEGaa4e@Ur",
    "database": "zeddpszw_testtorial"
}

def convert_time(time_str):
    """แปลงเวลา Robot Framework เป็น 'YYYY-MM-DD HH:MM:SS'"""
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str.split(".")[0], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error converting time {time_str}: {e}")
        return None

def update_test_results(filepath):
    """อ่าน output.xml และอัปเดตผลลัพธ์ไปยัง MySQL"""
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        run_id = root.attrib.get("generated")

        if not run_id:
            print("No generated attribute found in <robot> tag.")
            return

        global_start = convert_time(run_id)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM test_runs WHERE run_id = %s", (run_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO test_runs (run_id, start_time, status)
                VALUES (%s, %s, %s)
            """, (run_id, global_start, "PASS"))
            conn.commit()
            print(f"Inserted new test_run with run_id {run_id}")

        for suite in root.findall('./suite'):
            parse_suite(suite, run_id, conn)

        conn.close()
        print(f"Test results updated successfully. Run ID: {run_id}")
    except Exception as e:
        print(f"Error updating test results: {e}")

def parse_suite(suite_elem, run_id, conn):
    """อ่านข้อมูล Suite และอัปเดตผลลัพธ์"""
    suite_name = suite_elem.attrib.get("name")
    suite_id = suite_elem.attrib.get("id")
    status_elem = suite_elem.find('status')
    suite_status = status_elem.get("status", "PASS") if status_elem is not None else "PASS"

    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO test_suites (run_id, suite_name, suite_id, status)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                status=VALUES(status)
        """, (run_id, suite_name, suite_id, suite_status))
        conn.commit()
    except Exception as e:
        print(f"Error updating suite {suite_id}: {e}")

    for test in suite_elem.findall('./test'):
        parse_test(test, suite_id, conn)

def parse_test(test_elem, suite_id, conn):
    """อ่านข้อมูล Test Case และอัปเดตผลลัพธ์"""
    test_name = test_elem.attrib.get("name")
    test_id = test_elem.attrib.get("id")
    status_elem = test_elem.find('status')
    test_status = status_elem.get("status", "PASS") if status_elem is not None else "PASS"

    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO test_cases (suite_id, test_name, test_id, status)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                status=VALUES(status)
        """, (suite_id, test_name, test_id, test_status))
        conn.commit()
    except Exception as e:
        print(f"Error updating test case {test_id}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        xml_file = sys.argv[1]
        update_test_results(xml_file)
    else:
        print("No XML file provided.")
