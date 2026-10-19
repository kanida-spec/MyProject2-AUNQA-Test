# plan.md — แผนการพัฒนาระบบประกันคุณภาพและติดตามโครงการ
คณะวิทยาศาสตร์และเทคโนโลยี มหาวิทยาลัยหาดใหญ่

อ้างอิงข้อกำหนดใน spec.md และปฏิบัติตาม AGENT.md

---

## [x] Task 1: พัฒนาระบบฐานข้อมูลและตรรกะหลัก (Core Logic & Database in tracker.py)
- [x] ออกแบบตาราง SQLite พร้อม Parameterized Query: `projects`, `qa_indicators`, `project_indicators`, `evidence_links`
- [x] ฟังก์ชัน CRUD โครงการ: `add_project()`, `update_project()`, `delete_project()`, `get_project()`, `list_projects()`
- [x] ฟังก์ชันตัวชี้วัด QA: `add_qa_indicator()`, `list_qa_indicators()`, `link_project_indicator()`
- [x] ระบบจัดเก็บเอกสารหลักฐาน: `add_evidence_link()`, `delete_evidence_link()`
- [x] ฟังก์ชันคำนวณ Dashboard: `get_dashboard_summary()` (ยอดโครงการ, งบประมาณ, ร้อยละการเบิกจ่าย, อัตราความสำเร็จ)
- [x] ฟังก์ชันส่งออกรายงาน: `export_projects_csv()`

---

## [x] Task 2: พัฒนาชุดทดสอบอัตโนมัติ (Automated Tests in test_tracker.py)
- [x] ทดสอบการเพิ่มโครงการและ Input Validation (ป้องกันรหัสซ้ำ, งบประมาณติดลบ, งบใช้จริงเกินงบจัดสรร)
- [x] ทดสอบคำนวณงบประมาณและสถิติภาพรวมใน Dashboard
- [x] ทดสอบการเชื่อมโยงโครงการกับตัวชี้วัดประกันคุณภาพ (EdPEx 7 หมวด / AUN-QA)
- [x] ทดสอบค้นหา กรอง และส่งออก CSV
- [x] รัน pytest ผ่านครบ 10/10 รายการ (100%)

---

## [x] Task 3: พัฒนาระบบเว็บแอปพลิเคชัน (Web Application in app.py + UI)
- [x] สร้าง Flask Application (`app.py`) พร้อม Routing ครบวงจร
- [x] ออกแบบหน้า Executive Dashboard (`templates/dashboard.html`) พร้อมการ์ดสรุป KPI, แถบสัดส่วนงบประมาณ, และกราฟสถานะ
- [x] หน้ารายการโครงการและระบบค้นหา/ตัวกรอง (`templates/projects.html`)
- [x] หน้าดูรายละเอียดโครงการรายบุคคลพร้อม PDCA Cycle Stepper (`templates/project_detail.html`)
- [x] หน้าฟอร์มบันทึก/แก้ไขโครงการ (`templates/project_form.html`)
- [x] หน้าจัดการตัวชี้วัด EdPEx และ AUN-QA (`templates/indicators.html`)
- [x] ระบบส่งออกข้อมูล CSV สำหรับทำเล่ม SAR (`/export`)
- [x] พัฒนาชุดทดสอบ Integration Test ครอบคลุมทุก Route ใน `test_app.py` (ผ่านครบ 7/7 รายการ)

---

## [x] Task 4: ชุดข้อมูลตัวอย่างคณะวิทยาศาสตร์และเทคโนโลยี (Seed Data)
- [x] เตรียมข้อมูลตัวชี้วัด EdPEx 7 หมวด และ AUN-QA พร้อมค่าเป้าหมายและผลงาน
- [x] เตรียมข้อมูลโครงการจริงจำลอง เช่น การพัฒนาหลักสูตร AUN-QA, ทุนวิจัย Scopus, อบรม Generative AI, สัมมนาแผนกลยุทธ์
- [x] ระบบ Seed อัตโนมัติเมื่อเริ่มใช้งานครั้งแรก หรือผ่านปุ่มบนหน้าแดชบอร์ด

---

## วิธีการรันระบบ
1. **รันการทดสอบทั้งหมด (Pytest)**:
   ```powershell
   python -m pytest MyProject2/test_tracker.py MyProject2/test_app.py -v
   ```
2. **เปิดใช้งานระบบเว็บแอปพลิเคชัน**:
   ```powershell
   python MyProject2/app.py
   ```
   หรือ
   ```powershell
   flask --app MyProject2/app.py run --debug
   ```
   เปิดเว็บเบราว์เซอร์ไปที่: `http://127.0.0.1:5000`
