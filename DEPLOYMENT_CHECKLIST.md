# Production Deployment Checklist

## Pre-Deployment Requirements

### System Requirements
- [ ] **Windows 10/11** or **Windows Server 2016+**
- [ ] **Python 3.8+** installed and accessible
- [ ] **SQL Server** accessible from deployment machine
- [ ] **Network connectivity** to database server
- [ ] **Administrator privileges** for service installation
- [ ] **Printer access** (local or network printers)

### Software Dependencies
- [ ] **Git** for repository management
- [ ] **NSSM** (Non-Sucking Service Manager) for Windows services
- [ ] **Visual C++ Redistributable** for Python ODBC drivers
- [ ] **SQL Server ODBC drivers** (preferably Driver 18)

---

## Installation Steps

### 1. Repository Setup
- [ ] Clone repository to deployment location
- [ ] Navigate to project directory
- [ ] Verify all core files are present:
  - [ ] `app.py` (main application)
  - [ ] `wsgi.py` (production server)
  - [ ] `service_manager.py` (service management)
  - [ ] `requirements.txt` (dependencies)
  - [ ] `templates/index.html` (web interface)

### 2. Python Environment
```bash
# Create virtual environment
- [ ] python -m venv .venv

# Activate virtual environment  
- [ ] .venv\Scripts\activate

# Install dependencies
- [ ] pip install -r requirements.txt

# Verify installation
- [ ] python -c "import flask, pyodbc, waitress; print('Dependencies OK')"
```

### 3. Configuration Setup
- [ ] Copy `.env.production` to `.env`
- [ ] Edit `.env` file with production settings:
  - [ ] `DB_SERVER=your-sql-server`
  - [ ] `DB_NAME=your-database-name`
  - [ ] `SECRET_KEY=generate-secure-random-key`
  - [ ] `LOG_LEVEL=INFO`
  - [ ] `FLASK_ENV=production`

### 4. Database Configuration
- [ ] Verify SQL Server is accessible
- [ ] Test Windows Authentication works
- [ ] Confirm required tables exist:
  - [ ] `Tran2` (transaction records)
  - [ ] `Master1` (customer master)
  - [ ] `MasterAddressInfo` (customer addresses)
- [ ] Test database connection manually

---

## Service Installation

### 1. Install NSSM
```powershell
# Option 1: Chocolatey (if available)
- [ ] choco install nssm

# Option 2: Manual download
- [ ] Download from https://nssm.cc/download
- [ ] Extract to PATH or project directory
- [ ] Verify: nssm version
```

### 2. Install Label Print Server Service
```powershell
- [ ] python service_manager.py install
- [ ] Verify no errors in installation output
- [ ] Check Windows Services for "LabelPrintServer"
```

### 3. Configure Service
- [ ] Set service to automatic startup
- [ ] Configure service recovery options
- [ ] Set appropriate service account (if needed)
- [ ] Verify log directory permissions

---

## First Startup & Testing

### 1. Start Service
```powershell
- [ ] python service_manager.py start
- [ ] python service_manager.py status
- [ ] Verify status shows "SERVICE_RUNNING"
```

### 2. Basic Connectivity Tests
- [ ] **Health Check**: `http://localhost:5000/health`
- [ ] **Web Interface**: `http://localhost:5000`
- [ ] **Metrics**: `http://localhost:5000/metrics`
- [ ] Verify all endpoints return valid responses

### 3. Database Testing
- [ ] Open web interface settings (⚙️ button)
- [ ] Click "🔍 Test Connection" button
- [ ] Verify successful database connection
- [ ] Test customer lookup with known quotation

### 4. Label Printing Test
- [ ] Enter test quotation number
- [ ] Verify customer information appears
- [ ] Test label printing functionality
- [ ] Confirm print job reaches printer

---

## Security Configuration

### 1. Firewall Rules
```powershell
# Allow inbound connections on port 5000
- [ ] netsh advfirewall firewall add rule name="Label Print Server" dir=in action=allow protocol=TCP localport=5000

# Or restrict to specific networks
- [ ] Configure firewall for specific IP ranges only
```

### 2. Network Access
- [ ] Determine required network access (local only vs network)
- [ ] Configure appropriate network restrictions
- [ ] Test access from client machines (if needed)
- [ ] Verify security headers in HTTP responses

### 3. Service Account (Optional)
- [ ] Create dedicated service account (if required)
- [ ] Grant necessary permissions:
  - [ ] Database access
  - [ ] Printer access
  - [ ] Log directory write permissions
  - [ ] Application directory read permissions

---

## Monitoring Setup

### 1. Log Configuration
- [ ] Verify `logs/` directory exists and is writable
- [ ] Configure log retention policies
- [ ] Set up log monitoring (if required)
- [ ] Test log rotation functionality

### 2. Health Monitoring
- [ ] Configure health check monitoring system
- [ ] Set up alerts for service failures
- [ ] Configure metrics collection (if required)
- [ ] Test monitoring system integration

### 3. Performance Monitoring
- [ ] Baseline performance metrics
- [ ] Configure slow query alerts
- [ ] Set up disk space monitoring for logs
- [ ] Monitor database connection health

---

## Post-Deployment Verification

### 1. Functional Testing
- [ ] **Customer Lookup**: Test with multiple quotation numbers
- [ ] **Label Printing**: Verify all printer configurations work
- [ ] **Settings Management**: Test configuration changes
- [ ] **Error Handling**: Test with invalid inputs
- [ ] **Print History**: Verify tracking works correctly

### 2. Performance Testing
- [ ] **Load Testing**: Multiple concurrent requests
- [ ] **Database Performance**: Query response times
- [ ] **Memory Usage**: Monitor for memory leaks
- [ ] **Service Recovery**: Test service restart scenarios

### 3. Security Testing
- [ ] **Input Validation**: Test with malicious inputs
- [ ] **Error Messages**: Verify no sensitive info exposure
- [ ] **Network Access**: Test unauthorized access attempts
- [ ] **Log Security**: Verify logs don't contain credentials

---

## Maintenance Procedures

### 1. Regular Maintenance
- [ ] **Weekly**: Check service status and logs
- [ ] **Monthly**: Review log file sizes and cleanup
- [ ] **Quarterly**: Update dependencies and security patches
- [ ] **Annually**: Review and update configuration

### 2. Backup Procedures
- [ ] **Configuration**: Backup `.env` and `db_settings.json`
- [ ] **Print History**: Backup `printed_records.db`
- [ ] **Logs**: Archive important log files
- [ ] **Application**: Backup entire application directory

### 3. Update Procedures
- [ ] **Service Stop**: `python service_manager.py stop`
- [ ] **Code Update**: Update application files
- [ ] **Dependencies**: Update Python packages if needed
- [ ] **Service Start**: `python service_manager.py start`
- [ ] **Verification**: Run full testing checklist

---

## Troubleshooting Resources

### 1. Log Locations
- [ ] **Application Logs**: `logs/label_print_server.log`
- [ ] **Error Logs**: `logs/errors.log`
- [ ] **Database Logs**: `logs/database.log`
- [ ] **Access Logs**: `logs/access.log`
- [ ] **Service Logs**: `logs/service_stdout.log`, `logs/service_stderr.log`

### 2. Service Management
```powershell
- [ ] python service_manager.py status    # Check status
- [ ] python service_manager.py logs      # View recent logs
- [ ] python service_manager.py restart   # Restart service
- [ ] nssm status LabelPrintServer        # Direct NSSM status
```

### 3. Common Issues
- [ ] **Database Connection**: Use Test Connection feature
- [ ] **Service Won't Start**: Check service logs
- [ ] **Print Failures**: Verify printer configuration
- [ ] **Permission Issues**: Check service account permissions
- [ ] **Network Issues**: Verify firewall and network configuration

---

## Emergency Procedures

### 1. Service Recovery
```powershell
# If service fails to start
- [ ] Check Windows Event Viewer
- [ ] Review service error logs
- [ ] Restart with manual server: python wsgi.py
- [ ] Reinstall service if necessary
```

### 2. Database Recovery
- [ ] Test database connectivity outside application
- [ ] Verify SQL Server service is running
- [ ] Check Windows Authentication credentials
- [ ] Use alternative connection string if needed

### 3. Rollback Procedures
- [ ] Stop current service
- [ ] Restore backup configuration
- [ ] Restore previous application version
- [ ] Restart service and verify functionality

---

## Sign-off Checklist

### Technical Verification
- [ ] All services running correctly
- [ ] Database connectivity confirmed
- [ ] Label printing tested and working
- [ ] Monitoring systems operational
- [ ] Security configurations applied
- [ ] Performance metrics baseline established

### Documentation
- [ ] Deployment documented with specifics
- [ ] Administrator credentials recorded securely
- [ ] Maintenance procedures communicated
- [ ] Support contacts established
- [ ] Troubleshooting guide available

### Stakeholder Approval
- [ ] **Technical Lead**: System functionality verified
- [ ] **Operations**: Monitoring and maintenance approved
- [ ] **Security**: Security requirements met
- [ ] **End Users**: Training completed and system accepted

---

**Deployment Date**: ________________  
**Deployed By**: ____________________  
**Approved By**: ____________________  

*Keep this checklist for future reference and updates*