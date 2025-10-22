# Label Print Server

> **Enterprise-grade Flask web application for automated customer label printing from quotation numbers in warehouse/retail environments.**

## 🎯 Overview

Label Print Server is a production-ready web application that looks up customer information from SQL Server databases and prints professional labels on Windows systems. Originally designed for warehouse operations where staff scan quotation numbers to quickly print customer shipping labels.

## ✨ Features

### Core Functionality
- **Real-time Customer Lookup** - Type quotation numbers, get instant customer details
- **Professional Label Printing** - Supports both text printing and BarTender templates
- **Print History Tracking** - Complete audit trail of all printed labels
- **Modern Web Interface** - Responsive design works on desktop and mobile devices

### Production Features
- **Enterprise Logging** - Multi-level logging with automatic rotation and retention
- **Health Monitoring** - Built-in health checks and metrics endpoints
- **Windows Service** - Runs as system service with automatic startup
- **Database Resilience** - Advanced error handling and connection recovery
- **Security Hardening** - Production-ready security headers and input validation
- **Performance Monitoring** - Request timing, slow query detection, and performance metrics

### System Integration
- **SQL Server Integration** - Native Windows Authentication support
- **Printer Management** - Network and local printer support with configuration
- **Tray Application** - System tray interface for easy server management
- **Settings Management** - Runtime configuration without service restarts

## 🚀 Quick Start

### Production Deployment (Recommended - Auto-Startup with Tray)
```powershell
# Quick setup (automated)
setup.bat

# Or manual setup:
# 1. Clone and setup
git clone <repository-url>
cd Label-print-server

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database (see Configuration section)
copy .env.production .env
# Edit .env with your database settings

# 5. Setup auto-startup with system tray
python auto_startup.py setup

# 6. Start immediately (or will start automatically on next boot)
start_tray_silent.vbs
```

### Alternative Deployment Methods
```powershell
# Windows Service (for dedicated servers)
python service_manager.py install
python service_manager.py start

# Manual tray application
python tray_app.py

# Development server only
python app.py

# Verify deployment
# Visit: http://localhost:5000/health
```

## ⚙️ Configuration

### Database Setup
Configure your SQL Server connection in `.env`:
```env
DB_SERVER="Your Server Name"
DB_NAME="You Db Name"
```

### Required Database Tables
- **Tran2** - Transaction records (VchType='26' for quotations)
- **Master1** - Customer master data (MasterType=2 for shops) 
- **MasterAddressInfo** - Customer address details

### Environment Variables
```env
# Application
FLASK_ENV=production
LOG_LEVEL=INFO
SECRET_KEY=your-secure-secret-key

# Database  
DB_SERVER=your-sql-server
DB_NAME=your-database-name
DATABASE_CONNECTION_TIMEOUT=30

# Performance
REQUEST_TIMEOUT=60
THREADS=4
MAX_CONTENT_LENGTH=16777216

# Security
TRUSTED_HOSTS=localhost,127.0.0.1,192.168.10.55
```

## �️ Auto-Startup & Tray Application

### Auto-Startup Configuration (Recommended)
The Label Print Server can be configured to start automatically with Windows, running silently in the system tray:

```powershell
# Complete auto-startup setup (recommended)
python auto_startup.py setup

# Manual commands
python auto_startup.py install    # Configure auto-startup
python auto_startup.py status     # Check current status  
python auto_startup.py uninstall  # Remove auto-startup
python auto_startup.py shortcut   # Create desktop shortcut
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
- **`tray_app.py`** - Main tray application with embedded server

## �📊 Monitoring & Health Checks

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

### Tray Application
- **System Tray Icon** - Quick access to server controls
- **GUI Interface** - User-friendly management interface  
- **Single Instance** - Prevents multiple server instances
- **Auto-start** - Optional automatic startup

## 🔧 Development

### Project Structure
```
Label-print-server/
├── app.py                 # Main Flask application
├── wsgi.py               # Production WSGI server
├── service_manager.py    # Windows service management
├── tray_app.py          # System tray application
├── tray_gui.py          # GUI management interface
├── printed_db.py        # Print history database
├── templates/
│   └── index.html       # Web interface template
├── logs/                # Application logs
├── icons/              # Application icons
└── .venv/              # Python virtual environment
```

### Database Schema
The application expects this SQL Server schema:

```sql
-- Transaction records
Tran2 (
    VchNo VARCHAR(25),      -- Formatted as "                   G-9171"
    VchType VARCHAR(2),     -- '26' for quotations
    MasterCode2 VARCHAR(3), -- '201' 
    CM1 VARCHAR(10)         -- Customer master code
)

-- Customer master
Master1 (
    Code VARCHAR(10),       -- Customer code
    Name VARCHAR(100),      -- Customer name
    MasterType INT          -- 2 for shops
)

-- Customer addresses  
MasterAddressInfo (
    MasterCode VARCHAR(10), -- Links to Master1.Code
    Address1 VARCHAR(100),
    Address2 VARCHAR(100), 
    Address3 VARCHAR(100),
    Address4 VARCHAR(100),
    Telno VARCHAR(20),
    Mobile VARCHAR(20)
)
```

### API Endpoints
- `GET /` - Web interface
- `POST /lookup` - Customer lookup by quotation number
- `POST /print` - Print label
- `GET /printed-records` - Print history
- `GET /get-settings` - Current configuration
- `POST /save-settings` - Update configuration  
- `POST /test-connection` - Database connectivity test
- `GET /health` - Health check
- `GET /metrics` - Application metrics

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
- **Python 3.8+**
- **SQL Server** (any supported version)
- **Network Printer** (optional, can use local printers)

### Dependencies
- Flask (web framework)
- pyodbc (SQL Server connectivity)
- waitress (production WSGI server)
- pywin32 (Windows integration)
- pystray (system tray functionality)
- Pillow (image processing)

## 📄 License

This project is proprietary software. All rights reserved.

## 🤝 Support

For support, configuration assistance, or deployment help:
1. Check the logs in `logs/` directory
2. Use health check endpoints for diagnostics
3. Review the troubleshooting section
4. Contact your system administrator

---

**Label Print Server** - Enterprise-grade customer label printing solution.