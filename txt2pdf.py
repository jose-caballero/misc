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
from reportlab.lib.enums import TA_CENTER  # For center alignment of text

def parse_markdown(input_text):
    """
    Parses the input markdown text and converts it into a list of ReportLab flowables.

    Args:
        input_text (str): The input text containing markdown-like syntax.

    Returns:
        list: A list of ReportLab flowables (text, tables, etc.) to be included in the PDF.
    """
    flowables = []  # List to store elements to be added to the PDF
    styles = getSampleStyleSheet()  # Get default styles provided by ReportLab

    # Define custom styles for different heading levels
    title_styles = {
        f'Heading{level}': ParagraphStyle(
            f'Heading{level}',
            parent=styles['Heading1' if level == 1 else 'Normal'],
            fontSize=24 - (level - 1) * 2,  # Font size decreases with level
            leading=28 - (level - 1) * 2,  # Line height decreases with level
            spaceAfter=12,  # Space after the heading
        )
        for level in range(1, 7)  # Define styles for headings 1 through 6
    }

    normal_style = styles['Normal']  # Default style for regular paragraphs

    lines = input_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Handle headings defined by # symbols
        title_match = re.match(r'^(#{1,6})\s+(.*)', line)  # Match lines like "# Heading"
        if title_match:
            level = len(title_match.group(1))  # Number of # symbols defines the level
            text = title_match.group(2)  # Extract the heading text
            style = title_styles[f'Heading{level}']  # Select the appropriate style
            if level == 1 and flowables:  # Insert a page break for new sections
                flowables.append(PageBreak())
            paragraph = Paragraph(process_inline(text), style)  # Create a styled paragraph
            flowables.append(paragraph)
            flowables.append(Spacer(1, 12))  # Add space after the heading
            i += 1
            continue

        # Handle tables (lines containing '|')
        if '|' in line:
            table_lines = []
            while i < len(lines) and '|' in lines[i]:  # Continue until the table ends
                table_lines.append(lines[i])
                i += 1
            table = parse_table(table_lines)  # Parse the table lines
            if table:
                flowables.append(table)  # Add the table to the flowables
                flowables.append(Spacer(1, 12))  # Add space after the table
            continue

        # Handle regular paragraphs
        paragraph = Paragraph(process_inline(line), normal_style)
        flowables.append(paragraph)
        flowables.append(Spacer(1, 12))  # Add space after the paragraph
        i += 1

    return flowables

def process_inline(text):
    """
    Processes inline markdown syntax like bold (**text**) and italic (*text*).

    Args:
        text (str): The input text with inline markdown syntax.

    Returns:
        str: Text with ReportLab-compatible HTML tags for styling.
    """
    bold_pattern = r'(\*\*|__)(.*?)\1'  # Pattern for bold (** or __)
    italic_pattern = r'(\*|_)(.*?)\1'  # Pattern for italic (* or _)

    # Replace bold markdown with <b> tags
    def bold_repl(match):
        return f'<b>{match.group(2)}</b>'

    # Replace italic markdown with <i> tags
    def italic_repl(match):
        return f'<i>{match.group(2)}</i>'

    text = re.sub(bold_pattern, bold_repl, text)  # Apply bold replacements
    text = re.sub(italic_pattern, italic_repl, text)  # Apply italic replacements

    return text

def parse_table(table_lines):
    """
    Parses markdown table lines into a ReportLab Table object.

    Args:
        table_lines (list): List of strings representing the table in markdown format.

    Returns:
        Table: A styled ReportLab Table object.
    """
    if len(table_lines) < 2:  # A valid table requires at least a header and one row
        return None

    # Extract headers from the first line (ignoring leading and trailing |)
    headers = [cell.strip() for cell in re.split(r'\|', table_lines[0])[1:-1]]
    data = [headers]  # Initialize table data with headers

    # Extract data rows (skipping the separator line)
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in re.split(r'\|', line)[1:-1]]
        if len(cells) == len(headers):  # Ensure row length matches header length
            data.append(cells)

    if not data:
        return None

    # Create the table with centered alignment
    tbl = Table(data, hAlign='CENTER')

    # Apply table styles
    tbl_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Grey background for header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # White text for header
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold font for header
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding for header
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Black grid lines
    ])
    tbl.setStyle(tbl_style)

    return tbl

def convert_to_pdf(input_file, output_file):
    """
    Converts the input markdown-like file to a PDF.

    Args:
        input_file (str): Path to the input file containing markdown-like text.
        output_file (str): Path to save the generated PDF.
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            input_text = f.read()

        flowables = []  # List to store elements for the PDF

        # Add a title page with the current date
        date_str = datetime.now().strftime('%Y-%m-%d')
        title = Paragraph("Cloud Operations Report", ParagraphStyle('Title', fontSize=36, alignment=TA_CENTER))
        date = Paragraph(date_str, ParagraphStyle('Date', fontSize=24, alignment=TA_CENTER))
        flowables.extend([Spacer(1, 100), title, Spacer(1, 50), date, PageBreak()])

        # Parse the markdown content and add to flowables
        flowables.extend(parse_markdown(input_text))

        # Create and build the PDF document
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



