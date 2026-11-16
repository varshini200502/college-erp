"""
Pure-Python PDF 1.4 Generator for College ERP Fee Receipts.
Generates ISO 32000-1 / PDF 1.4 compliant binary PDF files without external library dependencies.
"""
import io
from datetime import datetime


class SimplePDF:
    def __init__(self, title="Fee Receipt"):
        self.title = title
        self.objects = []
        self.page_object_ids = []
        self.pages_catalog_id = 0
        self.current_page_stream = []

    def _add_object(self, content):
        self.objects.append(content)
        return len(self.objects)  # 1-based object number

    def escape_text(self, text):
        if not text:
            return ""
        # PDF string literal escape
        return str(text).replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    def build_receipt(self, receipt_data):
        """
        Build a high-quality, professional College ERP payment receipt.
        receipt_data: dictionary of student, payment, and college details.
        """
        college_name = receipt_data.get('college_name', 'SHRI INDIRA GANDHI COLLEGE OF ENGINEERING')
        college_sub = receipt_data.get('college_sub', 'Approved by AICTE | Affiliated to Mumbai University | NAAC Accredited')
        college_address = receipt_data.get('college_address', 'Sector 8, Ghansoli, Navi Mumbai, Maharashtra - 400701')
        
        receipt_no = receipt_data.get('receipt_no', 'REC-000000')
        payment_date = receipt_data.get('payment_date', str(datetime.now().strftime('%d-%b-%Y')))
        payment_mode = receipt_data.get('payment_mode', 'Online')
        txn_ref = receipt_data.get('txn_ref', 'N/A')
        status = receipt_data.get('status', 'CONFIRMED')

        student_name = receipt_data.get('student_name', 'Student Name')
        student_id = receipt_data.get('student_id', 'N/A')
        roll_no = receipt_data.get('roll_no', 'N/A')
        department = receipt_data.get('department', 'Engineering')
        academic_year = receipt_data.get('academic_year', '2024-2025')
        semester = receipt_data.get('semester', 'N/A')
        section = receipt_data.get('section', 'A')

        fee_structure_name = receipt_data.get('fee_structure_name', 'Tuition & Academic Fees')
        amount_paid = float(receipt_data.get('amount_paid', 0.0))
        net_fee = float(receipt_data.get('net_fee', 0.0))
        total_paid = float(receipt_data.get('total_paid', 0.0))
        due_amount = float(receipt_data.get('due_amount', 0.0))
        recorded_by = receipt_data.get('recorded_by', 'Finance Office')

        # PDF Dimensions: Letter size 612 x 792 pt
        stream = []
        
        # Background / Borders
        # Outer double border (Navy)
        stream.append("0.05 0.20 0.45 RG") # Stroke color
        stream.append("2 w") # Line width
        stream.append("25 25 562 742 re S")
        stream.append("0.5 w")
        stream.append("28 28 556 736 re S")

        # Header Box (Dark Blue gradient-like header banner)
        stream.append("0.05 0.22 0.50 rg") # Fill color
        stream.append("30 685 552 75 re f")

        # College Header Text
        stream.append("BT")
        stream.append("/F2 16 Tf")
        stream.append("1 1 1 rg") # White text
        stream.append(f"1 0 0 1 50 735 Tm ({self.escape_text(college_name)}) Tj")
        stream.append("/F1 9 Tf")
        stream.append(f"1 0 0 1 95 718 Tm ({self.escape_text(college_sub)}) Tj")
        stream.append(f"1 0 0 1 120 703 Tm ({self.escape_text(college_address)}) Tj")
        stream.append("ET")

        # Receipt Title Badge
        stream.append("0.90 0.94 1.00 rg")
        stream.append("180 650 252 24 re f")
        stream.append("0.05 0.22 0.50 RG")
        stream.append("1 w")
        stream.append("180 650 252 24 re S")

        stream.append("BT")
        stream.append("/F2 12 Tf")
        stream.append("0.05 0.22 0.50 rg")
        stream.append("1 0 0 1 205 658 Tm (OFFICIAL FEE PAYMENT RECEIPT) Tj")
        stream.append("ET")

        # Meta Info Table (Receipt No, Date, Status, Mode)
        # Top Row Box
        stream.append("0.96 0.97 0.99 rg")
        stream.append("40 595 532 45 re f")
        stream.append("0.8 0.85 0.9 RG")
        stream.append("0.5 w")
        stream.append("40 595 532 45 re S")

        stream.append("BT")
        stream.append("/F2 10 Tf")
        stream.append("0.1 0.1 0.1 rg")
        stream.append(f"1 0 0 1 50 625 Tm (Receipt Number:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 150 625 Tm ({self.escape_text(receipt_no)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append(f"1 0 0 1 340 625 Tm (Payment Date:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 430 625 Tm ({self.escape_text(payment_date)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append(f"1 0 0 1 50 605 Tm (Payment Mode:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 150 605 Tm ({self.escape_text(payment_mode)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append(f"1 0 0 1 340 605 Tm (Txn Reference:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 430 605 Tm ({self.escape_text(txn_ref)}) Tj")
        stream.append("ET")

        # Student Information Box
        stream.append("0.05 0.22 0.50 rg")
        stream.append("40 565 532 20 re f")
        stream.append("BT")
        stream.append("/F2 10 Tf")
        stream.append("1 1 1 rg")
        stream.append("1 0 0 1 50 571 Tm (STUDENT DETAILS) Tj")
        stream.append("ET")

        stream.append("0.98 0.98 1.0 rg")
        stream.append("40 480 532 85 re f")
        stream.append("0.8 0.85 0.9 RG")
        stream.append("40 480 532 85 re S")

        stream.append("BT")
        stream.append("/F2 10 Tf")
        stream.append("0.2 0.2 0.2 rg")
        stream.append("1 0 0 1 50 545 Tm (Student Name:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 150 545 Tm ({self.escape_text(student_name)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("1 0 0 1 340 545 Tm (Roll Number:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 430 545 Tm ({self.escape_text(roll_no)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("1 0 0 1 50 525 Tm (Department / Course:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 150 525 Tm ({self.escape_text(department)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("1 0 0 1 340 525 Tm (Student ID:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 430 525 Tm ({self.escape_text(student_id)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("1 0 0 1 50 505 Tm (Academic Year:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 150 505 Tm ({self.escape_text(academic_year)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("1 0 0 1 340 505 Tm (Semester / Section:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 430 505 Tm (Sem {self.escape_text(semester)} / Sec {self.escape_text(section)}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("1 0 0 1 50 488 Tm (Payment Status:) Tj")
        stream.append("/F2 10 Tf")
        if status == 'REFUNDED':
            stream.append("0.8 0.1 0.1 rg")
            stream.append(f"1 0 0 1 150 488 Tm (REFUNDED) Tj")
        else:
            stream.append("0.1 0.6 0.2 rg")
            stream.append(f"1 0 0 1 150 488 Tm (CONFIRMED / PAID) Tj")
        stream.append("ET")

        # Fee Details & Ledger Table
        stream.append("0.05 0.22 0.50 rg")
        stream.append("40 445 532 20 re f")
        stream.append("BT")
        stream.append("/F2 10 Tf")
        stream.append("1 1 1 rg")
        stream.append("1 0 0 1 50 451 Tm (FEE BREAKDOWN & PAYMENT SUMMARY) Tj")
        stream.append("ET")

        # Table Header
        stream.append("0.90 0.92 0.96 rg")
        stream.append("40 420 532 25 re f")
        stream.append("0.7 0.75 0.8 RG")
        stream.append("40 420 532 25 re S")

        stream.append("BT")
        stream.append("/F2 10 Tf")
        stream.append("0.1 0.1 0.1 rg")
        stream.append("1 0 0 1 50 428 Tm (Particulars / Description) Tj")
        stream.append("1 0 0 1 460 428 Tm (Amount (INR)) Tj")
        stream.append("ET")

        # Table Row 1
        stream.append("1 1 1 rg")
        stream.append("40 385 532 35 re f")
        stream.append("0.8 0.8 0.8 RG")
        stream.append("40 385 532 35 re S")

        stream.append("BT")
        stream.append("/F1 10 Tf")
        stream.append("0.1 0.1 0.1 rg")
        stream.append(f"1 0 0 1 50 405 Tm ({self.escape_text(fee_structure_name)}) Tj")
        stream.append("/F1 8 Tf")
        stream.append("0.4 0.4 0.4 rg")
        stream.append(f"1 0 0 1 50 392 Tm (Tuition, Development, Laboratory, Library & Assessment Charges) Tj")
        stream.append("/F2 11 Tf")
        stream.append("0.05 0.2 0.5 rg")
        stream.append(f"1 0 0 1 460 400 Tm (Rs. {amount_paid:,.2f}) Tj")
        stream.append("ET")

        # Summary Totals Box
        stream.append("0.96 0.97 0.99 rg")
        stream.append("40 280 532 95 re f")
        stream.append("0.7 0.75 0.8 RG")
        stream.append("40 280 532 95 re S")

        stream.append("BT")
        stream.append("/F2 10 Tf")
        stream.append("0.2 0.2 0.2 rg")
        stream.append("1 0 0 1 50 355 Tm (Total Net Applicable Fee:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 200 355 Tm (Rs. {net_fee:,.2f}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("0.1 0.6 0.2 rg")
        stream.append("1 0 0 1 50 335 Tm (Amount Paid in This Transaction:) Tj")
        stream.append("/F2 11 Tf")
        stream.append(f"1 0 0 1 250 335 Tm (Rs. {amount_paid:,.2f}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("0.2 0.2 0.2 rg")
        stream.append("1 0 0 1 50 315 Tm (Total Cumulative Paid:) Tj")
        stream.append("/F1 10 Tf")
        stream.append(f"1 0 0 1 200 315 Tm (Rs. {total_paid:,.2f}) Tj")

        stream.append("/F2 10 Tf")
        stream.append("0.8 0.1 0.1 rg")
        stream.append("1 0 0 1 50 295 Tm (Current Outstanding Dues:) Tj")
        stream.append("/F2 10 Tf")
        stream.append(f"1 0 0 1 200 295 Tm (Rs. {due_amount:,.2f}) Tj")
        stream.append("ET")

        # Security & Verification note
        stream.append("0.9 0.9 0.9 RG")
        stream.append("40 230 532 0.5 re S")

        stream.append("BT")
        stream.append("/F1 8 Tf")
        stream.append("0.4 0.4 0.4 rg")
        stream.append("1 0 0 1 50 215 Tm (* This is a digitally verified receipt generated by the College ERP system.) Tj")
        stream.append("1 0 0 1 50 203 Tm (* No physical signature is required. Transaction is electronically reconciled with the institutional ledger.) Tj")
        stream.append(f"1 0 0 1 50 191 Tm (* Recorded by: {self.escape_text(recorded_by)} | Printed: {datetime.now().strftime('%d-%b-%Y %I:%M %p')}) Tj")
        stream.append("ET")

        # Signature Box
        stream.append("380 110 180 0.5 re S")
        stream.append("BT")
        stream.append("/F2 9 Tf")
        stream.append("0.1 0.1 0.1 rg")
        stream.append("1 0 0 1 405 95 Tm (Authorized Signatory) Tj")
        stream.append("/F1 8 Tf")
        stream.append("0.3 0.3 0.3 rg")
        stream.append("1 0 0 1 390 82 Tm (Finance & Accounts Department) Tj")
        stream.append(f"1 0 0 1 400 70 Tm ({self.escape_text(college_name[:28])}) Tj")
        stream.append("ET")

        # Footer Banner
        stream.append("0.05 0.22 0.50 rg")
        stream.append("28 30 556 22 re f")
        stream.append("BT")
        stream.append("/F1 8 Tf")
        stream.append("1 1 1 rg")
        stream.append("1 0 0 1 160 38 Tm (College ERP System - Complete Institutional Management Platform) Tj")
        stream.append("ET")

        stream_content = "\n".join(stream).encode('latin-1', 'replace')
        
        # Build PDF structure
        # Obj 1: Catalog
        # Obj 2: Pages
        # Obj 3: Page 1
        # Obj 4: Font Helvetica
        # Obj 5: Font Helvetica-Bold
        # Obj 6: Content Stream

        pdf_output = io.BytesIO()
        pdf_output.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        offsets = []

        # Object 1: Catalog
        offsets.append(pdf_output.tell())
        pdf_output.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

        # Object 2: Pages
        offsets.append(pdf_output.tell())
        pdf_output.write(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

        # Object 3: Page
        offsets.append(pdf_output.tell())
        page_dict = (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 6 0 R /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> >>\nendobj\n"
        )
        pdf_output.write(page_dict)

        # Object 4: Font F1 (Helvetica regular)
        offsets.append(pdf_output.tell())
        pdf_output.write(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n")

        # Object 5: Font F2 (Helvetica bold)
        offsets.append(pdf_output.tell())
        pdf_output.write(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n")

        # Object 6: Stream
        offsets.append(pdf_output.tell())
        pdf_output.write(f"6 0 obj\n<< /Length {len(stream_content)} >>\nstream\n".encode('ascii'))
        pdf_output.write(stream_content)
        pdf_output.write(b"\nendstream\nendobj\n")

        # Xref table
        xref_offset = pdf_output.tell()
        num_objects = len(offsets) + 1
        pdf_output.write(f"xref\n0 {num_objects}\n".encode('ascii'))
        pdf_output.write(b"0000000000 65535 f \n")
        for off in offsets:
            pdf_output.write(f"{off:010d} 00000 n \n".encode('ascii'))

        # Trailer
        pdf_output.write(
            f"trailer\n<< /Size {num_objects} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('ascii')
        )

        return pdf_output.getvalue()
