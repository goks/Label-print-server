# API Documentation - Label Print Server

## Overview
The Label Print Server provides a RESTful API for customer lookup, label printing, configuration management, and system monitoring.

## Base URL
```
http://localhost:5000
```

## Authentication
The API uses session-based authentication. No explicit authentication required for local network access.

---

## Endpoints

### 1. Web Interface

#### Get Main Interface
```http
GET /
```

**Description**: Serves the main web interface for the Label Print Server.

**Response**: HTML page with the label printing interface.

---

### 2. Customer Lookup

#### Lookup Customer by Quotation
```http
POST /lookup
Content-Type: application/json
```

**Request Body**:
```json
{
  "quotation": "9171"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "party": {
    "name": "ABC Corporation",
    "code": "CUST001", 
    "address1": "123 Business St",
    "address2": "Suite 456", 
    "address3": "Business District",
    "address4": "Metro City",
    "phone": "555-0123",
    "mobile": "555-0456"
  }
}
```

**Error Response** (200 - No Match):
```json
{
  "success": false,
  "error": "No customer found for quotation 9171"
}
```

**Database Error** (200):
```json
{
  "success": false,
  "error": "Database connection failed: Cannot reach SQL Server"
}
```

---

### 3. Label Printing

#### Print Customer Label
```http
POST /print  
Content-Type: application/json
```

**Request Body**:
```json
{
  "quotation": "9171",
  "party": {
    "name": "ABC Corporation",
    "code": "CUST001",
    "address1": "123 Business St",
    "address2": "Suite 456",
    "address3": "Business District", 
    "address4": "Metro City",
    "phone": "555-0123",
    "mobile": "555-0456"
  }
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Label printed successfully",
  "printer": "OneNote (Desktop)",
  "timestamp": "2025-10-22T17:00:00Z"
}
```

**Error Response** (200):
```json
{
  "success": false,
  "error": "Printer not available or print job failed"
}
```

---

### 4. Print History

#### Get Printed Records
```http
GET /printed-records?page=1&page_size=50
```

**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Records per page (default: 50, max: 100)

**Response** (200):
```json
{
  "records": [
    {
      "id": 1,
      "quotation": "9171",
      "customer_name": "ABC Corporation",
      "printed_at": "2025-10-22T17:00:00Z",
      "printer_name": "OneNote (Desktop)"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_records": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### 5. Configuration Management

#### Get Current Settings
```http
GET /get-settings
```

**Response** (200):
```json
{
  "server": "GASERVER\\BUSYSTDSQL",
  "database": "BusyComp0004_db12025", 
  "printer": "OneNote (Desktop)",
  "bartender_template": "C:\\Templates\\label.btw"
}
```

#### Save Settings
```http
POST /save-settings
Content-Type: application/json
```

**Request Body**:
```json
{
  "server": "GASERVER\\BUSYSTDSQL",
  "database": "BusyComp0004_db12025",
  "printer": "OneNote (Desktop)", 
  "bartender_template": "C:\\Templates\\label.btw"
}
```

**Success Response** (200):
```json
{
  "success": true
}
```

**Error Response** (200):
```json
{
  "success": false,
  "error": "Database connection failed: Server not found"
}
```

---

### 6. Database Testing

#### Test Database Connection
```http
POST /test-connection
Content-Type: application/json
```

**Request Body**:
```json
{
  "server": "GASERVER\\BUSYSTDSQL",
  "database": "BusyComp0004_db12025"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "driver": "ODBC Driver 18 for SQL Server",
  "version": "Microsoft SQL Server 2019",
  "tables_found": "3/3 required tables",
  "message": "Successfully connected using ODBC Driver 18 for SQL Server"
}
```

**Error Response** (200):
```json
{
  "success": false,
  "error": "Unable to connect to SQL Server GASERVER\\BUSYSTDSQL",
  "available_drivers": ["SQL Server", "ODBC Driver 18 for SQL Server"],
  "test_results": [
    {
      "driver": "ODBC Driver 18 for SQL Server", 
      "success": false,
      "error": "Login failed for user"
    }
  ],
  "suggestions": [
    "Check if SQL Server is running",
    "Verify server name is correct", 
    "Ensure SQL Server allows remote connections"
  ]
}
```

---

### 7. System Monitoring

#### Health Check
```http
GET /health
```

**Healthy Response** (200):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-22T17:00:00Z",
  "version": "1.0.0",
  "environment": "production", 
  "uptime_seconds": 3600,
  "database": "connected",
  "printed_db": "connected"
}
```

**Degraded Response** (503):
```json
{
  "status": "degraded", 
  "timestamp": "2025-10-22T17:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600,
  "database": "disconnected",
  "printed_db": "connected"
}
```

**Unhealthy Response** (503):
```json
{
  "status": "unhealthy",
  "error": "Critical system error",
  "timestamp": "2025-10-22T17:00:00Z"
}
```

#### System Metrics
```http
GET /metrics
```

**Response** (200):
```json
{
  "timestamp": "2025-10-22T17:00:00Z",
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
      "modified": "2025-10-22T16:59:30"
    },
    "errors.log": {
      "size_bytes": 50000,
      "modified": "2025-10-22T16:45:00" 
    }
  },
  "system": {
    "platform": "nt",
    "python_version": "3.11.0"
  }
}
```

---

### 8. System Control

#### Get Available Printers
```http
GET /get-printers
```

**Response** (200):
```json
[
  "Default Printer",
  "OneNote (Desktop)", 
  "Microsoft Print to PDF",
  "Network Printer \\\\SERVER\\HP-LaserJet"
]
```

#### Server Control
```http
POST /control
Content-Type: application/json
```

**Request Body**:
```json
{
  "action": "shutdown",
  "token": "secure-token-here"
}
```

**Actions**:
- `shutdown` - Graceful server shutdown
- `start` - Signal server start (for tray integration)

**Success Response** (200):
```json
{
  "success": true,
  "message": "Complete shutdown requested"
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-10-22T17:00:00Z"
}
```

### HTTP Status Codes
- **200 OK** - Success (even for application-level errors)
- **400 Bad Request** - Invalid request format
- **404 Not Found** - Endpoint not found  
- **500 Internal Server Error** - Unexpected server error
- **503 Service Unavailable** - Health check failed

---

## Rate Limiting
No rate limiting implemented. Consider implementing for production use with high traffic.

## CORS Policy  
CORS headers not explicitly configured. Same-origin policy applies.

## Request/Response Headers

### Security Headers (All Responses)
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block  
Referrer-Policy: strict-origin-when-cross-origin
```

### Content Types
- **Request**: `application/json` for POST requests
- **Response**: `application/json` for API endpoints, `text/html` for web interface

---

## SDK/Client Examples

### JavaScript (Browser)
```javascript
// Customer lookup
async function lookupCustomer(quotation) {
  const response = await fetch('/lookup', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({quotation})
  });
  return await response.json();
}

// Health check
async function checkHealth() {
  const response = await fetch('/health');
  return await response.json(); 
}
```

### Python
```python
import requests

# Customer lookup
def lookup_customer(quotation):
    response = requests.post('http://localhost:5000/lookup', 
                           json={'quotation': quotation})
    return response.json()

# Health check  
def check_health():
    response = requests.get('http://localhost:5000/health')
    return response.json()
```

### PowerShell
```powershell
# Customer lookup
$body = @{quotation = "9171"} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:5000/lookup" `
                             -Method POST `
                             -Body $body `
                             -ContentType "application/json"

# Health check
$health = Invoke-RestMethod -Uri "http://localhost:5000/health"
```