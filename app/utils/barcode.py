from barcode import Code128
from barcode.writer import ImageWriter

def generate_file_barcode(file_number):
    barcode = Code128(file_number, writer=ImageWriter())
    path = f"app/static/barcodes/{file_number}"
    barcode.save(path)
    
import qrcode

def generate_file_qr(file):
    img = qrcode.make(file.file_number)
    img.save(f"app/static/qrcodes/{file.file_number}.png")
