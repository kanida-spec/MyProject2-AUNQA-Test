"""
test_app.py - Integration tests for Flask Web Application
Faculty of Science and Technology, Hatyai University.
"""

import pytest
from MyProject2.app import app
from MyProject2.tracker import init_db, seed_faculty_data, get_project


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create Flask test client with a isolated temporary SQLite database."""
    test_db = str(tmp_path / "test_web_tracking.db")
    init_db(test_db)
    seed_faculty_data(test_db)

    # Monkeypatch DEFAULT_DB_PATH in tracker so app uses the test database
    import MyProject2.tracker as tracker
    monkeypatch.setattr(tracker, "DEFAULT_DB_PATH", test_db)

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client, test_db


def test_dashboard_route(client):
    """Test dashboard route returns 200 and displays executive KPI cards."""
    c, _ = client
    response = c.get("/dashboard")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "แดชบอร์ดภาพรวมผู้บริหาร" in html
    assert "HU SciTech" in html
    assert "โครงการทั้งหมดในแผน" in html


def test_projects_list_and_search_route(client):
    """Test project list view and search filter."""
    c, _ = client
    # Normal list
    res = c.get("/projects")
    assert res.status_code == 200
    assert "แผนงานโครงการ" in res.data.decode("utf-8")

    # Filter by search
    res_search = c.get("/projects?search=AUN-QA")
    assert res_search.status_code == 200
    assert "PRJ-2567-001" in res_search.data.decode("utf-8")


def test_project_add_get_and_post(client):
    """Test adding a new project via web form."""
    c, _ = client
    # GET form
    res_get = c.get("/projects/add")
    assert res_get.status_code == 200
    assert "เสนอโครงการใหม่" in res_get.data.decode("utf-8")

    # POST new project
    payload = {
        "code": "PRJ-TEST-WEB-01",
        "title": "โครงการทดสอบระบบเว็บ",
        "category": "หมวด 4: การวัด การวิเคราะห์ และการจัดการความรู้ (Measurement & KM)",
        "department": "ฝ่ายสารสนเทศ",
        "leader": "อาจารย์ผู้ทดสอบ",
        "fiscal_year": "2567",
        "budget_allocated": "50000.0",
        "budget_spent": "20000.0",
        "status": "in_progress",
        "pdca_stage": "do",
        "objective": "เพื่อทดสอบการทำงานของฟอร์ม",
    }
    res_post = c.post("/projects/add", data=payload, follow_redirects=True)
    assert res_post.status_code == 200
    content = res_post.data.decode("utf-8")
    assert "บันทึกข้อมูลโครงการเรียบร้อยแล้ว" in content
    assert "PRJ-TEST-WEB-01" in content


def test_project_detail_and_edit_routes(client):
    """Test viewing and editing project."""
    c, _ = client
    # Detail view
    res = c.get("/projects/1")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "PRJ-2567-001" in html
    assert "PDCA Cycle" in html

    # Edit form GET
    res_edit_get = c.get("/projects/1/edit")
    assert res_edit_get.status_code == 200
    assert "แก้ไขข้อมูลโครงการ" in res_edit_get.data.decode("utf-8")

    # Edit form POST
    update_data = {
        "code": "PRJ-2567-001",
        "title": "โครงการพัฒนาหลักสูตรปรับปรุงใหม่",
        "category": "AUN-QA: ระดับหลักสูตร (Programme Level)",
        "department": "สาขาวิทยาการคอมพิวเตอร์และสารสนเทศ",
        "leader": "ผศ.ดร.ประเสริฐ นิลพันธุ์",
        "fiscal_year": "2567",
        "budget_allocated": "150000.0",
        "budget_spent": "100000.0",
        "status": "completed",
        "pdca_stage": "act",
    }
    res_edit_post = c.post("/projects/1/edit", data=update_data, follow_redirects=True)
    assert res_edit_post.status_code == 200
    assert "ปรับปรุงข้อมูลโครงการเรียบร้อยแล้ว" in res_edit_post.data.decode("utf-8")


def test_project_link_indicator_and_evidence(client):
    """Test linking indicator and adding evidence via web routes."""
    c, _ = client
    # Link indicator
    link_data = {
        "indicator_id": "1",
        "contribution_note": "ตอบโจทย์ตัวชี้วัดหมวด 1",
    }
    res_link = c.post("/projects/2/indicators/link", data=link_data, follow_redirects=True)
    assert res_link.status_code == 200
    assert "เชื่อมโยงตัวชี้วัดประกันคุณภาพสำเร็จ" in res_link.data.decode("utf-8")

    # Add evidence
    evidence_data = {
        "title": "รายงานผลการดำเนินงานประจำปี (PDF)",
        "url": "https://sci.hu.ac.th/report-2567.pdf",
        "doc_type": "pdf",
    }
    res_ev = c.post("/projects/2/evidence/add", data=evidence_data, follow_redirects=True)
    assert res_ev.status_code == 200
    assert "แนบเอกสารหลักฐาน SAR สำเร็จ" in res_ev.data.decode("utf-8")
    assert "รายงานผลการดำเนินงานประจำปี (PDF)" in res_ev.data.decode("utf-8")


def test_indicators_list_and_update(client):
    """Test QA indicators list view and updating actual result."""
    c, _ = client
    # List view
    res = c.get("/indicators")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "ตัวชี้วัดการประกันคุณภาพการศึกษา" in html
    assert "EDPEX-1.1" in html

    # Update actual value
    res_upd = c.post("/indicators/update-result", data={"indicator_id": "1", "actual_value": "95.5"}, follow_redirects=True)
    assert res_upd.status_code == 200
    assert "บันทึกผลการดำเนินงานจริงเรียบร้อยแล้ว" in res_upd.data.decode("utf-8")


def test_export_csv_route(client):
    """Test CSV export route returns valid CSV with UTF-8 BOM."""
    c, _ = client
    res = c.get("/export")
    assert res.status_code == 200
    assert res.mimetype == "text/csv"
    assert "attachment; filename=" in res.headers.get("Content-Disposition", "")
    content = res.data.decode("utf-8")
    assert content.startswith("\ufeff")  # BOM
    assert "รหัสโครงการ" in content
    assert "PRJ-2567-001" in content
