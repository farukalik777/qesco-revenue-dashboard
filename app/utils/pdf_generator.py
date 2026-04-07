"""
PDF Report Generator
Creates professional A4 formatted PDF reports
"""

from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def __init__(self):
        super().__init__('L', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=13)

    def header(self):
        self.set_left_margin(13)
        self.set_right_margin(10)
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, "Government of Pakistan  |  QESCO  |  Government of Balochistan", ln=True, align='C', fill=True)
        self.ln(3)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, "QESCO Government Department", ln=True, align='C')
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, f"Revenue Report - {self.agg_level}", ln=True, align='C')
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, f"Page {self.page_no()}", align='C')

    def set_agg_level(self, level):
        self.agg_level = level


def generate_pdf_report(report_df, display_cols, col_config, agg_level, rep_df=None):
    """Generate PDF report with proper formatting"""
    if rep_df is None:
        rep_df = report_df

    pdf = PDF()
    pdf.set_agg_level(agg_level)
    pdf.add_page()
    pdf.set_left_margin(13)

    # Build table headers
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    col_widths = []
    for col in display_cols:
        if col in ['CIRCLENAME', 'DIVNAME', 'SUBDIVNAME', 'DEPARTMENT_NAME']:
            col_widths.append(46)
        else:
            col_widths.append(25)
    for i, col_name in enumerate(display_cols):
        header = col_config.get(col_name, {}).get("label", col_name) if isinstance(col_config, dict) else col_name
        pdf.cell(col_widths[i], 7, str(header), border=1, align='C', fill=True)
    pdf.ln()

    # Table rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 7)
    fill = False
    for _, row in report_df.iterrows():
        if fill:
            pdf.set_fill_color(245, 245, 245)
        else:
            pdf.set_fill_color(255, 255, 255)
        fill = not fill
        for i, col in enumerate(display_cols):
            val = str(row.get(col, ''))[:20]
            pdf.cell(col_widths[i], 5, val, border=1, align='C', fill=True)
        pdf.ln()

    # Totals row
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(col_widths[0], 7, "TOTAL", border=1, align='C', fill=True)
    for i, col in enumerate(display_cols[1:], 1):
        if col == 'Connections':
            val = str(rep_df['CONSNO'].count())[:18]
        elif col == 'Active':
            if 'PDISC' in rep_df.columns:
                val = str((rep_df['PDISC'] == 0).sum())
            else:
                val = str(rep_df['CONSNO'].count())
        elif col == 'Disconnected':
            if 'PDISC' in rep_df.columns:
                val = str((rep_df['PDISC'] > 0).sum())
            else:
                val = '0'
        elif col == 'ASSESSMENT_AMNT':
            val = f"{rep_df['ASSESSMENT_AMNT'].sum()/1e6:.2f}M"
        elif col == 'PAYMENT_NOR':
            val = f"{rep_df['PAYMENT_NOR'].sum()/1e6:.2f}M"
        elif col == 'TOTAL_CL_BAL':
            val = f"{rep_df['TOTAL_CL_BAL'].sum()/1e6:.2f}M"
        elif col == 'Recovery_%':
            total_ass = rep_df['ASSESSMENT_AMNT'].sum()
            total_pay = rep_df['PAYMENT_NOR'].sum()
            val = f"{(total_pay/total_ass*100):.1f}%" if total_ass > 0 else "0%"
        elif col == 'Accuracy_%':
            total_match = rep_df['MATCH'].sum()
            total_all = rep_df['ALL'].sum()
            val = f"{(total_match/total_all*100):.1f}%" if total_all > 0 else "0%"
        else:
            val = ''
        pdf.cell(col_widths[i], 7, val, border=1, align='C', fill=True)
    pdf.ln()

    return bytes(pdf.output())
