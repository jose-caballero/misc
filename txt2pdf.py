import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    ListFlowable,
    ListItem,
)
from reportlab.lib.enums import TA_LEFT

def parse_markdown(input_text):
    """
    Parses the input markdown text and converts it into a list of ReportLab flowables.
    """
    flowables = []
    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=18,
        leading=22,
        spaceAfter=10,
    )
    normal_style = styles['Normal']
    bold_style = ParagraphStyle(
        'BoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold'
    )
    list_style = ParagraphStyle(
        'ListStyle',
        parent=styles['Normal'],
        leftIndent=20,
        bulletIndent=10,
        spaceBefore=5,
        spaceAfter=5,
    )

    lines = input_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Handle Titles
        title_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if title_match:
            level = len(title_match.group(1))
            text = title_match.group(2)
            style = title_style if level == 1 else subtitle_style
            paragraph = Paragraph(process_inline(text), style)
            flowables.append(paragraph)
            flowables.append(Spacer(1, 12))
            i += 1
            continue

        # Handle Tables
        if '|' in line:
            # Check if it's a table
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            table = parse_table(table_lines)
            if table:
                flowables.append(table)
                flowables.append(Spacer(1, 12))
            continue

        # Handle Lists
        list_match = re.match(r'^(\*|\-|\d+\.)\s+(.*)', line)
        if list_match:
            list_items = []
            while i < len(lines):
                current_line = lines[i].strip()
                lm = re.match(r'^(\*|\-|\d+\.)\s+(.*)', current_line)
                if lm:
                    item_text = process_inline(lm.group(2))
                    list_items.append(ListItem(Paragraph(item_text, normal_style)))
                    i += 1
                else:
                    break
            lf = ListFlowable(
                list_items,
                bulletType='bullet' if list_match.group(1) in ['*', '-'] else '1',
                start='1' if list_match.group(1).endswith('.') else None,
                bulletFontName='Helvetica',
                bulletFontSize=12,
                leftIndent=20,
            )
            flowables.append(lf)
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
    Processes inline markdown syntax like bold text.
    """
    # Handle bold text **text** or __text__
    bold_pattern = r'(\*\*|__)(.*?)\1'

    def bold_repl(match):
        return f'<b>{match.group(2)}</b>'

    return re.sub(bold_pattern, bold_repl, text)

def parse_table(table_lines):
    """
    Parses markdown table lines into a ReportLab Table object.
    """
    # Remove separator lines like |---|---|
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

    tbl = Table(data, hAlign='LEFT')
    tbl_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ])
    tbl.setStyle(tbl_style)
    return tbl

def convert_to_pdf(input_file, output_file):
    """
    Converts the input markdown-like file to a PDF.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        input_text = f.read()

    flowables = parse_markdown(input_text)

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


if __name__ == '__main__':
    convert_to_pdf("input.txt", 'output.pdf')
