import os
from docx import Document as DocxDocument
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from reportlab.lib.pagesizes import A4
import re

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from flask import current_app
from web.app.models import DocumentApp, DocumentSectionContent


def clean_html_content(html_content):
    """
    Clean HTML content by removing tags and preserving text formatting.
    
    Args:
        html_content (str): HTML content to clean
        
    Returns:
        str: Cleaned text content
    """
    if not html_content:
        return ""
        
    # Replace <br> and <p> tags with newlines
    content = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
    content = re.sub(r'</?p\s*/?>', '\n', content, flags=re.IGNORECASE)
    
    # Replace <i> and <em> tags with special markers
    content = re.sub(r'<i>', '[[italic_start]]', content, flags=re.IGNORECASE)
    content = re.sub(r'</i>', '[[italic_end]]', content, flags=re.IGNORECASE)
    content = re.sub(r'<em>', '[[italic_start]]', content, flags=re.IGNORECASE)
    content = re.sub(r'</em>', '[[italic_end]]', content, flags=re.IGNORECASE)
    
    # Remove all other HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Replace HTML entities
    content = content.replace('&nbsp;', ' ')
    content = content.replace('&amp;', '&')
    content = content.replace('&lt;', '<')
    content = content.replace('&gt;', '>')
    content = content.replace('&quot;', '"')
    content = content.replace('&#39;', "'")
    
    # Clean up multiple newlines and whitespace
    content = re.sub(r'\n\s*\n', '\n', content)  # Replace multiple newlines with single newline
    content = re.sub(r' +', ' ', content)
    
    # Remove leading/trailing whitespace and empty lines
    content = '\n'.join(line for line in content.split('\n') if line.strip())
    content = content.strip()
    
    return content


def export_to_docx(document_id):
    """
    Export document to DOCX format according to GOST 7.32-2017

    Args:
        document_id (int): Document ID

    Returns:
        str: Path to the exported file
    """
    document = DocumentApp.query.get_or_404(document_id)
    sections = document.sections.order_by(DocumentSectionContent.id).all()

    # Create a new Word document
    docx = DocxDocument()

    # Set up document according to GOST 7.32-2017
    section = docx.sections[0]
    section.page_height = Cm(29.7)  # A4
    section.page_width = Cm(21.0)  # A4
    section.left_margin = Cm(3.0)  # Left margin 3 cm
    section.right_margin = Cm(1.5)  # Right margin 1.5 cm
    section.top_margin = Cm(2.0)  # Top margin 2 cm
    section.bottom_margin = Cm(2.0)  # Bottom margin 2 cm

    # Add title
    title = docx.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run(document.title)
    title_run.font.name = 'Times New Roman'
    title_run.font.size = Pt(16)
    title_run.font.bold = True

    # Add document sections
    for section_content in sections:
        p = docx.add_paragraph()

        # Set paragraph formatting according to section type
        section_template = section_content.section_template
        if section_template.code == 'ТЛ' or section_template.code == 'СИ':
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(section_template.name)
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            run.font.bold = True

            # Add section content
            p = docx.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            p.paragraph_format.first_line_indent = Cm(1.25)  # First line indent 1.25 cm
            p.paragraph_format.left_indent = Cm(0)  # Ensure left indent is 0
            p.paragraph_format.space_before = Pt(0)  # Remove space before paragraph
            p.paragraph_format.space_after = Pt(0)  # Remove space after paragraph
            p.paragraph_format.keep_together = True  # Keep paragraph together
            p.paragraph_format.keep_with_next = False  # Don't keep with next paragraph
            
            # Process content with italic formatting
            content = clean_html_content(section_content.content)
            if not content.strip():  # Skip empty paragraphs
                continue
                
            # Split content into paragraphs and process each one
            paragraphs = content.split('\n')
            for i, para in enumerate(paragraphs):
                if not para.strip():
                    continue
                    
                if i > 0:  # Add new paragraph for each line after the first
                    p = docx.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
                    p.paragraph_format.first_line_indent = Cm(1.25)
                    p.paragraph_format.left_indent = Cm(0)
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.keep_together = True
                    p.paragraph_format.keep_with_next = False
                
                parts = para.split('[[italic_start]]')
                
                # Add first part if it exists
                if parts[0]:
                    run = p.add_run(parts[0])
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(14)
                
                # Process remaining parts with italic formatting
                for part in parts[1:]:
                    if '[[italic_end]]' in part:
                        italic_part, rest = part.split('[[italic_end]]', 1)
                        # Add italic part
                        run = p.add_run(italic_part)
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(14)
                        run.italic = True
                        # Add rest of the text
                        if rest:
                            run = p.add_run(rest)
                            run.font.name = 'Times New Roman'
                            run.font.size = Pt(14)
                    else:
                        # If no end marker, treat as normal text
                        run = p.add_run(part)
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(14)
        else:  # Default paragraph formatting
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            p.paragraph_format.first_line_indent = Cm(1.25)  # First line indent 1.25 cm
            p.paragraph_format.left_indent = Cm(0)  # Ensure left indent is 0
            p.paragraph_format.space_before = Pt(0)  # Remove space before paragraph
            p.paragraph_format.space_after = Pt(0)  # Remove space after paragraph
            p.paragraph_format.keep_together = True  # Keep paragraph together
            p.paragraph_format.keep_with_next = False  # Don't keep with next paragraph
            
            # Process content with italic formatting
            content = clean_html_content(section_content.content)
            if not content.strip():  # Skip empty paragraphs
                continue
                
            # Split content into paragraphs and process each one
            paragraphs = content.split('\n')
            for i, para in enumerate(paragraphs):
                if not para.strip():
                    continue
                    
                if i > 0:  # Add new paragraph for each line after the first
                    p = docx.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
                    p.paragraph_format.first_line_indent = Cm(1.25)
                    p.paragraph_format.left_indent = Cm(0)
                    p.paragraph_format.space_before = Pt(0)
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.keep_together = True
                    p.paragraph_format.keep_with_next = False
                
                parts = para.split('[[italic_start]]')
                
                # Add first part if it exists
                if parts[0]:
                    run = p.add_run(parts[0])
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(14)
                
                # Process remaining parts with italic formatting
                for part in parts[1:]:
                    if '[[italic_end]]' in part:
                        italic_part, rest = part.split('[[italic_end]]', 1)
                        # Add italic part
                        run = p.add_run(italic_part)
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(14)
                        run.italic = True
                        # Add rest of the text
                        if rest:
                            run = p.add_run(rest)
                            run.font.name = 'Times New Roman'
                            run.font.size = Pt(14)
                    else:
                        # If no end marker, treat as normal text
                        run = p.add_run(part)
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
    sections = document.sections.order_by(DocumentSectionContent.id).all()

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
        topMargin=57,  # ~2 cm
        bottomMargin=57  # ~2 cm
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Create custom styles according to GOST 7.32-2017
    gost_title_style = ParagraphStyle(
        name='GOSTTitle',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=16,
        leading=18,
        alignment=1,  # Center
        spaceAfter=12,
        encoding='UTF-8'
    )
    styles.add(gost_title_style)

    gost_heading_style = ParagraphStyle(
        name='GOSTHeading',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=14,
        leading=16,
        alignment=1,  # Center
        spaceAfter=12,
        encoding='UTF-8'
    )
    styles.add(gost_heading_style)

    gost_normal_style = ParagraphStyle(
        name='GOSTNormal',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=14,
        leading=21,  # 1.5 line spacing
        alignment=0,  # Left
        firstLineIndent=35,  # 1.25 cm
        spaceBefore=0,
        spaceAfter=0,
        encoding='UTF-8'
    )
    styles.add(gost_normal_style)

    # Build the document
    elements = []

    # Add title
    title_text = document.title.encode('utf-8').decode('utf-8')
    elements.append(Paragraph(title_text, styles['GOSTTitle']))
    elements.append(Spacer(1, 12))

    # Add sections
    for section_content in sections:
        section_template = section_content.section_template

        if section_template.code == 'ТЛ' or section_template.code == 'СИ':
            # Add section title
            title_text = section_template.name.encode('utf-8').decode('utf-8')
            elements.append(Paragraph(title_text, styles['GOSTHeading']))
            elements.append(Spacer(1, 12))

        # Add section content
        content = clean_html_content(section_content.content)
        if content.strip():
            # Split content into paragraphs and add each one
            paragraphs = content.split('\n')
            for para in paragraphs:
                if para.strip():
                    # Process italic formatting
                    parts = para.split('[[italic_start]]')
                    if len(parts) > 1:
                        # Handle italic text
                        for i, part in enumerate(parts):
                            if i == 0:
                                # First part is normal text
                                if part:
                                    text = part.encode('utf-8').decode('utf-8')
                                    elements.append(Paragraph(text, styles['GOSTNormal']))
                            else:
                                # Handle italic parts
                                if '[[italic_end]]' in part:
                                    italic_part, rest = part.split('[[italic_end]]', 1)
                                    # Add italic text
                                    italic_text = italic_part.encode('utf-8').decode('utf-8')
                                    italic_style = ParagraphStyle(
                                        name='GOSTItalic',
                                        parent=styles['GOSTNormal'],
                                        fontName='Times-Italic',
                                        encoding='UTF-8'
                                    )
                                    elements.append(Paragraph(italic_text, italic_style))
                                    # Add rest of the text
                                    if rest:
                                        text = rest.encode('utf-8').decode('utf-8')
                                        elements.append(Paragraph(text, styles['GOSTNormal']))
                                else:
                                    # If no end marker, treat as normal text
                                    text = part.encode('utf-8').decode('utf-8')
                                    elements.append(Paragraph(text, styles['GOSTNormal']))
                    else:
                        # Normal text without formatting
                        text = para.encode('utf-8').decode('utf-8')
                        elements.append(Paragraph(text, styles['GOSTNormal']))
                    elements.append(Spacer(1, 0))  # No extra space between paragraphs

    # Build the PDF
    pdf.build(elements)

    return output_path

