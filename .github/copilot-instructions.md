# Label Print Server - AI Coding Instructions

## Project Overview
A Flask web application for looking up customer information from SQL Server and printing labels on Windows systems. Used in a warehouse/retail environment where users scan quotation numbers to print customer labels.

## Architecture & Data Flow
- **Frontend**: Single-page HTML app (`templates/index.html`) with real-time lookup as user types
- **Backend**: Flask API (`app.py`) with main endpoints: `/lookup`, `/print`, `/get-settings`, `/save-settings`
- **Database**: SQL Server with Windows Authentication, queries across 3 tables:
  - `Tran2`: Transaction records (VchType='26' for quotations)
  - `Master1`: Customer master data (MasterType=2 for shops)
  - `MasterAddressInfo`: Customer address details
- **Printing**: Uses Windows `notepad /p` command to send text files to default printer
- **Settings**: Modal dialog (⚙️ button) for database configuration without workflow interruption

## Critical Database Query Pattern
```python
# Input: quotation number (e.g., "9171")
# Format as: 25-character right-aligned string with 'G-' prefix
formatted_vch_no = f"G-{quotation_number}".rjust(25)
# Result: "                   G-9171"
```

**Query Chain:**
1. Get MasterCode from `Tran2.CM1` using formatted VchNo
2. Get customer name from `Master1.Name` using MasterCode
3. Get address details from `MasterAddressInfo` using MasterCode

## Settings Management
- **Storage**: Database settings saved to `db_settings.json`, fallback to `.env` variables
- **UI**: Settings button (top-right) opens modal without interfering with main workflow
- **Validation**: Connection test before saving new database settings
- **Runtime**: Settings loaded on startup and updated dynamically without restart

## Key Conventions
- **Error Handling**: Database connections must be properly closed in try/except blocks
- **Data Format**: Quotation numbers are zero-padded and prefixed for database queries
- **Response Structure**: Lookup returns comprehensive customer data (name, address, phone, mobile)
- **Printing**: Labels include quotation number, customer info, and contact details
- **UI Focus**: Main quotation input stays focused, settings accessed via discrete button

## Development Workflow
- **Dependencies**: Flask, pyodbc, python-dotenv (see `requirements.txt`)
- **Environment**: Virtual environment with `.venv/Scripts/python.exe`
- **Configuration**: Database settings via UI or `.env` file (`DB_SERVER`, `DB_NAME`)
- **Testing**: Run with virtual environment Python, access via `http://localhost:5000`
- **Deployment**: Designed for Windows server with SQL Server and printer access

## Integration Points
- **Database**: SQL Server with Windows Authentication (Trusted_Connection=yes)
- **Printer**: Windows default printer via notepad command
- **Network**: Designed for Raspberry Pi browsers connecting to Windows server
- **Real-time**: Auto-lookup on keystroke with debounced database queries
- **Settings**: Runtime database configuration with connection validation

## Common Patterns
- Use `get_party_info()` for all customer lookups (returns dict or None)
- Always validate `request.json` exists before accessing data
- Format database strings exactly as shown in existing queries
- Handle missing address fields gracefully in label generation
- Test database connections before saving settings
- Use CSS classes (not inline styles) for show/hide functionality