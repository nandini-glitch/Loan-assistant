import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

def generate_sanction_letter_pdf(details):
    """Generate a professional sanction letter PDF"""
    output_dir = 'generated_letters'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{output_dir}/sanction_letter_{details['loan_reference_number']}.pdf"
    
    print(f"[PDF Generator] Creating PDF at: {filename}")
    
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
        fontSize=18, textColor=colors.HexColor('#1a237e'), spaceAfter=30,
        alignment=TA_CENTER, fontName='Helvetica-Bold')
    
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
        fontSize=12, textColor=colors.HexColor('#283593'), spaceAfter=12,
        fontName='Helvetica-Bold')
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14
    
    # Header
    story.append(Paragraph("TATA CAPITAL LIMITED", title_style))
    story.append(Paragraph("Personal Loan Sanction Letter", heading_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Reference details
    ref_data = [
        ['Loan Reference Number:', details['loan_reference_number']],
        ['Date of Sanction:', details['sanction_date']],
        ['Valid Until:', details['validity_date']]
    ]
    ref_table = Table(ref_data, colWidths=[2.5*inch, 3*inch])
    ref_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(ref_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Customer details
    story.append(Paragraph("Customer Details", heading_style))
    cust_data = [
        ['Name:', details['customer_name']],
        ['Address:', details['customer_address']],
        ['PAN:', details['customer_pan']],
        ['Email:', details['customer_email']]
    ]
    cust_table = Table(cust_data, colWidths=[2.5*inch, 3*inch])
    cust_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(cust_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Loan details
    story.append(Paragraph("Loan Details", heading_style))
    loan_data = [
        ['Sanctioned Amount:', f"₹{details['loan_amount']:,}"],
        ['Tenure:', f"{details['tenure_months']} months"],
        ['Interest Rate:', f"{details['interest_rate']}% p.a."],
        ['EMI Amount:', f"₹{details['emi_amount']:,.2f}"],
        ['Processing Fee:', f"₹{details['processing_fee']:,.2f}"],
        ['Total Interest:', f"₹{details['total_interest']:,.2f}"],
        ['Total Amount Payable:', f"₹{details['total_payable']:,.2f}"]
    ]
    loan_table = Table(loan_data, colWidths=[2.5*inch, 3*inch])
    loan_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#424242')),
        ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#e8eaf6')),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(loan_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Terms and conditions
    story.append(Paragraph("Terms and Conditions", heading_style))
    for idx, term in enumerate(details['terms'], 1):
        story.append(Paragraph(f"{idx}. {term}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Documents required
    story.append(Paragraph("Documents Required for Disbursal", heading_style))
    for doc_item in details['documents_required']:
        story.append(Paragraph(f"• {doc_item}", normal_style))
        story.append(Spacer(1, 0.08*inch))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_text = """
    <para alignment="center">
    <b>This is a system-generated document and does not require a signature.</b><br/>
    For queries, contact us at: customercare@tatacapital.com | 1800-209-9966<br/>
    <br/>
    <b>Tata Capital Limited</b><br/>
    11th Floor, Tower A, Peninsula Business Park, Ganpatrao Kadam Marg,<br/>
    Lower Parel, Mumbai - 400013
    </para>
    """
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(footer_text, normal_style))
    
    # Build PDF
    doc.build(story)
    
    # Verify file was created
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        abs_path = os.path.abspath(filename)
        print(f"[PDF Generator] ✅ PDF created successfully!")
        print(f"[PDF Generator] Path: {abs_path}")
        print(f"[PDF Generator] Size: {file_size} bytes")
    else:
        print(f"[PDF Generator] ❌ PDF creation failed!")
    
    return filename