from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / 'docs'
OUTPUT_DIR = DOCS_DIR


def parse_markdown_lines(md_text):
    lines = []
    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            lines.append(('blank', ''))
            continue

        if line.startswith('### '):
            lines.append(('h3', line[4:].strip()))
        elif line.startswith('## '):
            lines.append(('h2', line[3:].strip()))
        elif line.startswith('# '):
            lines.append(('h1', line[2:].strip()))
        elif line.startswith('- '):
            lines.append(('bullet', line[2:].strip()))
        elif line[:3].isdigit() and line[1:3] == '. ':
            lines.append(('num', line.strip()))
        elif line[0].isdigit() and len(line) > 2 and line[1:3] == '. ':
            lines.append(('num', line.strip()))
        else:
            lines.append(('p', line.strip()))
    return lines


def markdown_to_pdf(source_md: Path, output_pdf: Path):
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0B4F8A'),
        spaceAfter=10,
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#173A5E'),
        spaceBefore=8,
        spaceAfter=5,
    )
    h3_style = ParagraphStyle(
        'H3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1D4E89'),
        spaceBefore=6,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=14,
        bulletIndent=4,
        spaceAfter=2,
    )

    content = source_md.read_text(encoding='utf-8')
    entries = parse_markdown_lines(content)

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title=source_md.stem,
        author='MediMind Team',
    )

    story = []
    for kind, text in entries:
        if kind == 'blank':
            story.append(Spacer(1, 0.08 * inch))
            continue

        safe = (
            text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
        )

        if kind == 'h1':
            story.append(Paragraph(safe, title_style))
        elif kind == 'h2':
            story.append(Paragraph(safe, h2_style))
        elif kind == 'h3':
            story.append(Paragraph(safe, h3_style))
        elif kind in ('bullet', 'num'):
            story.append(Paragraph(safe, bullet_style, bulletText='-'))
        else:
            story.append(Paragraph(safe, body_style))

    doc.build(story)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sources = [
        DOCS_DIR / 'DEFENSE_MID_REPORT.md',
        DOCS_DIR / 'PROJECT_TECHNICAL_DOCUMENTATION.md',
    ]

    generated = []
    for source in sources:
        if not source.exists():
            raise FileNotFoundError(f'Missing input markdown: {source}')
        output_pdf = OUTPUT_DIR / f'{source.stem}.pdf'
        markdown_to_pdf(source, output_pdf)
        generated.append(output_pdf)

    for pdf in generated:
        print(f'Generated: {pdf}')


if __name__ == '__main__':
    main()
