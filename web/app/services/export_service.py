import os
from docx import Document as DocxDocument
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from flask import current_app
from ..models import DocumentApp, DocumentBlock

def export_to_docx(document_id):
    """
    Export document to DOCX format according to GOST 7.32-2017
    
    Args:
        document_id (int): Document ID
        
    Returns:
        str: Path to the exported file
    """
    document = DocumentApp.query.get_or_404(document_id)
    blocks = document.blocks.order_by(DocumentBlock.order).all()
    
    # Create a new Word document
    docx = DocxDocument()
    
    # Set up document according to GOST 7.32-2017
    section = docx.sections[0]
    section.page_height = Cm(29.7)  # A4
    section.page_width = Cm(21.0)   # A4
    section.left_margin = Cm(3.0)   # Left margin 3 cm
    section.right_margin = Cm(1.5)  # Right margin 1.5 cm
    section.top_margin = Cm(2.0)    # Top margin 2 cm
    section.bottom_margin = Cm(2.0) # Bottom margin 2 cm
    
    # Add title
    title = docx.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(document.title)
    title_run.font.name = 'Times New Roman'
    title_run.font.size = Pt(16)
    title_run.font.bold = True
    
    # Add document blocks
    for block in blocks:
        p = docx.add_paragraph()
        
        # Set paragraph formatting according to block type
        if block.block_type == 'heading':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(block.content)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            run.font.bold = True
        else:  # Default paragraph formatting
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            p.paragraph_format.first_line_indent = Cm(1.25)  # First line indent 1.25 cm
            run = p.add_run(block.content)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
    
    # Save the document
    output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'exports')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{document.title}_{document.id}.docx")
    docx.save(output_path)
    
    return output_path

def export_to_pdf(document_id):
    """
    Export document to PDF format according to GOST 7.32-2017
    
    Args:
        document_id (int): Document ID
        
    Returns:
        str: Path to the exported file
    """
    document = DocumentApp.query.get_or_404(document_id)
    blocks = document.blocks.order_by(DocumentBlock.order).all()
    
    # Create output directory
    output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'exports')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{document.title}_{document.id}.pdf")
    
    # Create PDF document
    pdf = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=85,  # ~3 cm
        rightMargin=42,  # ~1.5 cm
        topMargin=57,    # ~2 cm
        bottomMargin=57  # ~2 cm
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Create custom styles according to GOST 7.32-2017
    styles.add(ParagraphStyle(
        name='Title',
        parent=styles['Title'],
        fontName='Times-Roman',
        fontSize=16,
        leading=18,
        alignment=1,  # Center
        spaceAfter=12
    ))
    
    styles.add(ParagraphStyle(
        name='Heading',
        parent=styles['Heading1'],
        fontName='Times-Roman',
        fontSize=14,
        leading=16,
        alignment=1,  # Center
        spaceAfter=12
    ))
    
    styles.add(ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=14,
        leading=21,  # 1.5 line spacing
        alignment=4,  # Justify
        firstLineIndent=35,  # ~1.25 cm
        spaceAfter=6
    ))
    
    # Build PDF content
    content = []
    
    # Add title
    content.append(Paragraph(document.title, styles['Title']))
    content.append(Spacer(1, 12))
    
    # Add document blocks
    for block in blocks:
        if block.block_type == 'heading':
            content.append(Paragraph(block.content, styles['Heading']))
        else:  # Default paragraph formatting
            content.append(Paragraph(block.content, styles['Normal']))
    
    # Build the PDF
    pdf.build(content)
    
    return output_path

