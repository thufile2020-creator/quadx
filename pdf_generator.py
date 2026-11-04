"""Printable, evidence-backed carbon passport PDF (self-reported estimates)."""
from pathlib import Path
from html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)

DARK = colors.HexColor('#183A3B')
TEAL = colors.HexColor('#117B6A')
SOFT = colors.HexColor('#E9F3EF')
MUTED = colors.HexColor('#5C6D70')
GRAY_BG = colors.HexColor('#F3F6F5')
ORANGE = colors.HexColor('#B26322')


def _safe(value):
    return escape(str(value), quote=True)


def _fmt(value, decimals=2):
    return f"{float(value):,.{decimals}f}"


def generate_passport_pdf(passport: dict, output_path: str, qr_path: str = None, qr_url: str = None) -> str:
    """Write PDF; input is the normalized output from build_passport()."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Brand', fontName='Helvetica-Bold', fontSize=19, leading=23, textColor=DARK, spaceAfter=6))
    styles.add(ParagraphStyle(name='SectionCustom', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=DARK, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='BodyCustom', fontName='Helvetica', fontSize=9, leading=13, textColor=DARK, spaceAfter=5))
    styles.add(ParagraphStyle(name='SmallCustom', fontName='Helvetica', fontSize=7.5, leading=10, textColor=MUTED, spaceAfter=3, wordWrap='CJK'))
    styles.add(ParagraphStyle(name='CellCustom', fontName='Helvetica', fontSize=7.4, leading=10, textColor=DARK, wordWrap='CJK'))
    styles.add(ParagraphStyle(name='CellHeadCustom', fontName='Helvetica-Bold', fontSize=7.2, leading=10, textColor=colors.white))
    styles.add(ParagraphStyle(name='HeroCustom', fontName='Helvetica-Bold', fontSize=21, leading=26, textColor=TEAL))

    usable_width = A4[0] - 36*mm
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=20*mm, bottomMargin=18*mm, title=f"CarbonEase Passport - {passport['report_id']}",
                            author="CarbonEase Hackathon Demo")
    body = []
    body.append(Paragraph('CarbonEase <font color="#117B6A">/</font> Carbon Passport', styles['Brand']))
    body.append(Paragraph('BUSINESS EMISSIONS SUMMARY | EVIDENCE-LINKED REPORT', styles['SmallCustom']))
    body.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#D7E6E1'), spaceAfter=10))

    status = _safe(passport['status'])
    meta = [
        [Paragraph('<b>REPORT ID</b>', styles['SmallCustom']), Paragraph('<b>REPORTING PERIOD</b>', styles['SmallCustom']), Paragraph('<b>REPORT STATUS</b>', styles['SmallCustom'])],
        [Paragraph(_safe(passport['report_id']), styles['BodyCustom']),
         Paragraph(_safe(passport['period']['start']) + ' to ' + _safe(passport['period']['end']), styles['BodyCustom']),
         Paragraph(status, styles['SmallCustom'])]
    ]
    tbl = Table(meta, colWidths=[usable_width*.27, usable_width*.36, usable_width*.37])
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),GRAY_BG),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    body += [tbl, Spacer(1, 11)]

    b = passport['business']
    company_info = [
        Paragraph(_safe(b['name']), styles['SectionCustom']),
        Paragraph(f"{_safe(b['industry'])} | {_safe(b['location'])} | Supplier ID: {_safe(b['supplier_id'])}", styles['BodyCustom'])
    ]
    if qr_path and qr_url and Path(qr_path).is_file():
        company_info.append(Paragraph('Scan QR to view the digital demo passport', styles['SmallCustom']))
        qr_image = Image(qr_path, width=26*mm, height=26*mm)
        company_table = Table([[company_info, qr_image]], colWidths=[usable_width - 30*mm, 30*mm])
        company_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
        body.append(company_table)
    else:
        body += company_info
    body.append(Spacer(1, 6))

    head = Table([
        [Paragraph('TOTAL LISTED EMISSIONS', styles['SmallCustom']), Paragraph('Scope 1', styles['SmallCustom']), Paragraph('Scope 2', styles['SmallCustom']), Paragraph('Scope 3', styles['SmallCustom'])],
        [Paragraph(_fmt(passport['total_kg_co2e']) + ' kg CO2e', styles['HeroCustom']),
         Paragraph(_fmt(passport['scope_totals_kg_co2e']['Scope 1'])+' kg', styles['BodyCustom']),
         Paragraph(_fmt(passport['scope_totals_kg_co2e']['Scope 2'])+' kg', styles['BodyCustom']),
         Paragraph(_fmt(passport['scope_totals_kg_co2e']['Scope 3'])+' kg', styles['BodyCustom'])]
    ], colWidths=[usable_width*.42, usable_width*.19, usable_width*.19, usable_width*.20])
    head.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),SOFT),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
    body.append(head)

    production = passport.get('production')
    if production:
        intensity = passport.get('operational_intensity_kg_co2e_per_unit')
        body.append(Spacer(1, 9))
        body.append(Paragraph(f"Operational emissions intensity: <b>{_fmt(intensity,4)} kg CO2e / {_safe(production['unit'])}</b> "
                              f"for {_fmt(production['quantity'], 0)} {_safe(production['unit'])} produced.", styles['BodyCustom']))
        body.append(Paragraph('Allocation: ' + _safe(production['allocation_note']), styles['SmallCustom']))

    body.append(Paragraph('Activity inventory and factors', styles['SectionCustom']))
    cells = [[Paragraph(x, styles['CellHeadCustom']) for x in ('Activity / evidence', 'Scope', 'Quantity', 'Factor', 'Emissions')]]
    for r in passport['activities']:
        evidence = r.get('evidence_file') or 'No evidence filename provided'
        source_cell = f"<b>{_safe(r['source'])}</b><br/>{_safe(r['id'])}<br/><font color='#5C6D70'>Evidence: {_safe(evidence)}</font>"
        factor_cell = f"{_fmt(r['emission_factor'], 4)}<br/><font color='#5C6D70'>{_safe(r['factor_unit'])}</font>"
        cells.append([
            Paragraph(source_cell, styles['CellCustom']),
            Paragraph(_safe(r['scope']), styles['CellCustom']),
            Paragraph(_fmt(r['quantity'], 2) + '<br/>' + _safe(r['unit']), styles['CellCustom']),
            Paragraph(factor_cell, styles['CellCustom']),
            Paragraph(_fmt(r['kg_co2e'], 2) + ' kg', styles['CellCustom'])
        ])
    data_table = Table(cells, repeatRows=1, colWidths=[usable_width*.34, usable_width*.13, usable_width*.16, usable_width*.20, usable_width*.17], hAlign='LEFT')
    data_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,GRAY_BG]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#D7E6E1')),
        ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),5),
    ]))
    body.append(data_table)

    body.append(Paragraph('Factors and methodology', styles['SectionCustom']))
    body.append(Paragraph(_safe(passport['methodology']), styles['BodyCustom']))
    for record in passport['activities']:
        body.append(Paragraph(f"<b>{_safe(record['id'])} ({_safe(record['source'])}):</b> "
                              f"{_safe(record['factor_source'])} (factor year {_safe(record['factor_year'])}).", styles['SmallCustom']))

    if passport.get('quality_notes'):
        body.append(Paragraph('Data quality notes', styles['SectionCustom']))
        for note in passport['quality_notes']:
            body.append(Paragraph('- ' + _safe(note), styles['SmallCustom']))

    body.append(Paragraph('Important limitations', styles['SectionCustom']))
    for note in passport['limitations']:
        body.append(Paragraph('- ' + _safe(note), styles['SmallCustom']))


    def page_footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#D7E6E1'))
        canvas.line(18*mm, 14.2*mm, A4[0]-18*mm, 14.2*mm)
        canvas.setFont('Helvetica',7)
        canvas.setFillColor(MUTED)
        canvas.drawString(18*mm, 10.7*mm, 'CARBONEASE | Self-reported emissions estimate | NOT A CERTIFICATION')
        canvas.drawRightString(A4[0]-18*mm, 10.7*mm, f'Page {document.page}')
        canvas.restoreState()

    doc.build(body, onFirstPage=page_footer, onLaterPages=page_footer)
    return str(path)
