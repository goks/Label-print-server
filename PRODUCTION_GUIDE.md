# Label Print Server - Production Deployment Guide

## 🚀 Production Features Added

### ✅ Comprehensive Logging System
- **Multi-file logging** with automatic rotation
- **Separate logs** for application, errors, database, and access
- **Performance monitoring** with request timing
- **Structured logging** with request IDs for tracing

### ✅ Production Security
- **Security headers** (XSS protection, content-type sniffing, frame options)
- **Error handling** with safe error responses
- **Request size limits** to prevent abuse
- **Proxy support** for reverse proxy deployments

### ✅ Health Monitoring
- **Health check endpoint** (`/health`) for load balancers
- **Metrics endpoint** (`/metrics`) for monitoring systems
- **Database connectivity** checks
- **Uptime tracking** and system information

### ✅ Production Server Configuration
- **Waitress WSGI server** for production reliability
- **Multi-threading support** for concurrent requests
- **Connection pooling** and timeout management
- **Graceful error handling** and recovery

### ✅ Windows Service Integration
- **NSSM service manager** for Windows service installation
- **Automatic startup** on system boot
- **Log rotation** and management
- **Service control** commands

## 📋 Production Deployment Steps

### 1. Environment Setup

```powershell
# Navigate to project directory
cd "c:\Users\Gokul\Desktop\PROGRAM FILES\Label-print-server"

# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Install/update production dependencies
pip install -r requirements.txt
```

### 2. Configure Production Environment

Copy and customize the production configuration:
```powershell
# Copy production environment template
copy .env.production .env

# Edit configuration (use your preferred editor)
notepad .env
```

Key settings to configure:
- `SECRET_KEY`: Generate a secure random key
- `DB_SERVER`: Your SQL Server instance
- `DB_NAME`: Your database name
- `LOG_LEVEL`: INFO for production, DEBUG for troubleshooting

### 3. Install NSSM (Non-Sucking Service Manager)

Download and install NSSM:
```powershell
# Option 1: Using Chocolatey (if installed)
choco install nssm

# Option 2: Manual installation
# Download from https://nssm.cc/download
# Extract nssm.exe to a folder in your PATH or project directory
```

### 4. Install as Windows Service

```powershell
# Install the service
python service_manager.py install

# Start the service
python service_manager.py start

# Check status
python service_manager.py status
```

### 5. Verify Production Deployment

Check that everything is working:

```powershell
# Health check
curl http://localhost:5000/health

# Web interface
# Open browser to http://localhost:5000

# Check logs
python service_manager.py logs
```

## 📊 Monitoring and Maintenance

### Log Files Location
All logs are stored in the `logs/` directory:
- `label_print_server.log` - Main application log (daily rotation)
- `errors.log` - Error-only log (size-based rotation)
- `database.log` - Database operations and performance
- `access.log` - Request/response logging
- `service_stdout.log` - Service standard output
- `service_stderr.log` - Service error output

### Health Check Endpoints

**Health Check**: `GET /health`
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-10-22T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600,
  "database": "connected|disconnected|not_configured",
  "printed_db": "connected|error"
}
```

**Metrics**: `GET /metrics`
```json
{
  "timestamp": "2025-10-22T10:30:00Z",
  "application": {
    "name": "Label Print Server",
    "version": "1.0.0",
    "environment": "production",
    "uptime_seconds": 3600
  },
  "database": {
    "server": "GASERVER\\BUSYSTDSQL",
    "database": "BusyComp0004_db12025",
    "configured": true
  },
  "logs": {
    "label_print_server.log": {
      "size_bytes": 1024000,
      "modified": "2025-10-22T10:29:30"
    }
  }
}
```

### Service Management Commands

```powershell
# Check service status
python service_manager.py status

# Start/stop service
python service_manager.py start
python service_manager.py stop
python service_manager.py restart

# View recent logs
python service_manager.py logs

# Uninstall service (if needed)
python service_manager.py uninstall
```

### Performance Tuning

Edit `.env` for production optimization:

```env
# Connection pooling
DATABASE_CONNECTION_TIMEOUT=30
REQUEST_TIMEOUT=60

# Threading (adjust based on server capacity)
THREADS=4
WORKERS=1

# Security
MAX_CONTENT_LENGTH=16777216  # 16MB max request

# Logging
LOG_LEVEL=INFO  # Use DEBUG only for troubleshooting
```

## 🔧 Production Troubleshooting

### Database Connection Issues
1. Check health endpoint: `curl http://localhost:5000/health`
2. Use test connection: Settings → Test Connection in web interface
3. Review database logs: `logs/database.log`
4. Verify SQL Server is running and accessible

### Service Issues
```powershell
# Check Windows Event Viewer
eventvwr.msc

# View service logs
python service_manager.py logs

# Check NSSM service status
nssm status LabelPrintServer
```

### Performance Issues
1. Monitor `logs/label_print_server.log` for slow request warnings
2. Check `logs/access.log` for request patterns
3. Review `/metrics` endpoint for system status
4. Consider adjusting thread count in configuration

### Log Management
- Logs rotate automatically (daily for app logs, size-based for errors)
- Old logs are kept for 30 days (application) and 90 days (access)
- Manual cleanup: `logs/` directory if disk space is low

## 🔒 Security Considerations

### Network Security
- **Firewall**: Open port 5000 only for required networks
- **Access Control**: Consider restricting access to local network
- **HTTPS**: Use reverse proxy (IIS/nginx) for HTTPS in production

### Application Security
- **Secret Key**: Use strong, unique SECRET_KEY in production
- **Input Validation**: All inputs are validated and sanitized
- **Error Handling**: Sensitive information is not exposed in errors
- **Logging**: Access patterns are logged for security monitoring

### Database Security
- **Windows Authentication**: Uses integrated Windows authentication
- **Connection Timeout**: Prevents hanging connections
- **Error Logging**: Database errors are logged but sanitized for responses

## 📈 Scaling Considerations

### Horizontal Scaling
- Deploy multiple instances behind a load balancer
- Use shared database and file storage
- Health checks support load balancer integration

### Performance Optimization
- **Connection pooling**: Enabled by default
- **Request caching**: Consider implementing for frequently accessed data
- **Static files**: Serve from web server (IIS/nginx) in production
- **Database indexing**: Ensure proper indexes on lookup tables

### Monitoring Integration
- Health and metrics endpoints support monitoring tools
- Structured logging compatible with log aggregation systems
- Performance metrics available for monitoring dashboards

## 🔄 Updates and Maintenance

### Application Updates
```powershell
# Stop service
python service_manager.py stop

# Update code (git pull, copy files, etc.)
git pull origin main

# Update dependencies if needed
pip install -r requirements.txt

# Start service
python service_manager.py start
```

### Database Maintenance
- Monitor database log for connection issues
- Review query performance in database logs
- Ensure database backup procedures are in place

This production setup provides enterprise-level reliability, monitoring, and maintainability for the Label Print Server.