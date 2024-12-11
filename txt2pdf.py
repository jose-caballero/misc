import re
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER


def parse_markdown(input_text):
    """
    Parses the input markdown text and converts it into a list of ReportLab flowables.
    """
    flowables = []
    styles = getSampleStyleSheet()

    # Define custom styles
    title_styles = {
        f'Heading{level}': ParagraphStyle(
            f'Heading{level}',
            parent=styles['Heading1' if level == 1 else 'Normal'],
            fontSize=24 - (level - 1) * 2,
            leading=28 - (level - 1) * 2,
            spaceAfter=12,
        )
        for level in range(1, 7)
    }
    normal_style = styles['Normal']

    lines = input_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Handle Titles (Sections start on a new page)
        title_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if title_match:
            level = len(title_match.group(1))
            text = title_match.group(2)
            style = title_styles[f'Heading{level}']
            if level == 1 and flowables:  # New section starts on a new page
                flowables.append(PageBreak())
            paragraph = Paragraph(process_inline(text), style)
            flowables.append(paragraph)
            flowables.append(Spacer(1, 12))
            i += 1
            continue

        # Handle Tables
        if '|' in line:
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            table = parse_table(table_lines)
            if table:
                flowables.append(table)
                flowables.append(Spacer(1, 12))
            continue

        # Handle Paragraphs
        paragraph = Paragraph(process_inline(line), normal_style)
        flowables.append(paragraph)
        flowables.append(Spacer(1, 12))
        i += 1

    return flowables


def process_inline(text):
    """
    Processes inline markdown syntax like bold, italic, and underline text.
    """
    bold_pattern = r'(\*\*|__)(.*?)\1'
    italic_pattern = r'(\*|_)(.*?)\1'

    def bold_repl(match):
        return f'<b>{match.group(2)}</b>'

    def italic_repl(match):
        return f'<i>{match.group(2)}</i>'

    text = re.sub(bold_pattern, bold_repl, text)
    text = re.sub(italic_pattern, italic_repl, text)

    return text


def parse_table(table_lines):
    """
    Parses markdown table lines into a ReportLab Table object.
    """
    if len(table_lines) < 2:
        return None
    headers = [cell.strip() for cell in re.split(r'\|', table_lines[0])[1:-1]]
    data = [headers]
    for line in table_lines[2:]:  # Skip the separator
        cells = [cell.strip() for cell in re.split(r'\|', line)[1:-1]]
        if len(cells) == len(headers):
            data.append(cells)
    if not data:
        return None

    tbl = Table(data, hAlign='CENTER')
    tbl_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    tbl.setStyle(tbl_style)
    return tbl


def convert_to_pdf(input_file, output_file):
    """
    Converts the input markdown-like file to a PDF.
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()

        flowables = []

        # Add the first page with title and date
        date_str = datetime.now().strftime('%Y-%m-%d')
        title = Paragraph("Cloud Operations Report", ParagraphStyle('Title', fontSize=36, alignment=TA_CENTER))
        date = Paragraph(date_str, ParagraphStyle('Date', fontSize=24, alignment=TA_CENTER))
        #flowables.extend([Spacer(1, 6 * 72), title, Spacer(1, 24), date, PageBreak()])
        flowables.extend([Spacer(1, 100), title, Spacer(1, 50), date, PageBreak()])

        # Add parsed content
        flowables.extend(parse_markdown(input_text))

        doc = SimpleDocTemplate(
            output_file,
            pagesize=LETTER,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        doc.build(flowables)
        print(f"PDF generated successfully: {output_file}")
    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == '__main__':
    input_filename = input("Enter name of file:")
    output_filename = input_filename + '.pdf'
    convert_to_pdf(input_filename, output_filename)

