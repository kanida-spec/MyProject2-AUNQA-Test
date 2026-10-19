"""
tracker.py - Core database and business logic for Quality Assurance (EdPEx & AUN-QA)
and Project Strategic Tracking System.
Faculty of Science and Technology, Hatyai University.
"""

import sqlite3
import os
import io
import csv
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "qa_tracking.db")

VALID_STATUSES = ["not_started", "in_progress", "under_review", "completed", "delayed"]
VALID_PDCA_STAGES = ["plan", "do", "check", "act"]

EDPEX_CATEGORIES = [
    "หมวด 1: การนำองค์กร (Leadership)",
    "หมวด 2: กลยุทธ์ (Strategy)",
    "หมวด 3: ลูกค้าและผู้มีส่วนได้ส่วนเสีย (Customers)",
    "หมวด 4: การวัด การวิเคราะห์ และการจัดการความรู้ (Measurement & KM)",
    "หมวด 5: บุคลากร (Workforce)",
    "หมวด 6: การปฏิบัติการ (Operations)",
    "หมวด 7: ผลลัพธ์ (Results)",
    "AUN-QA: ระดับหลักสูตร (Programme Level)",
]


def get_connection(db_path=None):
    """Create and return a database connection with row factory enabled."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None):
    """Initialize database tables with parameterized execution."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS qa_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            target_value REAL NOT NULL DEFAULT 0.0,
            actual_value REAL NOT NULL DEFAULT 0.0,
            unit TEXT NOT NULL,
            description TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            department TEXT NOT NULL,
            leader TEXT NOT NULL,
            fiscal_year INTEGER NOT NULL,
            start_date TEXT,
            end_date TEXT,
            budget_allocated REAL NOT NULL DEFAULT 0.0,
            budget_spent REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'not_started',
            pdca_stage TEXT NOT NULL DEFAULT 'plan',
            objective TEXT,
            output TEXT,
            outcome TEXT,
            problems TEXT,
            solutions TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS project_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            indicator_id INTEGER NOT NULL,
            contribution_note TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (indicator_id) REFERENCES qa_indicators(id) ON DELETE CASCADE,
            UNIQUE(project_id, indicator_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            doc_type TEXT NOT NULL DEFAULT 'link',
            created_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()


def validate_project_payload(data):
    """Validate project payload and raise ValueError on any violation."""
    code = str(data.get("code", "")).strip()
    if not code:
        raise ValueError("Project code cannot be empty.")

    title = str(data.get("title", "")).strip()
    if not title:
        raise ValueError("Project title cannot be empty.")

    leader = str(data.get("leader", "")).strip()
    if not leader:
        raise ValueError("Project leader cannot be empty.")

    department = str(data.get("department", "")).strip()
    if not department:
        raise ValueError("Department cannot be empty.")

    category = str(data.get("category", "")).strip()
    if not category:
        raise ValueError("Category cannot be empty.")

    try:
        fiscal_year = int(data.get("fiscal_year", 2567))
        if fiscal_year < 2500 or fiscal_year > 2650:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Fiscal year must be a valid Buddhist Era year (e.g., 2567).")

    try:
        budget_allocated = float(data.get("budget_allocated", 0.0))
        if budget_allocated < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Budget allocated must be a positive number.")

    try:
        budget_spent = float(data.get("budget_spent", 0.0))
        if budget_spent < 0:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Budget spent must be a non-negative number.")

    if budget_spent > budget_allocated and budget_allocated > 0:
        raise ValueError("Budget spent cannot exceed allocated budget.")

    status = str(data.get("status", "not_started")).strip().lower()
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: '{status}'. Must be one of {VALID_STATUSES}")

    pdca_stage = str(data.get("pdca_stage", "plan")).strip().lower()
    if pdca_stage not in VALID_PDCA_STAGES:
        raise ValueError(f"Invalid PDCA stage: '{pdca_stage}'. Must be one of {VALID_PDCA_STAGES}")

    return {
        "code": code,
        "title": title,
        "category": category,
        "department": department,
        "leader": leader,
        "fiscal_year": fiscal_year,
        "start_date": data.get("start_date", ""),
        "end_date": data.get("end_date", ""),
        "budget_allocated": budget_allocated,
        "budget_spent": budget_spent,
        "status": status,
        "pdca_stage": pdca_stage,
        "objective": data.get("objective", ""),
        "output": data.get("output", ""),
        "outcome": data.get("outcome", ""),
        "problems": data.get("problems", ""),
        "solutions": data.get("solutions", ""),
    }


def add_project(data, db_path=None):
    """Add a new strategic project."""
    cleaned = validate_project_payload(data)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check unique code
    cursor.execute("SELECT id FROM projects WHERE code = ?", (cleaned["code"],))
    if cursor.fetchone() is not None:
        conn.close()
        raise ValueError(f"Project code '{cleaned['code']}' already exists.")

    now = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO projects (
            code, title, category, department, leader, fiscal_year,
            start_date, end_date, budget_allocated, budget_spent,
            status, pdca_stage, objective, output, outcome,
            problems, solutions, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cleaned["code"],
            cleaned["title"],
            cleaned["category"],
            cleaned["department"],
            cleaned["leader"],
            cleaned["fiscal_year"],
            cleaned["start_date"],
            cleaned["end_date"],
            cleaned["budget_allocated"],
            cleaned["budget_spent"],
            cleaned["status"],
            cleaned["pdca_stage"],
            cleaned["objective"],
            cleaned["output"],
            cleaned["outcome"],
            cleaned["problems"],
            cleaned["solutions"],
            now,
            now,
        ),
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return project_id


def update_project(project_id, data, db_path=None):
    """Update an existing project."""
    cleaned = validate_project_payload(data)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Ensure project exists
    cursor.execute("SELECT id, code FROM projects WHERE id = ?", (project_id,))
    existing = cursor.fetchone()
    if existing is None:
        conn.close()
        raise ValueError(f"Project with ID {project_id} not found.")

    # Ensure new code doesn't collide with other projects
    cursor.execute("SELECT id FROM projects WHERE code = ? AND id != ?", (cleaned["code"], project_id))
    if cursor.fetchone() is not None:
        conn.close()
        raise ValueError(f"Project code '{cleaned['code']}' is already used by another project.")

    now = datetime.now().isoformat()
    cursor.execute(
        """
        UPDATE projects SET
            code = ?, title = ?, category = ?, department = ?, leader = ?,
            fiscal_year = ?, start_date = ?, end_date = ?, budget_allocated = ?,
            budget_spent = ?, status = ?, pdca_stage = ?, objective = ?,
            output = ?, outcome = ?, problems = ?, solutions = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            cleaned["code"],
            cleaned["title"],
            cleaned["category"],
            cleaned["department"],
            cleaned["leader"],
            cleaned["fiscal_year"],
            cleaned["start_date"],
            cleaned["end_date"],
            cleaned["budget_allocated"],
            cleaned["budget_spent"],
            cleaned["status"],
            cleaned["pdca_stage"],
            cleaned["objective"],
            cleaned["output"],
            cleaned["outcome"],
            cleaned["problems"],
            cleaned["solutions"],
            now,
            project_id,
        ),
    )
    conn.commit()
    conn.close()
    return True


def delete_project(project_id, db_path=None):
    """Delete a project and its cascades."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_project(project_id, db_path=None):
    """Get project by ID including linked indicators and evidence."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None

    project = dict(row)

    # Linked indicators
    cursor.execute(
        """
        SELECT i.*, pi.contribution_note
        FROM qa_indicators i
        JOIN project_indicators pi ON i.id = pi.indicator_id
        WHERE pi.project_id = ?
        ORDER BY i.code ASC
        """,
        (project_id,),
    )
    project["indicators"] = [dict(r) for r in cursor.fetchall()]

    # Evidence links
    cursor.execute(
        "SELECT * FROM evidence_links WHERE project_id = ? ORDER BY id DESC",
        (project_id,),
    )
    project["evidence"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return project


def list_projects(category=None, status=None, fiscal_year=None, search=None, db_path=None):
    """List and filter projects."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM projects WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if status:
        query += " AND status = ?"
        params.append(status)

    if fiscal_year:
        query += " AND fiscal_year = ?"
        params.append(int(fiscal_year))

    if search:
        search_pattern = f"%{search.strip()}%"
        query += " AND (code LIKE ? OR title LIKE ? OR leader LIKE ? OR department LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    query += " ORDER BY fiscal_year DESC, code ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_qa_indicator(data, db_path=None):
    """Add a QA indicator (EdPEx or AUN-QA)."""
    code = str(data.get("code", "")).strip()
    name = str(data.get("name", "")).strip()
    category = str(data.get("category", "")).strip()
    unit = str(data.get("unit", "")).strip()

    if not code or not name or not category or not unit:
        raise ValueError("Indicator code, name, category, and unit are required.")

    target = float(data.get("target_value", 0.0))
    actual = float(data.get("actual_value", 0.0))
    desc = data.get("description", "")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM qa_indicators WHERE code = ?", (code,))
    if cursor.fetchone() is not None:
        conn.close()
        raise ValueError(f"Indicator code '{code}' already exists.")

    cursor.execute(
        """
        INSERT INTO qa_indicators (code, name, category, target_value, actual_value, unit, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (code, name, category, target, actual, unit, desc),
    )
    indicator_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return indicator_id


def update_qa_indicator_result(indicator_id, actual_value, db_path=None):
    """Update actual achieved value of an indicator."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE qa_indicators SET actual_value = ? WHERE id = ?",
        (float(actual_value), indicator_id),
    )
    conn.commit()
    conn.close()


def list_qa_indicators(category=None, db_path=None):
    """List QA indicators with project counts."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = """
        SELECT i.*, COUNT(pi.project_id) as linked_project_count
        FROM qa_indicators i
        LEFT JOIN project_indicators pi ON i.id = pi.indicator_id
    """
    params = []
    if category:
        query += " WHERE i.category = ?"
        params.append(category)

    query += " GROUP BY i.id ORDER BY i.category ASC, i.code ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def link_project_indicator(project_id, indicator_id, note="", db_path=None):
    """Link a project to an EdPEx/AUN-QA indicator."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT OR REPLACE INTO project_indicators (project_id, indicator_id, contribution_note)
            VALUES (?, ?, ?)
            """,
            (project_id, indicator_id, note),
        )
        conn.commit()
    finally:
        conn.close()


def unlink_project_indicator(project_id, indicator_id, db_path=None):
    """Remove link between a project and an indicator."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM project_indicators WHERE project_id = ? AND indicator_id = ?",
        (project_id, indicator_id),
    )
    conn.commit()
    conn.close()


def add_evidence_link(project_id, title, url, doc_type="link", db_path=None):
    """Add evidence link to support QA audit & SAR."""
    title = str(title).strip()
    url = str(url).strip()
    if not title or not url:
        raise ValueError("Evidence title and URL cannot be empty.")

    now = datetime.now().isoformat()
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO evidence_links (project_id, title, url, doc_type, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (project_id, title, url, doc_type, now),
    )
    evidence_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return evidence_id


def delete_evidence_link(evidence_id, db_path=None):
    """Delete an evidence record."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evidence_links WHERE id = ?", (evidence_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_dashboard_summary(fiscal_year=None, db_path=None):
    """Compute executive dashboard metrics."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    where_clause = ""
    params = []
    if fiscal_year:
        where_clause = " WHERE fiscal_year = ?"
        params.append(int(fiscal_year))

    # Overall project and budget summary
    cursor.execute(
        f"""
        SELECT
            COUNT(*) as total_projects,
            SUM(budget_allocated) as total_budget_allocated,
            SUM(budget_spent) as total_budget_spent,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_projects,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_projects,
            SUM(CASE WHEN status = 'delayed' THEN 1 ELSE 0 END) as delayed_projects,
            SUM(CASE WHEN status = 'under_review' THEN 1 ELSE 0 END) as under_review_projects,
            SUM(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) as not_started_projects
        FROM projects
        {where_clause}
        """,
        params,
    )
    summary_row = dict(cursor.fetchone())
    total_projects = summary_row["total_projects"] or 0
    total_budget_allocated = summary_row["total_budget_allocated"] or 0.0
    total_budget_spent = summary_row["total_budget_spent"] or 0.0

    budget_utilization = 0.0
    if total_budget_allocated > 0:
        budget_utilization = round((total_budget_spent / total_budget_allocated) * 100, 1)

    completion_rate = 0.0
    if total_projects > 0:
        completion_rate = round((summary_row["completed_projects"] / total_projects) * 100, 1)

    # Status distribution
    status_counts = {
        "completed": summary_row["completed_projects"] or 0,
        "in_progress": summary_row["in_progress_projects"] or 0,
        "delayed": summary_row["delayed_projects"] or 0,
        "under_review": summary_row["under_review_projects"] or 0,
        "not_started": summary_row["not_started_projects"] or 0,
    }

    # Category distribution
    cursor.execute(
        f"""
        SELECT category, COUNT(*) as count, SUM(budget_allocated) as budget
        FROM projects
        {where_clause}
        GROUP BY category
        ORDER BY count DESC
        """,
        params,
    )
    category_distribution = [dict(r) for r in cursor.fetchall()]

    # QA Indicators summary
    cursor.execute(
        """
        SELECT
            COUNT(*) as total_indicators,
            SUM(CASE WHEN actual_value >= target_value AND target_value > 0 THEN 1 ELSE 0 END) as achieved_indicators
        FROM qa_indicators
        """
    )
    qa_row = dict(cursor.fetchone())
    total_indicators = qa_row["total_indicators"] or 0
    achieved_indicators = qa_row["achieved_indicators"] or 0
    qa_achievement_rate = round((achieved_indicators / total_indicators * 100), 1) if total_indicators > 0 else 0.0

    conn.close()

    return {
        "fiscal_year": fiscal_year,
        "total_projects": total_projects,
        "total_budget_allocated": total_budget_allocated,
        "total_budget_spent": total_budget_spent,
        "budget_remaining": total_budget_allocated - total_budget_spent,
        "budget_utilization": budget_utilization,
        "completion_rate": completion_rate,
        "status_counts": status_counts,
        "category_distribution": category_distribution,
        "total_indicators": total_indicators,
        "achieved_indicators": achieved_indicators,
        "qa_achievement_rate": qa_achievement_rate,
    }


def export_projects_csv(fiscal_year=None, db_path=None):
    """Export project list to CSV formatted string for SAR and reporting."""
    projects = list_projects(fiscal_year=fiscal_year, db_path=db_path)
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Header
    writer.writerow([
        "รหัสโครงการ",
        "ชื่อโครงการ",
        "หมวด EdPEx / ยุทธศาสตร์",
        "สาขาวิชา/ฝ่ายงาน",
        "ผู้รับผิดชอบ",
        "ปีงบประมาณ",
        "วันที่เริ่มต้น",
        "วันที่สิ้นสุด",
        "งบประมาณจัดสรร (บาท)",
        "งบประมาณเบิกจ่าย (บาท)",
        "งบคงเหลือ (บาท)",
        "สถานะ",
        "วงจร PDCA",
        "วัตถุประสงค์",
        "ผลผลิต (Output)",
        "ผลลัพธ์ (Outcome)",
    ])

    for p in projects:
        budget_allocated = p.get("budget_allocated", 0.0)
        budget_spent = p.get("budget_spent", 0.0)
        remaining = budget_allocated - budget_spent
        writer.writerow([
            p.get("code", ""),
            p.get("title", ""),
            p.get("category", ""),
            p.get("department", ""),
            p.get("leader", ""),
            p.get("fiscal_year", ""),
            p.get("start_date", ""),
            p.get("end_date", ""),
            budget_allocated,
            budget_spent,
            remaining,
            p.get("status", ""),
            p.get("pdca_stage", ""),
            p.get("objective", ""),
            p.get("output", ""),
            p.get("outcome", ""),
        ])

    return output.getvalue()


def seed_faculty_data(db_path=None):
    """Seed standard EdPEx & AUN-QA indicators and sample projects for Faculty of Science and Technology, Hatyai University."""
    init_db(db_path)

    # Standard EdPEx Indicators (7 Categories) and AUN-QA
    sample_indicators = [
        # หมวด 1
        {"code": "EDPEX-1.1", "name": "ร้อยละการบรรลุเป้าหมายตามวิสัยทัศน์และพันธกิจของคณะ", "category": "หมวด 1: การนำองค์กร (Leadership)", "target_value": 85.0, "actual_value": 88.5, "unit": "ร้อยละ", "description": "การสื่อสารและขับเคลื่อนการนำองค์กรสู่ความยั่งยืน"},
        {"code": "EDPEX-1.2", "name": "ระดับความโปร่งใสและธรรมาภิบาลในการบริหารจัดการ", "category": "หมวด 1: การนำองค์กร (Leadership)", "target_value": 90.0, "actual_value": 92.0, "unit": "คะแนน", "description": "ผลการประเมิน ITA ประจำปีของคณะ"},
        # หมวด 2
        {"code": "EDPEX-2.1", "name": "ร้อยละความสำเร็จของแผนปฏิบัติราชการประจำปี", "category": "หมวด 2: กลยุทธ์ (Strategy)", "target_value": 80.0, "actual_value": 82.0, "unit": "ร้อยละ", "description": "การถ่ายทอดยุทธศาสตร์สู่การปฏิบัติ"},
        # หมวด 3
        {"code": "EDPEX-3.1", "name": "ระดับความพึงพอใจของนักศึกษาและผู้มีส่วนได้ส่วนเสีย", "category": "หมวด 3: ลูกค้าและผู้มีส่วนได้ส่วนเสีย (Customers)", "target_value": 4.5, "actual_value": 4.62, "unit": "ระดับ (เต็ม 5)", "description": "การสำรวจความพึงพอใจต่อสิ่งสนับสนุนการเรียนรู้"},
        # หมวด 4
        {"code": "EDPEX-4.1", "name": "จำนวนระบบสารสนเทศเพื่อการตัดสินใจของผู้บริหารที่เปิดใช้งาน", "category": "หมวด 4: การวัด การวิเคราะห์ และการจัดการความรู้ (Measurement & KM)", "target_value": 3.0, "actual_value": 4.0, "unit": "ระบบ", "description": "ระบบฐานข้อมูลและแดชบอร์ดติดตามงาน"},
        # หมวด 5
        {"code": "EDPEX-5.1", "name": "ร้อยละของอาจารย์ที่มีตำแหน่งทางวิชาการ (ผศ./รศ./ศ.)", "category": "หมวด 5: บุคลากร (Workforce)", "target_value": 55.0, "actual_value": 58.0, "unit": "ร้อยละ", "description": "การพัฒนาศักยภาพอาจารย์สายวิชาการ"},
        {"code": "EDPEX-5.2", "name": "ร้อยละของอาจารย์ที่ได้รับรองมาตรฐานวิชาชีพอาจารย์ (PSF/UKPSF)", "category": "หมวด 5: บุคลากร (Workforce)", "target_value": 50.0, "actual_value": 48.0, "unit": "ร้อยละ", "description": "มาตรฐานการจัดการเรียนการสอน"},
        # หมวด 6
        {"code": "EDPEX-6.1", "name": "ร้อยละของกระบวนการบริการการศึกษาที่มีการปรับปรุงสู่ระบบดิจิทัล", "category": "หมวด 6: การปฏิบัติการ (Operations)", "target_value": 80.0, "actual_value": 85.0, "unit": "ร้อยละ", "description": "Digital Transformation ในคณะวิทยาศาสตร์"},
        # หมวด 7
        {"code": "EDPEX-7.1", "name": "ร้อยละของบัณฑิตคณะวิทย์ฯ ที่ได้งานทำหรือประกอบอาชีพอิสระภายใน 1 ปี", "category": "หมวด 7: ผลลัพธ์ (Results)", "target_value": 88.0, "actual_value": 91.2, "unit": "ร้อยละ", "description": "อัตราการมีงานทำของบัณฑิตไอทีและวิทยาศาสตร์"},
        {"code": "EDPEX-7.2", "name": "จำนวนบทความวิจัยที่ได้รับการตีพิมพ์ในระดับนานาชาติ (Scopus/WoS)", "category": "หมวด 7: ผลลัพธ์ (Results)", "target_value": 20.0, "actual_value": 24.0, "unit": "ผลงาน", "description": "ผลผลิตด้านการวิจัยและนวัตกรรม"},
        # AUN-QA
        {"code": "AUN-1.1", "name": "ร้อยละของหลักสูตรที่ผลลัพธ์การเรียนรู้ (PLOs) สอดคล้องกับความต้องการของผู้ใช้บัณฑิต", "category": "AUN-QA: ระดับหลักสูตร (Programme Level)", "target_value": 100.0, "actual_value": 100.0, "unit": "ร้อยละ", "description": "AUN-QA Criterion 1: Expected Learning Outcomes"},
        {"code": "AUN-2.1", "name": "ร้อยละของหลักสูตรที่มีผลการประเมิน AUN-QA ระดับ 4 ขึ้นไป (Adequate as Expected)", "category": "AUN-QA: ระดับหลักสูตร (Programme Level)", "target_value": 80.0, "actual_value": 83.3, "unit": "ร้อยละ", "description": "AUN-QA Assessment Overall Quality"},
    ]

    for ind in sample_indicators:
        try:
            add_qa_indicator(ind, db_path)
        except ValueError:
            pass

    # Sample Projects for Faculty of Science and Technology, Hatyai University
    sample_projects = [
        {
            "code": "PRJ-2567-001",
            "title": "โครงการพัฒนาหลักสูตรวิทยาการคอมพิวเตอร์และเทคโนโลยีดิจิทัลสู่มาตรฐาน AUN-QA",
            "category": "AUN-QA: ระดับหลักสูตร (Programme Level)",
            "department": "สาขาวิทยาการคอมพิวเตอร์และสารสนเทศ",
            "leader": "ผศ.ดร.ประเสริฐ นิลพันธุ์",
            "fiscal_year": 2567,
            "start_date": "2567-01-15",
            "end_date": "2567-09-30",
            "budget_allocated": 120000.0,
            "budget_spent": 95000.0,
            "status": "completed",
            "pdca_stage": "act",
            "objective": "เพื่อปรับปรุงเล่มหลักสูตร มคอ.2 ให้มีผลลัพธ์การเรียนรู้ (PLOs) ชัดเจนและสอดคล้องตามเกณฑ์ AUN-QA v4.0",
            "output": "เล่มหลักสูตรปรับปรุง 2567 และรายงาน SAR หลักสูตร",
            "outcome": "หลักสูตรผ่านการประเมินคุณภาพภายในระดับดีมาก",
            "problems": "การติดตามผลจากผู้ใช้บัณฑิตบางส่วนมีความล่าช้า",
            "solutions": "ใช้แบบสำรวจดิจิทัลออนไลน์ผ่าน LINE OA",
        },
        {
            "code": "PRJ-2567-002",
            "title": "โครงการส่งเสริมการตีพิมพ์ผลงานวิจัยและสร้างนวัตกรรมดิจิทัลเพื่อชุมชนภาคใต้",
            "category": "หมวด 7: ผลลัพธ์ (Results)",
            "department": "ฝ่ายวิจัยและบริการวิชาการ",
            "leader": "ดร.วิภาดา รัตนคีรี",
            "fiscal_year": 2567,
            "start_date": "2567-02-01",
            "end_date": "2567-10-31",
            "budget_allocated": 250000.0,
            "budget_spent": 210000.0,
            "status": "in_progress",
            "pdca_stage": "check",
            "objective": "สนับสนุนทุนและค่าตีพิมพ์วารสาร Scopus/TCI กลุ่ม 1 สำหรับคณาจารย์",
            "output": "บทความวิจัยที่ส่งตีพิมพ์ 12 เรื่อง",
            "outcome": "เพิ่มผลงานวิจัยของคณะในระดับสากล 20%",
            "problems": "ระยะเวลาการ peer-review ของวารสารต่างประเทศใช้เวลานาน",
            "solutions": "จัดกิจกรรม Research Clinic และ Peer Mentoring ภายในคณะ",
        },
        {
            "code": "PRJ-2567-003",
            "title": "โครงการอบรมเพิ่มพูนทักษะปัญญาประดิษฐ์ (Generative AI) แก่บุคลากรและนักศึกษา",
            "category": "หมวด 5: บุคลากร (Workforce)",
            "department": "สาขาเทคโนโลยีสารสนเทศ",
            "leader": "อาจารย์อนุสรณ์ สุวรรณโณ",
            "fiscal_year": 2567,
            "start_date": "2567-03-10",
            "end_date": "2567-07-20",
            "budget_allocated": 60000.0,
            "budget_spent": 58500.0,
            "status": "completed",
            "pdca_stage": "act",
            "objective": "ยกระดับทักษะ AI Literacy และการประยุกต์ใช้ AI ในการทำงานและการจัดการเรียนรู้",
            "output": "อาจารย์และเจ้าหน้าที่ผ่านการอบรม 45 คน",
            "outcome": "ความพึงพอใจเฉลี่ย 4.82/5.0 บุคลากรนำ AI ไปใช้ช่วยลดเวลาทำงานเอกสาร",
            "problems": "ความแตกต่างของพื้นฐานเทคโนโลยีของผู้เข้าร่วมอบรม",
            "solutions": "จัดผู้ช่วยสอน (TA) ประกบดูแลรายบุคคลในการทำ Workshop",
        },
        {
            "code": "PRJ-2567-004",
            "title": "โครงการพัฒนาระบบสารสนเทศประกันคุณภาพและติดตามแผนงานคณะวิทย์ฯ (Smart QA & Project Tracker)",
            "category": "หมวด 4: การวัด การวิเคราะห์ และการจัดการความรู้ (Measurement & KM)",
            "department": "งานบริหารยุทธศาสตร์และประกันคุณภาพ",
            "leader": "ผศ.ดร.สมชาย ธนะโรจน์",
            "fiscal_year": 2567,
            "start_date": "2567-05-01",
            "end_date": "2567-11-30",
            "budget_allocated": 85000.0,
            "budget_spent": 42000.0,
            "status": "in_progress",
            "pdca_stage": "do",
            "objective": "พัฒนาระบบเว็บแอปพลิเคชันสำหรับติดตามแผนยุทธศาสตร์และตัวชี้วัด EdPEx/AUN-QA แบบเรียลไทม์",
            "output": "ระบบ Smart QA Tracker 1 ระบบ พร้อมคู่มือการใช้งาน",
            "outcome": "ลดระยะเวลาในการรวบรวมข้อมูลทำเล่ม SAR ได้มากกว่า 50%",
            "problems": "การเชื่อมต่อกับระบบกลางของมหาวิทยาลัยต้องขอสิทธิ์ API",
            "solutions": "ออกแบบฐานข้อมูลให้สามารถนำเข้าและส่งออกข้อมูลแบบ CSV/Excel ได้โดยตรง",
        },
        {
            "code": "PRJ-2567-005",
            "title": "โครงการสัมมนาจัดทำแผนยุทธศาสตร์คณะวิทยาศาสตร์และเทคโนโลยี ระยะ 5 ปี",
            "category": "หมวด 2: กลยุทธ์ (Strategy)",
            "department": "สำนักงานคณบดี",
            "leader": "คณบดีคณะวิทยาศาสตร์และเทคโนโลยี",
            "fiscal_year": 2567,
            "start_date": "2567-08-01",
            "end_date": "2567-12-15",
            "budget_allocated": 150000.0,
            "budget_spent": 30000.0,
            "status": "in_progress",
            "pdca_stage": "plan",
            "objective": "ทบทวนแผนกลยุทธ์ วิสัยทัศน์ และเป้าหมายตามเกณฑ์ EdPEx หมวด 2",
            "output": "ร่างแผนยุทธศาสตร์คณะ พ.ศ. 2568-2572",
            "outcome": "ทุกสาขาวิชามีทิศทางการพัฒนาสอดคล้องกัน",
            "problems": "-",
            "solutions": "-",
        },
    ]

    project_ids = []
    for proj in sample_projects:
        try:
            pid = add_project(proj, db_path)
            project_ids.append(pid)
        except ValueError:
            pass

    # Link some projects with indicators and add sample evidence links
    if len(project_ids) >= 1:
        # Link PRJ-2567-001 with AUN-1.1
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM qa_indicators WHERE code = 'AUN-1.1'")
        r = cursor.fetchone()
        if r:
            link_project_indicator(project_ids[0], r["id"], "โครงการปรับปรุงเล่มหลักสูตร มคอ.2", db_path)
            add_evidence_link(project_ids[0], "เล่มหลักสูตร มคอ.2 ฉบับปรับปรุง (Google Drive)", "https://drive.google.com/sample/tqf2-curriculum", "link", db_path)
            add_evidence_link(project_ids[0], "รายงานผลการประเมิน AUN-QA 2567 (PDF)", "https://sci.hu.ac.th/qa/reports/aunqa-2567.pdf", "pdf", db_path)

        # Link PRJ-2567-002 with EDPEX-7.2
        cursor.execute("SELECT id FROM qa_indicators WHERE code = 'EDPEX-7.2'")
        r = cursor.fetchone()
        if r and len(project_ids) >= 2:
            link_project_indicator(project_ids[1], r["id"], "ผลผลิตบทความวิจัยระดับ Scopus", db_path)
            add_evidence_link(project_ids[1], "รายชื่อบทความที่ตีพิมพ์ใน Scopus 2024", "https://sci.hu.ac.th/research/publications-2024", "link", db_path)

        conn.close()


if __name__ == "__main__":
    init_db()
    seed_faculty_data()
    print("Database initialized and seeded successfully.")
