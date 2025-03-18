import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
import mysql.connector

# 🔹 ข้อมูลการเชื่อมต่อ MySQL
db_config = {
    "host": "ps03.zwhhosting.com",
    "port": 3306,
    "user": "zeddpszw_testtorial",
    "password": "Bb@iFmEGaa4e@Ur",
    "database": "zeddpszw_testtorial"
}

def convert_time(time_str):
    """ แปลงเวลาในรูปแบบ Robot Framework เป็น 'YYYY-MM-DD HH:MM:SS' """
    if not time_str:
        return None
    try:
        if "." in time_str:
            time_str = time_str.split(".")[0]  # ตัดส่วนเศษวินาทีออก
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"❌ Error converting time {time_str}: {e}")
        return None

def process_test_results(xml_file):
    """ อ่าน `output.xml` และบันทึกข้อมูลลง MySQL """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        run_id = root.attrib.get("generated")
        if not run_id:
            print("❌ No run_id found in XML file.")
            return

        global_start = convert_time(run_id)
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 🔹 ตรวจสอบว่ามี record `test_runs` หรือยัง
        cursor.execute("SELECT COUNT(*) FROM test_runs WHERE run_id = %s", (run_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO test_runs (run_id, start_time, status, total_tests, passed_tests, failed_tests)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (run_id, global_start, "PASS", 0, 0, 0))
            conn.commit()
            print(f"✅ Inserted new test_run: {run_id}")

        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        # 🔹 Process test suites
        for suite in root.findall('./suite'):
            suite_name = suite.attrib.get("name")
            suite_id = suite.attrib.get("id")
            
            cursor.execute("""
                INSERT INTO test_suites (run_id, suite_name, suite_id, status, total_tests, passed_tests, failed_tests)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE status=VALUES(status)
            """, (run_id, suite_name, suite_id, "PASS", 0, 0, 0))
            conn.commit()
            
            # 🔹 Process test cases
            for test in suite.findall('./test'):
                test_name = test.attrib.get("name")
                test_id = test.attrib.get("id")

                status_elem = test.find('status')
                status = status_elem.get("status", "PASS")
                start_time = convert_time(status_elem.get("starttime"))
                end_time = convert_time(status_elem.get("endtime"))

                cursor.execute("""
                    INSERT INTO test_cases (suite_id, test_name, test_id, status, start_time, end_time)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE status=VALUES(status)
                """, (suite_id, test_name, test_id, status, start_time, end_time))
                conn.commit()

                total_tests += 1
                if status.upper() == "PASS":
                    passed_tests += 1
                else:
                    failed_tests += 1

        # 🔹 อัปเดต `test_runs` ด้วยจำนวนเคสทั้งหมด
        cursor.execute("""
            UPDATE test_runs
            SET total_tests = %s, passed_tests = %s, failed_tests = %s, status = %s
            WHERE run_id = %s
        """, (total_tests, passed_tests, failed_tests, "PASS" if failed_tests == 0 else "FAIL", run_id))
        conn.commit()

        conn.close()
        print(f"✅ XML processed: {xml_file}")
        print(f"   Total: {total_tests}, Passed: {passed_tests}, Failed: {failed_tests}")

    except Exception as e:
        print(f"❌ Error processing XML: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Please provide the XML file path")
        sys.exit(1)

    xml_file = sys.argv[1]
    if not os.path.exists(xml_file):
        print(f"❌ File not found: {xml_file}")
        sys.exit(1)

    process_test_results(xml_file)
