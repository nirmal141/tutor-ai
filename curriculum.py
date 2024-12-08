from fpdf import FPDF
import streamlit as st
from datetime import datetime

class CurriculumPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Curriculum Plan', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_curriculum_pdf(curriculum_content, grade, subject, duration):
    pdf = CurriculumPDF()
    pdf.add_page()
    
    # Add title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'{grade} {subject} Curriculum Plan', 0, 1, 'C')
    pdf.cell(0, 10, f'Duration: {duration}', 0, 1, 'C')
    pdf.ln(10)
    
    # Add generation date
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'R')
    pdf.ln(10)
    
    # Add content
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, curriculum_content)
    
    return pdf.output(dest='S').encode('latin-1')
