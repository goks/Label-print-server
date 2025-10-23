# Update System Documentation

## Overview
The Label Print Server includes a comprehensive auto-update system that keeps your application current with the latest features and fixes from GitHub releases.

## Features

### ✅ Automatic Update Detection
- **Background Checking**: Automatically checks for updates in the background
- **Configurable Intervals**: Set how often to check (default: 24 hours)  
- **Force Checks**: Manually trigger immediate update checks
- **Version Comparison**: Intelligent semantic version comparison

### ✅ Flexible Update Channels
- **Stable**: Production releases only (recommended)
- **Beta**: Include pre-release versions for testing
- **All**: All releases including development builds

### ✅ Safe Installation Process
- **Automatic Backups**: Creates backup before installing updates
- **Rollback Support**: Restore previous version if update fails
- **Service Management**: Safely stops and restarts application services
- **Integrity Verification**: Validates downloaded files before installation

### ✅ Multiple Interfaces
- **GUI Management**: Full-featured graphical interface in tray app
- **CLI Tools**: Command-line interface for automation
- **Web API**: RESTful endpoints for remote management
- **Batch Scripts**: Windows batch files for easy access

## Configuration

### Update Settings
The update system can be configured through multiple methods:

#### 1. GUI Configuration (Recommended)
1. Right-click the system tray icon
2. Select "Open Settings"
3. Navigate to "Update Management" section
4. Configure your preferences:
   - **Auto-check updates**: Enable/disable background checking
   - **Check interval**: How often to check (1-168 hours)
   - **Include prereleases**: Whether to include beta versions
   - **Auto-install**: Automatically install stable updates

#### 2. Configuration File
Edit the update configuration directly:

```json
{
    "github_repo": "yourusername/label-print-server",
    "auto_check": true,
    "check_interval_hours": 24,
    "include_prereleases": false,
    "auto_install": false,
    "backup_enabled": true,
    "update_channel": "stable"
}
```

#### 3. Environment Variables
Set these environment variables for system-wide configuration:
- `GITHUB_REPO`: Repository to check for updates
- `AUTO_CHECK_UPDATES`: Enable auto-checking (true/false)  
- `UPDATE_CHANNEL`: Update channel (stable/beta/all)

## Usage

### GUI Interface
The system tray application provides the most user-friendly interface:

1. **View Current Version**: Displayed in the update section
2. **Check for Updates**: Click "Check for Updates" button
3. **Install Updates**: Click "Install Update" when available
4. **View Progress**: Real-time progress bars during download/install
5. **Configure Settings**: Access all update preferences

### Command Line Interface

#### Quick Commands
```batch
# Check for updates
update_cli.bat check

# Install available updates  
update_cli.bat install

# View current configuration
update_cli.bat config

# Show system status
update_cli.bat status
```

#### Advanced CLI Usage
```batch
# Force check (ignore cache)
python update_manager.py check --force

# Auto-install updates when found
python update_manager.py check --auto-install

# Change update channel
python update_manager.py check --channel beta

# Manual update installation
python update_manager.py update
```

### Web API Endpoints
For integration with other systems:

```http
GET /check-updates
POST /install-update  
GET /update-config
POST /update-config
```

## Update Process

### 1. Detection Phase
- Connects to GitHub API to fetch latest release information
- Compares remote version with current local version
- Respects update channel settings (stable/beta/all)
- Caches results to avoid API rate limiting

### 2. Download Phase  
- Downloads update package from GitHub releases
- Verifies file integrity and checksums
- Shows progress feedback to user
- Stores in temporary directory for safety

### 3. Installation Phase
- **Backup Creation**: Backs up current application files
- **Service Stop**: Gracefully stops running application
- **File Replacement**: Extracts and replaces application files
- **Service Start**: Restarts application with new version
- **Verification**: Confirms successful installation

### 4. Rollback (If Needed)
- Automatically triggered if installation fails
- Restores previous version from backup
- Restarts application with original version
- Logs rollback details for troubleshooting

## Troubleshooting

### Common Issues

#### Update Check Fails
```
Problem: Cannot connect to GitHub
Solutions:
- Check internet connection
- Verify firewall settings allow GitHub access
- Check if GitHub API rate limit exceeded
- Ensure repository URL is correct
```

#### Download Fails
```
Problem: Update download interrupted
Solutions:  
- Check available disk space
- Verify write permissions to application directory
- Check antivirus software isn't blocking downloads
- Try manual download with force flag
```

#### Installation Fails
```
Problem: Update installation incomplete
Solutions:
- Ensure application is not running during update
- Check file permissions in application directory
- Run as administrator if needed
- Check logs for specific error details
```

#### Backup/Restore Issues
```
Problem: Cannot create backup or restore fails
Solutions:
- Verify sufficient disk space for backup
- Check write permissions to backup directory  
- Manually backup important files before updating
- Contact support if restore is needed
```

### Log Files
Update operations are logged to:
- `logs/label_print_server.log` - General application logs
- `logs/update.log` - Update-specific operations
- `logs/error.log` - Error details and stack traces

### Recovery Options

#### Manual Rollback
If automatic rollback fails:
1. Stop the application
2. Navigate to backup directory
3. Copy backup files back to application directory
4. Restart application

#### Force Update
If updates are stuck:
```batch
# Clear update cache and force fresh check
python update_manager.py check --force

# Skip backup and force install (use with caution)
python update_manager.py update --no-backup
```

#### Reset Update System
To completely reset the update system:
1. Delete `update_cache.json`
2. Delete `update_config.json` 
3. Restart application
4. Reconfigure update settings

## Security Considerations

### Safe Practices
- **Verify Sources**: Only download from official GitHub repository
- **Check Signatures**: Verify file integrity before installation  
- **Backup Always**: Never skip backup creation
- **Test Environment**: Test updates in non-production environment first

### Network Security
- Updates use HTTPS connections to GitHub
- No sensitive data transmitted during update process
- API tokens not required for public repositories
- Respects corporate firewall and proxy settings

### File System Security
- Backup files stored securely with proper permissions
- Temporary files cleaned up after installation
- No modifications to system directories outside application folder

## Best Practices

### For Administrators
1. **Enable Auto-Updates**: For security patches and critical fixes
2. **Monitor Logs**: Review update logs regularly
3. **Test First**: Test updates in staging environment
4. **Backup Strategy**: Maintain separate backup system
5. **Network Planning**: Ensure GitHub access during business hours

### For Developers
1. **Semantic Versioning**: Use proper version numbers in releases
2. **Release Notes**: Provide clear changelog information
3. **Testing**: Test update process before publishing releases
4. **Communication**: Notify users of critical updates

### For End Users  
1. **Regular Updates**: Keep application current for security
2. **Backup Important Data**: Backup database settings and configurations
3. **Test Functionality**: Verify application works after updates
4. **Report Issues**: Report update problems promptly

## Integration Examples

### Scheduled Updates
Set up automated updates using Windows Task Scheduler:
```batch
# Create daily update check task
schtasks /create /tn "LabelPrint_UpdateCheck" /tr "C:\path\to\update_cli.bat check" /sc daily /st 02:00
```

### Monitoring Integration
Monitor update status via API:
```python
import requests
response = requests.get('http://localhost:5000/check-updates')
update_info = response.json()
```

### Custom Update Notifications
Send notifications when updates are available:
```python
from update_manager import UpdateManager
manager = UpdateManager()
result = manager.check_and_update()
if result['status'] == 'update_available':
    send_notification(f"Update {result['version']} available")
```

## Support

### Getting Help
- Check logs for error details
- Review this documentation
- Search GitHub issues for similar problems
- Contact support with log files and system information

### Reporting Issues
When reporting update issues, include:
- Current application version  
- Operating system version
- Error messages from logs
- Steps to reproduce the problem
- Network configuration details

### Contributing  
- Report bugs via GitHub issues
- Submit feature requests
- Contribute code improvements
- Help improve documentation