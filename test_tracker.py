"""
test_tracker.py - Automated tests for Quality Assurance (EdPEx & AUN-QA)
and Strategic Project Tracking System.
Faculty of Science and Technology, Hatyai University.
"""

import os
import pytest
from MyProject2.tracker import (
    init_db,
    add_project,
    update_project,
    delete_project,
    get_project,
    list_projects,
    add_qa_indicator,
    list_qa_indicators,
    update_qa_indicator_result,
    link_project_indicator,
    unlink_project_indicator,
    add_evidence_link,
    delete_evidence_link,
    get_dashboard_summary,
    export_projects_csv,
    seed_faculty_data,
)


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing a temporary SQLite database path."""
    db_file = str(tmp_path / "test_tracking.db")
    init_db(db_file)
    return db_file


def test_add_project_success(temp_db):
    """AC-1: Adding a valid project succeeds and returns project ID."""
    payload = {
        "code": "PRJ-01",
        "title": "โครงการพัฒนาห้องปฏิบัติการ AI",
        "category": "หมวด 6: การปฏิบัติการ (Operations)",
        "department": "สาขาวิทยาการคอมพิวเตอร์",
        "leader": "ดร.สมชาย ใจดี",
        "fiscal_year": 2567,
        "budget_allocated": 100000.0,
        "budget_spent": 40000.0,
        "status": "in_progress",
        "pdca_stage": "do",
    }
    pid = add_project(payload, db_path=temp_db)
    assert pid > 0

    project = get_project(pid, db_path=temp_db)
    assert project is not None
    assert project["code"] == "PRJ-01"
    assert project["title"] == "โครงการพัฒนาห้องปฏิบัติการ AI"
    assert project["budget_allocated"] == 100000.0
    assert project["budget_spent"] == 40000.0
    assert project["status"] == "in_progress"
    assert project["pdca_stage"] == "do"


def test_add_project_duplicate_code_fails(temp_db):
    """AC-2: Adding project with duplicate code raises ValueError."""
    payload = {
        "code": "PRJ-DUP",
        "title": "โครงการ A",
        "category": "หมวด 1: การนำองค์กร (Leadership)",
        "department": "วิทยาการคอมพิวเตอร์",
        "leader": "อาจารย์ ก",
        "fiscal_year": 2567,
        "budget_allocated": 50000.0,
    }
    add_project(payload, db_path=temp_db)

    with pytest.raises(ValueError, match="already exists"):
        add_project(payload, db_path=temp_db)


def test_add_project_invalid_inputs(temp_db):
    """AC-3: Invalid inputs raise ValueError."""
    base = {
        "code": "PRJ-INV",
        "title": "โครงการทดสอบ",
        "category": "หมวด 1: การนำองค์กร (Leadership)",
        "department": "ฝ่ายวิชาการ",
        "leader": "อาจารย์ ข",
        "fiscal_year": 2567,
        "budget_allocated": 10000.0,
        "budget_spent": 5000.0,
        "status": "in_progress",
        "pdca_stage": "plan",
    }

    # Empty code
    bad = base.copy()
    bad["code"] = "   "
    with pytest.raises(ValueError):
        add_project(bad, db_path=temp_db)

    # Empty title
    bad = base.copy()
    bad["title"] = ""
    with pytest.raises(ValueError):
        add_project(bad, db_path=temp_db)

    # Empty leader
    bad = base.copy()
    bad["leader"] = ""
    with pytest.raises(ValueError):
        add_project(bad, db_path=temp_db)

    # Budget spent > budget allocated
    bad = base.copy()
    bad["budget_allocated"] = 10000.0
    bad["budget_spent"] = 20000.0
    with pytest.raises(ValueError, match="exceed allocated budget"):
        add_project(bad, db_path=temp_db)

    # Negative budget
    bad = base.copy()
    bad["budget_allocated"] = -500.0
    with pytest.raises(ValueError):
        add_project(bad, db_path=temp_db)

    # Invalid status
    bad = base.copy()
    bad["status"] = "cancelled_unsupported"
    with pytest.raises(ValueError, match="Invalid status"):
        add_project(bad, db_path=temp_db)

    # Invalid PDCA stage
    bad = base.copy()
    bad["pdca_stage"] = "invalid_stage"
    with pytest.raises(ValueError, match="Invalid PDCA stage"):
        add_project(bad, db_path=temp_db)


def test_update_project(temp_db):
    """AC-4: Updating project modifies fields successfully."""
    pid = add_project(
        {
            "code": "PRJ-UPD",
            "title": "ชื่อเดิม",
            "category": "หมวด 2: กลยุทธ์ (Strategy)",
            "department": "สาขาไอที",
            "leader": "ผู้รับผิดชอบเดิม",
            "fiscal_year": 2567,
            "budget_allocated": 50000.0,
            "budget_spent": 10000.0,
            "status": "not_started",
            "pdca_stage": "plan",
        },
        db_path=temp_db,
    )

    update_payload = {
        "code": "PRJ-UPD",
        "title": "ชื่อที่แก้ไขใหม่",
        "category": "หมวด 2: กลยุทธ์ (Strategy)",
        "department": "สาขาไอที",
        "leader": "ผู้รับผิดชอบใหม่",
        "fiscal_year": 2567,
        "budget_allocated": 60000.0,
        "budget_spent": 35000.0,
        "status": "completed",
        "pdca_stage": "act",
    }
    updated = update_project(pid, update_payload, db_path=temp_db)
    assert updated is True

    project = get_project(pid, db_path=temp_db)
    assert project["title"] == "ชื่อที่แก้ไขใหม่"
    assert project["leader"] == "ผู้รับผิดชอบใหม่"
    assert project["budget_allocated"] == 60000.0
    assert project["budget_spent"] == 35000.0
    assert project["status"] == "completed"
    assert project["pdca_stage"] == "act"


def test_delete_project(temp_db):
    """AC-5: Deleting project removes project and linked relations."""
    pid = add_project(
        {
            "code": "PRJ-DEL",
            "title": "โครงการที่จะลบ",
            "category": "หมวด 3: ลูกค้าและผู้มีส่วนได้ส่วนเสีย (Customers)",
            "department": "สำนักงานคณบดี",
            "leader": "เจ้าหน้าที่ทดสอบ",
            "fiscal_year": 2567,
        },
        db_path=temp_db,
    )
    assert get_project(pid, db_path=temp_db) is not None

    deleted = delete_project(pid, db_path=temp_db)
    assert deleted is True
    assert get_project(pid, db_path=temp_db) is None


def test_qa_indicators_and_linkage(temp_db):
    """AC-6: Add QA indicators, link to project, and update results."""
    ind_id = add_qa_indicator(
        {
            "code": "EDPEX-TEST-1",
            "name": "ร้อยละความสำเร็จตามแผน",
            "category": "หมวด 2: กลยุทธ์ (Strategy)",
            "target_value": 80.0,
            "actual_value": 75.0,
            "unit": "ร้อยละ",
            "description": "ทดสอบตัวชี้วัด",
        },
        db_path=temp_db,
    )
    assert ind_id > 0

    # Duplicate code check
    with pytest.raises(ValueError, match="already exists"):
        add_qa_indicator(
            {
                "code": "EDPEX-TEST-1",
                "name": "ซ้ำ",
                "category": "หมวด 2: กลยุทธ์ (Strategy)",
                "target_value": 10.0,
                "unit": "ข้อ",
            },
            db_path=temp_db,
        )

    # Link with project
    pid = add_project(
        {
            "code": "PRJ-LINK",
            "title": "โครงการเชื่อมโยงตัวชี้วัด",
            "category": "หมวด 2: กลยุทธ์ (Strategy)",
            "department": "สาขาเทคโนโลยีสารสนเทศ",
            "leader": "อาจารย์ทดสอบ",
            "fiscal_year": 2567,
        },
        db_path=temp_db,
    )
    link_project_indicator(pid, ind_id, "ส่งผลต่อตัวชี้วัด 80%", db_path=temp_db)

    project = get_project(pid, db_path=temp_db)
    assert len(project["indicators"]) == 1
    assert project["indicators"][0]["code"] == "EDPEX-TEST-1"
    assert project["indicators"][0]["contribution_note"] == "ส่งผลต่อตัวชี้วัด 80%"

    # Update actual value
    update_qa_indicator_result(ind_id, 85.0, db_path=temp_db)
    indicators = list_qa_indicators(category="หมวด 2: กลยุทธ์ (Strategy)", db_path=temp_db)
    assert len(indicators) == 1
    assert indicators[0]["actual_value"] == 85.0

    # Unlink
    unlink_project_indicator(pid, ind_id, db_path=temp_db)
    project_unlinked = get_project(pid, db_path=temp_db)
    assert len(project_unlinked["indicators"]) == 0


def test_evidence_links(temp_db):
    """AC-7: Evidence links can be added, queried and deleted."""
    pid = add_project(
        {
            "code": "PRJ-EVID",
            "title": "โครงการทดสอบหลักฐาน",
            "category": "AUN-QA: ระดับหลักสูตร (Programme Level)",
            "department": "สาขาวิทยาการคอมพิวเตอร์",
            "leader": "หัวหน้าหลักสูตร",
            "fiscal_year": 2567,
        },
        db_path=temp_db,
    )

    eid = add_evidence_link(
        pid,
        title="เล่ม SAR หลักสูตร วท.บ.",
        url="https://sci.hu.ac.th/sar2567.pdf",
        doc_type="pdf",
        db_path=temp_db,
    )
    assert eid > 0

    project = get_project(pid, db_path=temp_db)
    assert len(project["evidence"]) == 1
    assert project["evidence"][0]["title"] == "เล่ม SAR หลักสูตร วท.บ."
    assert project["evidence"][0]["url"] == "https://sci.hu.ac.th/sar2567.pdf"

    # Empty url or title raises ValueError
    with pytest.raises(ValueError):
        add_evidence_link(pid, "", "https://example.com", db_path=temp_db)

    with pytest.raises(ValueError):
        add_evidence_link(pid, "หลักฐาน", "   ", db_path=temp_db)

    # Delete evidence
    deleted = delete_evidence_link(eid, db_path=temp_db)
    assert deleted is True
    project_after = get_project(pid, db_path=temp_db)
    assert len(project_after["evidence"]) == 0


def test_dashboard_summary(temp_db):
    """AC-8: Executive dashboard aggregates metrics accurately."""
    add_project(
        {
            "code": "PRJ-SUM-1",
            "title": "โครงการ 1",
            "category": "หมวด 1: การนำองค์กร (Leadership)",
            "department": "คณะวิทย์",
            "leader": "อาจารย์ 1",
            "fiscal_year": 2567,
            "budget_allocated": 100000.0,
            "budget_spent": 80000.0,
            "status": "completed",
        },
        db_path=temp_db,
    )
    add_project(
        {
            "code": "PRJ-SUM-2",
            "title": "โครงการ 2",
            "category": "หมวด 5: บุคลากร (Workforce)",
            "department": "คณะวิทย์",
            "leader": "อาจารย์ 2",
            "fiscal_year": 2567,
            "budget_allocated": 50000.0,
            "budget_spent": 20000.0,
            "status": "in_progress",
        },
        db_path=temp_db,
    )
    add_qa_indicator(
        {
            "code": "IND-1",
            "name": "ตัวชี้วัด 1",
            "category": "หมวด 1: การนำองค์กร (Leadership)",
            "target_value": 80.0,
            "actual_value": 90.0,
            "unit": "%",
        },
        db_path=temp_db,
    )

    summary = get_dashboard_summary(fiscal_year=2567, db_path=temp_db)
    assert summary["total_projects"] == 2
    assert summary["total_budget_allocated"] == 150000.0
    assert summary["total_budget_spent"] == 100000.0
    assert summary["budget_remaining"] == 50000.0
    assert summary["budget_utilization"] == 66.7
    assert summary["completion_rate"] == 50.0
    assert summary["status_counts"]["completed"] == 1
    assert summary["status_counts"]["in_progress"] == 1
    assert summary["total_indicators"] == 1
    assert summary["achieved_indicators"] == 1
    assert summary["qa_achievement_rate"] == 100.0


def test_search_filter_and_export_csv(temp_db):
    """AC-9: Search, filter, and export CSV work accurately."""
    add_project(
        {
            "code": "PRJ-AI-01",
            "title": "นวัตกรรม AI คณะวิทย์",
            "category": "หมวด 6: การปฏิบัติการ (Operations)",
            "department": "สาขาวิทยาการคอมพิวเตอร์",
            "leader": "ดร.วิจัย เก่งมาก",
            "fiscal_year": 2567,
            "budget_allocated": 30000.0,
            "budget_spent": 15000.0,
            "status": "in_progress",
        },
        db_path=temp_db,
    )

    # Search by keyword
    results = list_projects(search="นวัตกรรม", db_path=temp_db)
    assert len(results) == 1
    assert results[0]["code"] == "PRJ-AI-01"

    # Search non-matching
    no_results = list_projects(search="ไม่มีคำนี้", db_path=temp_db)
    assert len(no_results) == 0

    # Filter by category
    cat_results = list_projects(category="หมวด 6: การปฏิบัติการ (Operations)", db_path=temp_db)
    assert len(cat_results) == 1

    # Filter by different category
    other_cat = list_projects(category="หมวด 1: การนำองค์กร (Leadership)", db_path=temp_db)
    assert len(other_cat) == 0

    # CSV Export
    csv_text = export_projects_csv(fiscal_year=2567, db_path=temp_db)
    assert "รหัสโครงการ" in csv_text
    assert "PRJ-AI-01" in csv_text
    assert "นวัตกรรม AI คณะวิทย์" in csv_text


def test_seed_faculty_data(temp_db):
    """AC-10: Seeding standard faculty data populates indicators and realistic projects."""
    seed_faculty_data(db_path=temp_db)
    indicators = list_qa_indicators(db_path=temp_db)
    assert len(indicators) >= 10

    projects = list_projects(db_path=temp_db)
    assert len(projects) >= 5

    # Check that some project has linked indicator and evidence
    prj1 = get_project(projects[0]["id"], db_path=temp_db)
    assert len(prj1["indicators"]) >= 1
    assert len(prj1["evidence"]) >= 1
