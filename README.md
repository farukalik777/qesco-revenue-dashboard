# QESCO Government Department - Revenue Dashboard

A comprehensive Streamlit application for analyzing government department billing accuracy and payment recovery.

## Features

- **📊 Dashboard Analytics**
  - Revenue overview with KPIs
  - Assessment vs Recovery analysis
  - Arrears analysis by department
  - Closing balance tracking

- **📑 Custom Reports**
  - Multiple aggregation levels (Circle, Division, Sub Division, Department)
  - Customizable columns
  - Export to CSV and PDF

- **📋 Master Ledger**
  - Searchable detailed records
  - Filter by various criteria

- **🔒 Password Protected**
  - Secure access with password authentication

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
cd app
streamlit run app.py
```

## Deployment to Streamlit Cloud

1. Push this code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy!

## File Structure

```
├── app/
│   ├── app.py              # Main application
│   └── utils/
│       ├── __init__.py
│       ├── data_processor.py    # Data loading utilities
│       └── pdf_generator.py    # PDF report generation
├── requirements.txt
├── README.md
└── data/                  # Data files (not included)
    ├── AUTO-BODIES-*.xlsx
    ├── LOCAL-BODIES-*.xlsx
    ├── PROV-GOVT-DEPT *.xlsx
    ├── SubDivisioncode.xlsx
    └── All Departments Codes.xlsx
```

## Usage

1. Upload an Excel file with pre-processed QESCO data
2. Use sidebar filters to narrow down data
3. View analytics in different tabs
4. Generate custom reports and export to CSV/PDF

## Security

- Password: `Qesco@786`
- Change password in app.py

## License

Private - QESCO Government Department
