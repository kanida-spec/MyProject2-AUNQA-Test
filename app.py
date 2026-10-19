"""
app.py - Web Application for Faculty of Science and Technology, Hatyai University
Quality Assurance (EdPEx & AUN-QA) and Strategic Project Tracking System.
"""

import os
import sys
from pathlib import Path

# Ensure both project root and MyProject2 folder are in sys.path
_current_dir = Path(__file__).resolve().parent
_root_dir = _current_dir.parent
for _p in (str(_root_dir), str(_current_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
)

try:
    from MyProject2.tracker import (
        DEFAULT_DB_PATH,
        EDPEX_CATEGORIES,
        init_db,
        seed_faculty_data,
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
    )
except ImportError:
    from tracker import (
        DEFAULT_DB_PATH,
        EDPEX_CATEGORIES,
        init_db,
        seed_faculty_data,
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
    )

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "hatyai-u-sci-tech-secret-key-2567")

# Ensure DB initialized on module load
if not os.path.exists(DEFAULT_DB_PATH):
    init_db(DEFAULT_DB_PATH)
    seed_faculty_data(DEFAULT_DB_PATH)


@app.route("/")
@app.route("/dashboard")
def dashboard():
    """Executive Dashboard view."""
    year_param = request.args.get("fiscal_year", "")
    selected_year = int(year_param) if year_param.isdigit() else None

    summary = get_dashboard_summary(fiscal_year=selected_year)
    recent_projects = list_projects(fiscal_year=selected_year)[:6]

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        summary=summary,
        recent_projects=recent_projects,
        selected_year=selected_year,
    )


@app.route("/projects")
def projects_list():
    """List and filter strategic projects."""
    category = request.args.get("category", "").strip() or None
    status = request.args.get("status", "").strip() or None
    search = request.args.get("search", "").strip() or None
    year_param = request.args.get("fiscal_year", "").strip()
    selected_year = int(year_param) if year_param.isdigit() else None

    projects = list_projects(
        category=category,
        status=status,
        fiscal_year=selected_year,
        search=search,
    )

    return render_template(
        "projects.html",
        active_page="projects",
        projects=projects,
        categories=EDPEX_CATEGORIES,
        selected_category=category,
        selected_status=status,
        selected_year=selected_year,
        search_query=search,
    )


@app.route("/projects/add", methods=["GET", "POST"])
def project_add():
    """Add new project form and action."""
    if request.method == "POST":
        try:
            pid = add_project(request.form)
            flash("บันทึกข้อมูลโครงการเรียบร้อยแล้ว", "success")
            return redirect(url_for("project_detail", project_id=pid))
        except ValueError as e:
            flash(f"เกิดข้อผิดพลาด: {str(e)}", "error")
            return render_template(
                "project_form.html",
                active_page="projects",
                project=request.form,
                categories=EDPEX_CATEGORIES,
            )

    return render_template(
        "project_form.html",
        active_page="projects",
        project=None,
        categories=EDPEX_CATEGORIES,
    )


@app.route("/projects/<int:project_id>")
def project_detail(project_id):
    """View detailed project with PDCA stepper, QA indicators and evidence."""
    project = get_project(project_id)
    if not project:
        flash("ไม่พบข้อมูลโครงการที่ระบุ", "error")
        return redirect(url_for("projects_list"))

    all_indicators = list_qa_indicators()
    return render_template(
        "project_detail.html",
        active_page="projects",
        project=project,
        all_indicators=all_indicators,
    )


@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
def project_edit(project_id):
    """Edit existing project."""
    project = get_project(project_id)
    if not project:
        flash("ไม่พบข้อมูลโครงการที่ระบุ", "error")
        return redirect(url_for("projects_list"))

    if request.method == "POST":
        try:
            update_project(project_id, request.form)
            flash("ปรับปรุงข้อมูลโครงการเรียบร้อยแล้ว", "success")
            return redirect(url_for("project_detail", project_id=project_id))
        except ValueError as e:
            flash(f"เกิดข้อผิดพลาด: {str(e)}", "error")
            return render_template(
                "project_form.html",
                active_page="projects",
                project=dict(request.form, id=project_id),
                categories=EDPEX_CATEGORIES,
            )

    return render_template(
        "project_form.html",
        active_page="projects",
        project=project,
        categories=EDPEX_CATEGORIES,
    )


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
def project_delete(project_id):
    """Delete project."""
    deleted = delete_project(project_id)
    if deleted:
        flash("ลบโครงการเรียบร้อยแล้ว", "success")
    else:
        flash("ไม่สามารถลบโครงการได้ หรือไม่พบโครงการ", "error")
    return redirect(url_for("projects_list"))


@app.route("/projects/<int:project_id>/indicators/link", methods=["POST"])
def project_link_indicator(project_id):
    """Link project to a QA indicator."""
    indicator_id = request.form.get("indicator_id")
    note = request.form.get("contribution_note", "").strip()
    if indicator_id:
        link_project_indicator(project_id, int(indicator_id), note)
        flash("เชื่อมโยงตัวชี้วัดประกันคุณภาพสำเร็จ", "success")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/indicators/<int:indicator_id>/unlink", methods=["POST"])
def project_unlink_indicator(project_id, indicator_id):
    """Unlink QA indicator from project."""
    unlink_project_indicator(project_id, indicator_id)
    flash("ยกเลิกการเชื่อมโยงตัวชี้วัดสำเร็จ", "success")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/evidence/add", methods=["POST"])
def add_evidence(project_id):
    """Add evidence link to project."""
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()
    doc_type = request.form.get("doc_type", "link").strip()
    try:
        add_evidence_link(project_id, title, url, doc_type)
        flash("แนบเอกสารหลักฐาน SAR สำเร็จ", "success")
    except ValueError as e:
        flash(f"ไม่สามารถแนบหลักฐานได้: {str(e)}", "error")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/evidence/<int:evidence_id>/delete", methods=["POST"])
def delete_evidence(project_id, evidence_id):
    """Delete an evidence link."""
    delete_evidence_link(evidence_id)
    flash("ลบเอกสารหลักฐานสำเร็จ", "success")
    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/indicators")
def indicators_list():
    """List QA indicators (EdPEx & AUN-QA)."""
    category = request.args.get("category", "").strip() or None
    indicators = list_qa_indicators(category=category)
    return render_template(
        "indicators.html",
        active_page="indicators",
        indicators=indicators,
        categories=EDPEX_CATEGORIES,
        selected_category=category,
    )


@app.route("/indicators/add", methods=["POST"])
def indicator_add():
    """Add a new QA indicator."""
    try:
        add_qa_indicator(request.form)
        flash("เพิ่มตัวชี้วัดประกันคุณภาพเรียบร้อยแล้ว", "success")
    except ValueError as e:
        flash(f"เกิดข้อผิดพลาด: {str(e)}", "error")
    return redirect(url_for("indicators_list"))


@app.route("/indicators/update-result", methods=["POST"])
def update_indicator_result():
    """Update actual achieved value of an indicator."""
    indicator_id = request.form.get("indicator_id")
    actual_val = request.form.get("actual_value", 0.0)
    if indicator_id:
        update_qa_indicator_result(int(indicator_id), float(actual_val))
        flash("บันทึกผลการดำเนินงานจริงเรียบร้อยแล้ว", "success")
    return redirect(url_for("indicators_list"))


@app.route("/export")
def export_csv():
    """Export project report in CSV format."""
    year_param = request.args.get("fiscal_year", "").strip()
    selected_year = int(year_param) if year_param.isdigit() else None
    csv_data = export_projects_csv(fiscal_year=selected_year)

    # Add UTF-8 BOM so Thai characters open cleanly in Microsoft Excel
    bom_csv = "\ufeff" + csv_data
    filename = f"HU_SciTech_Projects_{selected_year or 'All'}.csv"

    return Response(
        bom_csv,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/seed", methods=["POST"])
def seed_data():
    """Seed sample data for faculty demonstration."""
    seed_faculty_data()
    flash("โหลดชุดข้อมูลตัวอย่างของคณะวิทยาศาสตร์และเทคโนโลยีเรียบร้อยแล้ว", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
