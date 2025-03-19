import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
import mysql.connector
import pytz

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db_config = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DATABASE")
}

def convert_time(time_str):
    """แปลงเวลาในรูปแบบ Robot Framework (เช่น 2025-03-12T06:03:52.584829) เป็นเวลาประเทศไทย (YYYY-MM-DD HH:MM:SS)"""
    if not time_str:
        return None
    try:
        # ตัดส่วนหลังจุดออก
        dt = datetime.strptime(time_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
        # สมมติว่าเวลาที่รับเข้ามาเป็นเวลา UTC (ปรับตามความเหมาะสมหากไม่ใช่)
        utc = pytz.utc
        dt_utc = utc.localize(dt)
        # แปลงเป็นเวลาประเทศไทย (Asia/Bangkok) ซึ่งมี offset +7 ชั่วโมง
        thailand_tz = pytz.timezone("Asia/Bangkok")
        dt_thailand = dt_utc.astimezone(thailand_tz)
        return dt_thailand.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error converting time {time_str}: {e}")
        return None

def create_tables():
    """สร้างตารางทั้งหมดถ้าไม่มี"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_runs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            run_id VARCHAR(100) UNIQUE NOT NULL,
            start_time DATETIME NOT NULL,
            status ENUM('PASS', 'FAIL', 'ERROR') NOT NULL,
            total_tests INT DEFAULT 0,
            passed_tests INT DEFAULT 0,
            failed_tests INT DEFAULT 0,
            execution_time FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_suites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            run_id VARCHAR(100) NOT NULL,
            suite_name VARCHAR(255) NOT NULL,
            suite_id VARCHAR(100) NOT NULL,
            parent_suite_id VARCHAR(100),
            status ENUM('PASS', 'FAIL', 'ERROR') NOT NULL,
            total_tests INT DEFAULT 0,
            passed_tests INT DEFAULT 0,
            failed_tests INT DEFAULT 0,
            execution_time FLOAT,
            UNIQUE KEY unique_suite_run (run_id, suite_id),
            FOREIGN KEY (run_id) REFERENCES test_runs(run_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_cases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            suite_id INT NOT NULL,
            test_name VARCHAR(255) NOT NULL,
            test_id VARCHAR(100) UNIQUE NOT NULL,
            status ENUM('PASS', 'FAIL', 'ERROR') NOT NULL,
            start_time DATETIME,
            end_time DATETIME,
            execution_time FLOAT,
            error_message TEXT,
            FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_keywords (
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_id VARCHAR(100) NOT NULL,
            keyword_name VARCHAR(255) NOT NULL,
            keyword_type ENUM('SETUP', 'TEARDOWN', 'KEYWORD') NOT NULL,
            start_time DATETIME,
            end_time DATETIME,
            execution_time FLOAT,
            status ENUM('PASS', 'FAIL', 'ERROR') NOT NULL,
            error_message TEXT,
            FOREIGN KEY (test_id) REFERENCES test_cases(test_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_status (
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_run_id VARCHAR(100) NOT NULL,
            test_id VARCHAR(100) NOT NULL,
            status ENUM('PASS', 'FAIL', 'ERROR') NOT NULL,
            execution_time FLOAT,
            FOREIGN KEY (test_run_id) REFERENCES test_runs(run_id) ON DELETE CASCADE,
            FOREIGN KEY (test_id) REFERENCES test_cases(test_id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """)
        
        conn.commit()
        conn.close()
        print("Tables created successfully if not exist.")
    except Exception as e:
        print(f"Error creating tables: {e}")

def parse_suite(suite_elem, run_id, conn):
    """
    อ่านข้อมูล suite และบันทึกลงใน test_suites, test_cases, test_status
    ใช้ recursion สำหรับ child <suite>
    Return (total_tests, passed_tests, failed_tests)
    """
    suite_name = suite_elem.attrib.get("name")
    suite_id = suite_elem.attrib.get("id")
    
    status_elem = suite_elem.find('status')
    if status_elem is not None:
        suite_status = status_elem.get("status", "PASS")
        elapsed = status_elem.get("elapsed")
        try:
            suite_execution = float(elapsed)/1000 if elapsed else 0
        except:
            suite_execution = 0
    else:
        suite_status = "PASS"
        suite_execution = 0

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    cursor = conn.cursor()
    
    print(f"Processing suite '{suite_name}' (ID: {suite_id})")
    try:
        cursor.execute("""
            INSERT INTO test_suites (run_id, suite_name, suite_id, status, execution_time)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                status=VALUES(status),
                execution_time=VALUES(execution_time)
        """, (run_id, suite_name, suite_id, suite_status, suite_execution))
        conn.commit()
    except Exception as e:
        print(f"Error inserting/updating suite {suite_id}: {e}")

    tests = suite_elem.findall('./test')
    print(f"Found {len(tests)} test(s) in suite '{suite_id}'")
    for test in tests:
        test_name = test.attrib.get("name")
        test_id = test.attrib.get("id")
        
        test_status_elem = test.find('status')
        if test_status_elem is not None:
            t_status = test_status_elem.get("status", "PASS")
            starttime = convert_time(test_status_elem.get("starttime"))
            endtime = convert_time(test_status_elem.get("endtime"))
            try:
                t_elapsed = float(test_status_elem.get("elapsed"))/1000 if test_status_elem.get("elapsed") else 0
            except Exception as ex:
                t_elapsed = 0
                print(f"Error converting elapsed for test {test_id}: {ex}")
        else:
            t_status = "PASS"
            starttime = None
            endtime = None
            t_elapsed = 0

        cursor.execute("""
            SELECT id FROM test_suites WHERE run_id = %s AND suite_id = %s
        """, (run_id, suite_id))
        suite_row = cursor.fetchone()
        if suite_row:
            suite_db_id = suite_row[0]
        else:
            print(f"Error: ไม่พบ suite ในฐานข้อมูล สำหรับ run_id {run_id} และ suite_id {suite_id}")
            continue

        try:
            cursor.execute("""
                INSERT INTO test_cases (suite_id, test_name, test_id, status, start_time, end_time, execution_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status=VALUES(status),
                    start_time=VALUES(start_time),
                    end_time=VALUES(end_time),
                    execution_time=VALUES(execution_time)
            """, (suite_db_id, test_name, test_id, t_status, starttime, endtime, t_elapsed))
            conn.commit()
        except Exception as e:
            print(f"Error inserting/updating test case {test_id}: {e}")
        
        try:
            cursor.execute("""
                INSERT INTO test_status (test_run_id, test_id, status, execution_time)
                VALUES (%s, %s, %s, %s)
            """, (run_id, test_id, t_status, t_elapsed))
            conn.commit()
        except Exception as e:
            print(f"Error inserting test status for {test_id}: {e}")
        
        total_tests += 1
        if t_status.upper() == "PASS":
            passed_tests += 1
        else:
            failed_tests += 1

    # ประมวลผล child suite (recursive)
    child_suites = suite_elem.findall('./suite')
    print(f"Found {len(child_suites)} child suite(s) in suite '{suite_id}'")
    for child_suite in child_suites:
        ct, cp, cf = parse_suite(child_suite, run_id, conn)
        total_tests += ct
        passed_tests += cp
        failed_tests += cf

    suite_status_final = "PASS" if failed_tests == 0 else "FAIL"
    try:
        cursor.execute("""
            UPDATE test_suites
            SET total_tests = %s,
                passed_tests = %s,
                failed_tests = %s,
                status = %s
            WHERE run_id = %s AND suite_id = %s
        """, (total_tests, passed_tests, failed_tests, suite_status_final, run_id, suite_id))
        conn.commit()
    except Exception as e:
        print(f"Error updating suite {suite_id} stats: {e}")

    print(f"Suite '{suite_id}' stats: Total={total_tests}, Passed={passed_tests}, Failed={failed_tests}")
    return total_tests, passed_tests, failed_tests

def process_test_suites(filepath):
    """
    ประมวลผลไฟล์ XML:
    - อ่าน run_id จาก attribute "generated" ในแท็ก <robot>
    - สร้าง record ใน test_runs ถ้ายังไม่มี
    - เรียก parse_suite() สำหรับทุก <suite> ชั้นบนสุด
    - รวมสถิติทั้งหมดแล้วอัปเดตใน test_runs
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        run_id = root.attrib.get("generated")
        if not run_id:
            print("No generated attribute found in <robot> tag.")
            return

        global_start = convert_time(run_id)
        print(f"Run ID: {run_id}, Start Time: {global_start}")

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
        else:
            print(f"Test_run with run_id {run_id} already exists.")

        run_total_tests = 0
        run_passed_tests = 0
        run_failed_tests = 0

        top_suites = root.findall('./suite')
        print(f"Found {len(top_suites)} top-level suite(s).")
        for suite in top_suites:
            suite_total, suite_passed, suite_failed = parse_suite(suite, run_id, conn)
            run_total_tests += suite_total
            run_passed_tests += suite_passed
            run_failed_tests += suite_failed

        run_status = "PASS" if run_failed_tests == 0 else "FAIL"
        try:
            cursor.execute("""
                UPDATE test_runs
                SET total_tests = %s,
                    passed_tests = %s,
                    failed_tests = %s,
                    status = %s
                WHERE run_id = %s
            """, (run_total_tests, run_passed_tests, run_failed_tests, run_status, run_id))
            conn.commit()
        except Exception as e:
            print(f"Error updating test_runs stats: {e}")
        conn.close()
        print(f"Processed {filepath} successfully. Run ID: {run_id} (Total: {run_total_tests}, Passed: {run_passed_tests}, Failed: {run_failed_tests})")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    create_tables()

    # หากมี argument ส่งเข้ามาเป็น path ไฟล์ XML
    if len(sys.argv) > 1:
        xml_file = sys.argv[1]
        if os.path.exists(xml_file) and xml_file.endswith(".xml"):
            process_test_suites(xml_file)
        else:
            print(f"File not found or invalid file type: {xml_file}")
    else:
        # หากไม่ส่ง argument ให้ประมวลผลไฟล์ทั้งหมดในโฟลเดอร์ uploads
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith(".xml"):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                process_test_suites(filepath)
