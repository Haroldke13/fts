from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_file_report(file):
    filename = f"app/static/reports/file_{file.file_number}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)

    c.drawString(40, 800, f"FILE REPORT: {file.file_number}")
    c.drawString(40, 780, f"Department: {file.department}")

    y = 740
    for tx in file.transactions:
        c.drawString(40, y, f"{tx.user.name} | {tx.checkout_time}")
        y -= 15

    c.save()
    return filename
