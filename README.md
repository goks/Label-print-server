# Label Print Server

> **Enterprise-grade Flask web application for automated customer label printing from quotation numbers in warehouse/retail environments.**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](#)

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Configuration](#️-configuration)
- [Auto-Startup & Tray Application](#️-auto-startup--tray-application)
- [Monitoring & Health Checks](#-monitoring--health-checks)
- [User Interface](#-user-interface)
- [Development](#-development)
  - [Project Structure](#project-structure)
  - [API Endpoints](#api-endpoints-reference)
  - [Key Functions](#key-functions-documentation)
- [Security](#-security)
- [Performance & Scaling](#-performance--scaling)
- [Troubleshooting](#-troubleshooting)
- [Requirements](#-requirements)
- [Documentation](#-documentation)
- [Support](#-support--troubleshooting)

---

## 🎯 Overview

Label Print Server is a production-ready web application that streamlines warehouse and retail operations by automating customer label printing. Staff simply scan or enter quotation numbers, and the system instantly retrieves customer information from SQL Server and prints professional shipping labels.

**Perfect For**:
- Warehouse shipping departments
- Retail distribution centers
- Order fulfillment operations
- Any business needing rapid customer label printing from transaction numbers

**What Makes It Special**:
- ⚡ **Lightning Fast**: Real-time lookup with optimized database queries (<100ms)
- 🔄 **Multi-Copy Printing**: Sequential numbering (1/5, 2/5, etc.) for bulk orders
- 👴 **Accessibility**: Distance-optimized 720p UI for elderly users
- 🚀 **Zero-Config Startup**: Auto-starts with Windows, runs silently in system tray
- 📊 **Complete Audit Trail**: Every printed label tracked with full search capability
- 🔌 **Network Ready**: Access from multiple workstations via browser

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Windows System Tray                         │
│  ┌──────────────┐  ┌────────────────────────────────────────┐  │
│  │  Tray Icon   │  │   GUI Management Interface (Tkinter)   │  │
│  │  (pystray)   │──│   • Server Control                     │  │
│  │              │  │   • Auto-Startup Config                │  │
│  └──────────────┘  │   • Print History Viewer               │  │
│                    │   • Database Settings                  │  │
│                    └────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │   Flask Application (app.py)            │
         │   Waitress WSGI Server (Port 5000)      │
         │                                         │
         │   ┌─────────────────────────────────┐   │
         │   │  Connection Pool (5 threads)    │   │
         │   │  Thread-Safe DB Access          │   │
         │   └─────────────────────────────────┘   │
         └─────────────────────────────────────────┘
                    │                    │
        ┌───────────┴──────────┐  ┌──────┴─────────┐
        ▼                      ▼  ▼                ▼
┌──────────────┐     ┌─────────────────┐   ┌──────────────┐
│ SQL Server   │     │  Print History  │   │   Printers   │
│ (Customer DB)│     │  (SQLite DB)    │   │  (Windows)   │
│              │     │                 │   │              │
│ • Tran2      │     │ • Audit Trail   │   │ • Default    │
│ • Master1    │     │ • Search Index  │   │ • BarTender  │
│ • AddressInfo│     │ • Export CSV    │   │ • Network    │
└──────────────┘     └─────────────────┘   └──────────────┘
        ▲                                          ▲
        │                                          │
        └──────────────────┬───────────────────────┘
                           │
                  ┌────────────────────┐
                  │  Web Browsers      │
                  │  (Workstations)    │
                  │  http://server:5000│
                  └────────────────────┘
```

**Data Flow**:
1. User enters quotation number in web browser
2. Flask API queries SQL Server via connection pool
3. Customer data retrieved and displayed
4. User prints → Label sent to printer + history recorded to SQLite
5. GUI can view history, configure settings, control server

## ✨ Key Features

### Core Functionality
- **Real-time Customer Lookup** - Instant customer details as you type quotation numbers
- **Multi-Copy Printing** - Print multiple labels with sequential numbering (1/5, 2/5, etc.)
- **Professional Label Printing** - Supports both Windows text printing and BarTender templates
- **Print History Tracking** - Complete audit trail of all printed labels with search
- **Modern Web Interface** - Large, distance-optimized UI suitable for 720p viewing by elderly users
- **Runtime Settings** - Configure database and printer settings without restart via modal dialog

### Production Features
- **Enterprise Logging** - Multi-level logging with automatic rotation (daily/size-based)
- **Health Monitoring** - Built-in health checks and metrics endpoints
- **System Tray Application** - Silent background operation with GUI management
- **Auto-Startup** - Windows boot integration with one-click setup
- **Database Connection Pool** - Thread-safe pooling for optimal performance (5x faster)
- **Database Resilience** - Advanced error handling and connection recovery
- **Security Hardening** - Production-ready security headers and input validation
- **Performance Monitoring** - Request timing, slow query detection, and performance metrics
- **Auto-Update System** - GitHub-based version checking and update installation

## GitHub Releases

To publish an update that the tray updater can detect:

1. Update the `VERSION` file.
2. Commit and push your changes.
3. Create and push a git tag like `v3.1.3`.
4. GitHub Actions will build `Output/LabelPrintServer_Setup.exe` and attach it to the release for that tag.

The tray updater checks GitHub releases for a newer `LabelPrintServer_Setup.exe` asset and offers users a download-and-update option from the Updates tab.

### System Integration
- **SQL Server Integration** - Native Windows Authentication with driver auto-detection
- **Printer Management** - Network and local printer support with configuration
- **Single Instance Protection** - Prevents multiple server instances
- **Update System** - GitHub-based auto-update with version checking
- **Background Operation** - Windowless execution with VBScript launcher

## 🚀 Quick Start

### One-Click Installation (Recommended)
```powershell
# Double-click INSTALL.bat to launch the graphical installer
INSTALL.bat
```

The installer will guide you through:
1. Selecting installation location (default: current directory)
2. Choosing whether to auto-start with Windows
3. Creating desktop and Start Menu shortcuts
4. Setting up the application environment

After installation, the application will start automatically in your system tray.

### Manual Installation
```powershell
# 1. Clone repository
git clone <repository-url>
cd Label-print-server

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database
# Use the web UI settings panel at http://localhost:5000

# 5. Run application
python tray_app.py
# Or for silent background mode:
start_tray_silent.vbs
```

### First-Time Setup
1. **Database Configuration**: Click the ⚙️ button in the web interface at `http://localhost:5000`
2. **Enter Database Details**: Server name and database name
3. **Test Connection**: Verify connectivity before saving
4. **Start Using**: Enter quotation numbers to print labels

### Verify Installation
```powershell
# Check if server is running
# Open browser: http://localhost:5000/health
# Should return: {"status": "healthy", "database": "connected", ...}
```

## ⚙️ Configuration

### Database Setup
Database settings are configured via the web interface or `db_settings.json` file:

**Via Web Interface (Recommended):**
1. Open `http://localhost:5000`
2. Click the ⚙️ settings button (top-right)
3. Enter SQL Server name and database name
4. Click "Test Connection" to verify
5. Click "Save Settings" to apply

**Via Configuration File:**
```json
{
  "db_server": "YOUR_SQL_SERVER_NAME",
  "db_name": "YOUR_DATABASE_NAME"
}
```

### Required Database Tables
The application expects these SQL Server tables:

**Tran2** - Transaction records
- `VchNo` VARCHAR(25) - Quotation number (right-aligned with 'G-' prefix)
- `VchType` VARCHAR(2) - Must be '26' for quotations
- `MasterCode2` VARCHAR(3) - Must be '201'
- `CM1` VARCHAR(10) - Customer master code (links to Master1.Code)

**Master1** - Customer master data
- `Code` VARCHAR(10) - Customer code (primary key)
- `Name` VARCHAR(100) - Customer name
- `MasterType` INT - Must be 2 for shops

**MasterAddressInfo** - Customer address details
- `MasterCode` VARCHAR(10) - Links to Master1.Code
- `Address1-4` VARCHAR(100) - Address lines
- `Telno` VARCHAR(20) - Phone number
- `Mobile` VARCHAR(20) - Mobile number

### Environment Variables (Optional)
Advanced configuration via `.env` file:
```env
# Application
FLASK_ENV=production
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
SECRET_KEY=your-secure-key

# Database  
DB_SERVER=your-sql-server         # Overridden by db_settings.json
DB_NAME=your-database-name        # Overridden by db_settings.json
DATABASE_CONNECTION_TIMEOUT=30
DB_POOL_SIZE=5                    # Connection pool size
DB_POOL_TIMEOUT=30

# Performance
REQUEST_TIMEOUT=60
THREADS=4
MAX_CONTENT_LENGTH=16777216       # 16MB max request size

# Security (comma-separated)
TRUSTED_HOSTS=localhost,127.0.0.1,192.168.10.55
```

## �️ Auto-Startup & Tray Application

### Auto-Startup Configuration (Recommended)
The Label Print Server can be configured to start automatically with Windows, running silently in the system tray:

```powershell
# Complete auto-startup setup (recommended)
python auto_startup.py setup

# Interactive management menu
python auto_startup.py menu

# Manual commands
python auto_startup.py install    # Configure auto-startup
python auto_startup.py status     # Check current status  
python auto_startup.py uninstall  # Remove auto-startup
python auto_startup.py shortcut   # Create desktop shortcut

# Quick removal (with confirmation)
remove_startup.bat
```

### Tray Application Features
- **🔄 Auto-Start**: Starts automatically with Windows
- **🪟 Silent Mode**: No console window, runs in background  
- **🎯 System Tray Icon**: Quick access and status monitoring
- **🔒 Single Instance**: Prevents multiple server instances
- **📊 GUI Management**: User-friendly control interface
- **🔌 Instant Access**: Server available at http://localhost:5000

### Manual Tray Control
```powershell
# Start tray application (with console)
python tray_app.py

# Start silently (no console window)
start_tray_silent.vbs

# Start with batch file
run_tray.bat
```

### Startup Files
- **`auto_startup.py`** - Auto-startup installer/manager
- **`start_tray_silent.vbs`** - Silent startup script (no console)
- **`run_tray.bat`** - Batch file startup with virtual environment
- **`remove_startup.bat`** - User-friendly removal script
- **`INSTALL.bat`** - Launch graphical installer
- **`setup_installer.py`** - GUI installation wizard
- **`tray_app.py`** - Main tray application with embedded server

### Managing Auto-Startup
Auto-startup is configured during installation via the graphical installer. To remove:
```powershell
# Quick removal with confirmation
remove_startup.bat

# Or run the uninstaller created during installation
python uninstall.py
```

### GUI Startup Management
The tray GUI provides user-friendly startup management:

- 🔍 **Real-time Status** - Shows current auto-startup configuration
- ✅ **Enable Auto-Startup** - One-click Windows boot configuration  
- ❌ **Disable Auto-Startup** - Easy removal from startup programs
- 🔄 **Instant Updates** - Status updates automatically every 30 seconds
- ⚠️ **Error Handling** - Clear error messages and troubleshooting
- 💡 **Tooltips** - Helpful guidance for each startup option

## 📊 Monitoring & Health Checks

### Health Check Endpoint
```bash
GET /health
```
Returns system health status, database connectivity, and uptime information.

### Metrics Endpoint  
```bash
GET /metrics
```
Provides application metrics, log file status, and performance data.

### Log Files
All logs stored in `logs/` directory:
- `label_print_server.log` - Main application log (daily rotation)
- `errors.log` - Error-only log (size-based rotation) 
- `database.log` - Database operations and performance
- `access.log` - HTTP request/response logging
- `service_stdout.log` - Windows service output
- `service_stderr.log` - Windows service errors

## 🛠️ Service Management (Alternative to Tray)

### Windows Service Commands
For dedicated server environments where tray applications are not suitable:

```bash
# Install service
python service_manager.py install

# Service control
python service_manager.py start
python service_manager.py stop  
python service_manager.py restart
python service_manager.py status

# View logs
python service_manager.py logs

# Uninstall service
python service_manager.py uninstall
```

### Manual Server Start
```bash
# Development mode
python app.py

# Production mode
python wsgi.py

# Or use batch file
start_production.bat
```

## 🎨 User Interface

### Web Interface
- **Main Page** - Quotation lookup and label printing
- **Settings Modal** - Database and printer configuration
- **Test Connection** - Real-time database connectivity testing
- **Print History** - View and track all printed labels

### Tray Application & GUI Manager
- **System Tray Icon** - Quick access to server controls and status
- **Modern GUI Interface** - Comprehensive management dashboard with:
  - 🚦 **Server Control** - Start/stop server with visual status indicators
  - 🚀 **Auto-Startup Management** - Enable/disable Windows boot startup
  - 📊 **Print History** - View, search, and export printed label records
  - ⚙️ **Settings Management** - Database and printer configuration
  - 🔒 **Single Instance Protection** - Prevents multiple server instances
  - 📱 **System Tray Integration** - Minimize to tray, quick restore

## 🔧 Development

### Project Structure
```
Label-print-server/
├── app.py                    # Main Flask application with API endpoints
├── wsgi.py                   # Production WSGI entry point
├── tray_app.py              # System tray application with embedded server
├── tray_gui.py              # Tkinter GUI management interface
├── printed_db.py            # SQLite print history database manager
├── update_manager.py        # GitHub-based auto-update system
├── run_production.py        # Production mode launcher
├── INSTALL.bat              # Launch graphical installer
├── setup_installer.py       # GUI installation wizard
├── start_tray_silent.vbs    # Silent VBScript launcher (no console)
├── run_tray.bat            # Batch launcher with virtual environment
├── remove_startup.bat      # User-friendly auto-startup removal
├── force_start.bat         # Force start (kills existing instances)
├── cleanup_tray.bat        # Cleanup utility for stuck instances
├── db_settings.json        # Database configuration (runtime-editable)
├── VERSION                 # Application version file
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── FUNCTIONS.md           # Detailed function documentation
├── templates/
│   └── index.html         # Main web interface (distance-optimized UI)
├── logs/                  # Application logs (auto-rotated)
│   ├── label_print_server.log    # Main application log
│   ├── database.log              # Database operations
│   ├── errors.log                # Error-only log
│   └── access.log                # HTTP access log
├── icons/                 # Application icons
│   └── favicon.ico       # Tray icon and favicon
└── .venv/                # Python virtual environment
```

### Core Application Files

**app.py** (1766 lines)
- Flask application with production configuration
- Database connection pooling (thread-safe)
- Customer lookup and label printing endpoints
- Multi-copy printing with sequential numbering
- Print history tracking
- Settings management API
- Health and metrics endpoints
- Comprehensive logging system

**tray_app.py** (741 lines)
- System tray icon and menu
- Embedded Waitress WSGI server
- Single instance enforcement
- Inter-process signal monitoring
- GUI process management
- Silent background operation
- Graceful shutdown handling

**tray_gui.py** (1889 lines)
- Modern Tkinter management interface
- Multi-tab notebook design
- Server control with status indicators
- Auto-startup configuration UI
- Print history viewer with search/export
- Database settings with connection testing
- Update checking and installation UI
- System information display

**printed_db.py**
- SQLite database for print history
- Thread-safe connection management
- Indexed searches for performance
- Pagination support
- Export functionality

### Database Schema

**SQL Server Tables (Production Database)**:
```sql
-- Transaction records (quotations)
CREATE TABLE Tran2 (
    VchNo VARCHAR(25),          -- Right-aligned: "                   G-9171"
    VchType VARCHAR(2),         -- '26' for quotations
    MasterCode2 VARCHAR(3),     -- '201' for specific transaction type
    CM1 VARCHAR(10)             -- Customer master code (FK to Master1.Code)
)

-- Customer master data
CREATE TABLE Master1 (
    Code VARCHAR(10) PRIMARY KEY,
    Name VARCHAR(100),
    MasterType INT              -- 2 for shops/customers
)

-- Customer address details
CREATE TABLE MasterAddressInfo (
    MasterCode VARCHAR(10),     -- FK to Master1.Code
    Address1 VARCHAR(100),
    Address2 VARCHAR(100), 
    Address3 VARCHAR(100),
    Address4 VARCHAR(100),
    Telno VARCHAR(20),
    Mobile VARCHAR(20)
)
```

**SQLite Database (Print History)**:
```sql
CREATE TABLE printed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quotation TEXT NOT NULL,
    party TEXT,
    address TEXT,
    phone TEXT,
    mobile TEXT,
    printed_at TEXT NOT NULL
);

CREATE INDEX idx_quotation ON printed(quotation);
CREATE INDEX idx_printed_at ON printed(printed_at DESC);
```

### API Endpoints Reference

#### Customer Operations
| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/lookup` | POST | Customer lookup | `{"quotation": "9171"}` | Party info or error |
| `/print` | POST | Print label(s) | `{"quotation": "9171", "party": "...", "copies": 5}` | Success/error with message |
| `/preview-label` | POST | Label preview | Customer data | Formatted label text |

#### Configuration
| Endpoint | Method | Purpose | Description |
|----------|--------|---------|-------------|
| `/get-settings` | GET | Get config | Returns current database settings |
| `/save-settings` | POST | Save config | Tests connection, saves to db_settings.json |
| `/test-connection` | POST | Test DB | Validates connection without saving |
| `/get-printers` | GET | List printers | Returns available Windows printers |

#### Print History
| Endpoint | Method | Purpose | Query Params |
|----------|--------|---------|--------------|
| `/printed-records` | GET | Get history | `?q=search&limit=100&offset=0` |

#### Monitoring
| Endpoint | Method | Purpose | Use Case |
|----------|--------|---------|----------|
| `/health` | GET | Health check | Load balancer monitoring, uptime verification |
| `/metrics` | GET | Performance metrics | Performance monitoring, diagnostics |
| `/print-status` | GET | Print queue status | Printer availability check |

#### System Control
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/control` | POST | Server control | Local token (inter-process) |
| `/shutdown` | POST | Graceful shutdown | Local token only |

### Key Functions Documentation

For detailed function documentation including parameters, return values, examples, and implementation details, see **[FUNCTIONS.md](FUNCTIONS.md)**.

**Quick Reference**:
- `get_party_info(quotation_number)` - Customer lookup with optimized JOIN query
- `print_label(...)` - Universal printing function (text/BarTender)
- `DatabaseConnectionPool` - Thread-safe connection pooling
- `start_server()` / `stop_server()` - Tray app server control
- `record_print(...)` - Print history recording
- `check_for_updates()` - GitHub release checking

### Configuration Files

**db_settings.json** (Runtime database config)
```json
{
  "db_server": "SQLSERVER01",
  "db_name": "CustomerDB"
}
```

**VERSION** (Application version)
```
2.0.0
```

**update_config.json** (Update system config - optional)
```json
{
  "auto_check": true,
  "auto_install": false,
  "check_interval_hours": 24,
  "update_channel": "stable"
}
```

## 🔒 Security

### Production Security Features
- **Security Headers** - XSS protection, content-type sniffing prevention
- **Input Validation** - All user inputs validated and sanitized
- **Error Handling** - Safe error responses without information disclosure
- **Request Limits** - Maximum request size enforcement
- **Windows Authentication** - Integrated SQL Server authentication

### Network Security
- **Firewall Configuration** - Restrict access to required networks only
- **HTTPS Support** - Use reverse proxy (IIS/nginx) for SSL termination
- **Access Logging** - Complete audit trail of all requests

## 📈 Performance & Scaling

### Performance Features
- **Connection Pooling** - Efficient database connection management
- **Multi-threading** - Concurrent request handling (4 threads default)
- **Request Caching** - Optimized for frequent lookups
- **Log Rotation** - Automatic log management to prevent disk issues

### Scaling Considerations
- **Horizontal Scaling** - Deploy multiple instances behind load balancer
- **Database Optimization** - Ensure proper indexes on lookup tables
- **Monitoring Integration** - Health checks support load balancer integration

## 🐛 Troubleshooting

### Common Issues

**Database Connection Problems:**
1. Use Test Connection feature in Settings
2. Check `logs/database.log` for detailed errors
3. Verify SQL Server is running and accessible
4. Confirm Windows user has database permissions

**Service Issues:**
1. Check Windows Event Viewer
2. Review service logs: `python service_manager.py logs`
3. Verify NSSM installation: `nssm status LabelPrintServer`

**Performance Issues:**
1. Monitor `logs/label_print_server.log` for slow request warnings
2. Check `/metrics` endpoint for system status
3. Review access patterns in `logs/access.log`

### Debug Mode
```bash
# Enable debug logging
set LOG_LEVEL=DEBUG
python app.py
```

## 📋 Requirements

### System Requirements
- **Windows 10/11** or **Windows Server 2016+**
- **Python 3.8+** (3.9+ recommended)
- **SQL Server** (2012+ or any version with ODBC drivers)
- **Network Printer** (optional - local printers supported)
- **Disk Space**: 500MB minimum (for application, logs, virtual environment)
- **RAM**: 512MB minimum, 1GB recommended
- **Display**: 720p minimum (UI optimized for distance viewing)

### Python Dependencies
See `requirements.txt` for complete list. Key dependencies:

**Core Framework**:
- `Flask>=2.3.0` - Web framework
- `waitress>=2.1.2` - Production WSGI server

**Database**:
- `pyodbc>=4.0.39` - SQL Server connectivity
- `python-dotenv>=1.0.0` - Environment configuration

**Windows Integration**:
- `pywin32>=306` - Windows API access (COM, registry, GUI)
- `pystray>=0.19.4` - System tray functionality
- `Pillow>=10.0.0` - Image processing for icons

**Utilities**:
- `requests>=2.31.0` - HTTP client for updates
- `packaging>=23.0` - Version comparison

### ODBC Drivers
Application auto-detects and uses the best available driver:

**Recommended** (in order):
1. **ODBC Driver 18 for SQL Server** (latest, recommended)
2. **ODBC Driver 17 for SQL Server** (widely supported)
3. **SQL Server** (legacy driver, fallback)

**Installation**:
```powershell
# Download from Microsoft:
# https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

# Or use winget:
winget install Microsoft.SQLServerODBCDriver
```

### Installation Steps
```powershell
# 1. Install Python 3.8+ from python.org or Microsoft Store

# 2. Install ODBC drivers (if not already installed)
winget install Microsoft.SQLServerODBCDriver

# 3. Clone or download repository
git clone https://github.com/goks/Label-print-server.git
cd Label-print-server

# 4. Run graphical installer
INSTALL.bat

# 5. Configure database via web UI
# Open http://localhost:5000 and click settings ⚙️
```

## 📚 Documentation

### Available Documentation
- **[README.md](README.md)** - This file - overview, installation, configuration
- **[FUNCTIONS.md](FUNCTIONS.md)** - Detailed function documentation with examples
- **[VERSION](VERSION)** - Current application version

### Additional Resources
- **Logs Directory** (`logs/`) - Detailed operational logs with timestamps
- **Health Endpoint** (`/health`) - Real-time system status
- **Metrics Endpoint** (`/metrics`) - Performance and usage statistics

## 📄 License

This project is proprietary software. All rights reserved.

## 🤝 Support & Troubleshooting

### Getting Help
1. **Check Logs**: Review `logs/` directory for detailed error information
   - `label_print_server.log` - Main application log
   - `database.log` - Database connection and query logs
   - `errors.log` - Error-only log for quick troubleshooting

2. **Health Check**: Visit `http://localhost:5000/health` for system status

3. **Common Issues**:
   - **Database Connection Failed**: 
     - Verify SQL Server is running
     - Check Windows user has database permissions
     - Test connection via Settings panel
     - Review `logs/database.log` for specific errors
   
   - **Port 5000 Already in Use**:
     - Another instance may be running
     - Check system tray for existing icon
     - Run `cleanup_tray.bat` to reset
   
   - **Auto-Startup Not Working**:
     - Run `python auto_startup.py status` to check configuration
     - Verify VBScript file exists: `start_tray_silent.vbs`
     - Check Windows Event Viewer for startup errors
   
   - **Print Jobs Not Executing**:
     - Verify default printer is set in Windows
     - Check printer is online and has paper
     - Review `logs/label_print_server.log` for print errors
     - Test BarTender template path if using templates

4. **Debug Mode**: Enable detailed logging
   ```powershell
   # In PowerShell
   $env:LOG_LEVEL = "DEBUG"
   python app.py
   ```

5. **Reset Application**:
   ```powershell
   # Stop all instances
   cleanup_tray.bat
   
   # Remove auto-startup
   remove_startup.bat
   
   # Clear print history (optional)
   # Delete: printed_records.db
   
   # Restart fresh
   python tray_app.py
   ```

### Feature Highlights

#### Multi-Copy Printing
- Enter number of copies when printing
- Sequential numbering: 1/5, 2/5, 3/5, 4/5, 5/5
- Each copy recorded separately in history
- 500ms delay between copies for printer processing

#### Distance-Optimized UI
- Large fonts (30-70% larger than standard)
- High contrast design
- Bold labels (600-700 font weight)
- Optimized for 720p displays viewed from distance
- Suitable for elderly users with reduced vision

#### Print History
- Complete audit trail of all printed labels
- Search by quotation, customer, or address
- Pagination support (100 records per page)
- Export to CSV for external analysis
- Indexed database for fast searches

#### Auto-Update System
- Checks GitHub releases for new versions
- Configurable update channels (stable/beta)
- Automatic backup before updating
- Rollback support on update failure
- Manual or automatic update installation

### Performance Tips
1. **Database Optimization**:
   - Ensure indexes exist on SQL Server lookup tables
   - Monitor query performance in `database.log`
   - Adjust `DB_POOL_SIZE` for high-volume environments

2. **Log Management**:
   - Logs auto-rotate daily/size-based
   - Review and archive old logs periodically
   - Adjust retention in logging configuration

3. **Scaling**:
   - Deploy multiple instances for load balancing
   - Use reverse proxy (IIS/nginx) for SSL and load distribution
   - Monitor `/metrics` endpoint for capacity planning

---

**Label Print Server v2.0** - Enterprise-grade customer label printing solution.

**Project Repository**: [github.com/goks/Label-print-server](https://github.com/goks/Label-print-server)

**Maintained By**: Label Print Server Development Team  
**Last Updated**: November 15, 2025
