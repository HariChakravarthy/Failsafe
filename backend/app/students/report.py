import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, Line
from ml.explain import FEATURE_LABELS

def generate_student_report(student, prediction, interventions) -> bytes:
    """
    Generates a beautifully styled, high-impact PDF report for a student using ReportLab.
    """
    buffer = io.BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        leading=14
    )

    body_bold = ParagraphStyle(
        'BodyTextDarkBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        leading=12
    )

    table_text_bold = ParagraphStyle(
        'TableTextBold',
        parent=table_text,
        fontName='Helvetica-Bold'
    )

    story = []
    
    # 1. Header Section
    story.append(Paragraph("FAILSAFE ACADEMIC RISK REPORT", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    
    # Draw a line separator
    d_line = Drawing(532, 2)
    d_line.add(Line(0, 0, 532, 0, strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=1))
    story.append(d_line)
    story.append(Spacer(1, 10))
    
    # 2. Student Profile Table
    story.append(Paragraph("Student Profile", h2_style))
    profile_data = [
        [
            Paragraph("Name:", body_bold),
            Paragraph(student.name or "N/A", body_style),
            Paragraph("Student Code:", body_bold),
            Paragraph(student.student_code, body_style)
        ],
        [
            Paragraph("Department:", body_bold),
            Paragraph(student.department or "N/A", body_style),
            Paragraph("Semester:", body_bold),
            Paragraph(str(student.semester) if student.semester else "N/A", body_style)
        ],
        [
            Paragraph("Gender:", body_bold),
            Paragraph("Female" if student.gender == "F" else "Male" if student.gender == "M" else (student.gender or "N/A"), body_style),
            Paragraph("Age:", body_bold),
            Paragraph(str(student.age) if student.age else "N/A", body_style)
        ]
    ]
    
    profile_table = Table(profile_data, colWidths=[100, 166, 100, 166])
    profile_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor("#f1f5f9")),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 15))
    
    # 3. Risk Assessment Summary
    story.append(Paragraph("Risk Assessment", h2_style))
    
    risk_score_pct = int(prediction.risk_score * 100)
    risk_level = prediction.risk_level.upper()
    
    if risk_level == "HIGH":
        risk_color = colors.HexColor("#ef4444")
        bg_color = colors.HexColor("#fef2f2")
    elif risk_level == "MEDIUM":
        risk_color = colors.HexColor("#f97316")
        bg_color = colors.HexColor("#fff7ed")
    else:
        risk_color = colors.HexColor("#22c55e")
        bg_color = colors.HexColor("#f0fdf4")
        
    risk_level_para = Paragraph(f"<font color='{risk_color.hexval()}'><b>{risk_level} RISK ({risk_score_pct}%)</b></font>", body_bold)
    
    summary_para = Paragraph(prediction.shap_summary or "No summary available.", body_style)
    
    risk_data = [
        [Paragraph("Current Risk Status:", body_bold), risk_level_para],
        [Paragraph("Explanation Summary:", body_bold), summary_para]
    ]
    
    risk_table = Table(risk_data, colWidths=[130, 402])
    risk_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('BOX', (0,0), (-1,-1), 1, risk_color),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 15))
    
    # 4. SHAP Risk Drivers Chart
    story.append(Paragraph("Key Risk Impact Drivers", h2_style))
    story.append(Paragraph("Positive impact values increase predicted academic risk; negative values protect against it.", subtitle_style))
    
    # Extract top SHAP values (absolute value > 0.01)
    shap_items = sorted(prediction.shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
    top_shap = [item for item in shap_items if abs(item[1]) >= 0.01][:6]
    
    shap_data = [
        [
            Paragraph("<b>Risk Feature</b>", table_text_bold),
            Paragraph("<b>Impact</b>", table_text_bold),
            Paragraph("<b>Visualization (Negative vs Positive Impact)</b>", table_text_bold)
        ]
    ]
    
    for feat, val in top_shap:
        feat_label = FEATURE_LABELS.get(feat, feat).title()
        sign = "+" if val > 0 else ""
        impact_str = f"{sign}{val:.4f}"
        impact_color = "#ef4444" if val > 0 else "#22c55e"
        
        # Draw a custom horizontal bar chart element
        # Canvas width: 220px. Center (zero point) is at 110px.
        d = Drawing(220, 14)
        # Background reference lines
        d.add(Line(110, 0, 110, 14, strokeColor=colors.HexColor("#94a3b8"), strokeWidth=1))
        # Draw bar
        normalized_val = max(-1.0, min(1.0, val * 4.0)) # scale it slightly for better visibility
        bar_width = abs(normalized_val) * 110
        if val >= 0:
            d.add(Rect(110, 2, bar_width, 10, fillColor=colors.HexColor("#ef4444"), strokeColor=None))
        else:
            d.add(Rect(110 - bar_width, 2, bar_width, 10, fillColor=colors.HexColor("#22c55e"), strokeColor=None))
            
        shap_data.append([
            Paragraph(feat_label, table_text),
            Paragraph(f"<font color='{impact_color}'><b>{impact_str}</b></font>", table_text),
            d
        ])
        
    shap_table = Table(shap_data, colWidths=[180, 80, 272])
    shap_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(shap_table)
    story.append(Spacer(1, 20))
    
    # 5. Interventions List
    story.append(Paragraph("Recommended Interventions & Action Plan", h2_style))
    if not interventions:
        story.append(Paragraph("No interventions have been registered for this student yet.", body_style))
    else:
        interv_data = [
            [
                Paragraph("<b>Type / Title</b>", table_text_bold),
                Paragraph("<b>Priority</b>", table_text_bold),
                Paragraph("<b>Status</b>", table_text_bold),
                Paragraph("<b>Target Outcome</b>", table_text_bold)
            ]
        ]
        for iv in interventions:
            prio_color = "#ef4444" if iv.priority == "HIGH" else "#f97316" if iv.priority == "MEDIUM" else "#3b82f6"
            status_color = "#22c55e" if iv.status == "COMPLETED" else "#ef4444" if iv.status == "DISMISSED" else "#eab308" if iv.status == "IN_PROGRESS" else "#64748b"
            
            prio_para = Paragraph(f"<font color='{prio_color}'><b>{iv.priority or 'LOW'}</b></font>", table_text)
            status_para = Paragraph(f"<font color='{status_color}'><b>{iv.status.replace('_', ' ')}</b></font>", table_text)
            
            # Title & Description
            title_desc = f"<b>{iv.type.replace('_', ' ').title()}:</b> {iv.title}"
            if iv.description:
                title_desc += f"<br/><font color='#64748b'>{iv.description}</font>"
            title_para = Paragraph(title_desc, table_text)
            
            # Outcome
            outcome_desc = "-"
            if iv.status == "COMPLETED":
                if iv.outcome:
                    outcome_color = "#22c55e" if iv.outcome == "IMPROVED" else "#64748b" if iv.outcome == "NO_CHANGE" else "#ef4444"
                    outcome_desc = f"<font color='{outcome_color}'><b>{iv.outcome}</b></font>"
                if iv.outcome_notes:
                    outcome_desc += f"<br/><font color='#64748b'><i>{iv.outcome_notes}</i></font>"
            outcome_para = Paragraph(outcome_desc, table_text)
            
            interv_data.append([title_para, prio_para, status_para, outcome_para])
            
        interv_table = Table(interv_data, colWidths=[200, 70, 92, 170])
        interv_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor("#e2e8f0")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(interv_table)
        
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
