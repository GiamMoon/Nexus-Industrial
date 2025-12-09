from fpdf import FPDF
from datetime import datetime
import os

class PDFGenerator:
    @staticmethod
    def generar_orden_compra(producto_nombre: str, cantidad: int, proveedor: str) -> str:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "NEXUS ENTERPRISE - ORDEN DE COMPRA", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.cell(0, 10, f"Proveedor Sugerido: {proveedor}", ln=True)
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(100, 10, "Producto", 1)
        pdf.cell(40, 10, "Cantidad", 1)
        pdf.ln()
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(100, 10, producto_nombre, 1)
        pdf.cell(40, 10, str(cantidad), 1)
        
        filename = f"OC_{datetime.now().timestamp()}.pdf"
        path = f"/tmp/{filename}" 
        pdf.output(path)
        
        return path