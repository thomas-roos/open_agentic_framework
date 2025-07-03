# Backup & Restore Functionality

The Agentic AI Framework includes comprehensive backup and restore functionality that allows you to export and import your agents, workflows, tools, scheduled tasks, and configuration settings.

## Features

- **Complete System Backup**: Export agents, workflows, tools, scheduled tasks, and configuration
- **Selective Export**: Choose what to include in your backup
- **Memory Export**: Optionally include agent conversation history
- **Zip Compression**: Automatic zip file creation for easy storage and transfer
- **Web UI Integration**: Full backup management through the web interface
- **API Access**: Programmatic access to backup functionality
- **Import Validation**: Safe import with conflict resolution options
- **Dry Run Mode**: Test imports without making changes

## Web UI Usage

### Accessing Backup Management

1. Start the framework: `python main.py`
2. Open the web UI: `http://localhost:8000/ui`
3. Navigate to "Backup & Restore" in the sidebar

### Exporting a Backup

1. Click "Export Backup" button
2. Configure export options:
   - **Backup Name**: Optional custom name (uses timestamp if not provided)
   - **Include Memory**: Include agent conversation history
   - **Include Configuration**: Export system settings
   - **Include Tools**: Export tool definitions
   - **Include Scheduled Tasks**: Export scheduled tasks
   - **Create Zip**: Create compressed zip file
3. Click "Export Backup"
4. The backup will be created and appear in the backups list

### Importing a Backup

1. Click "Import Backup" button
2. Select a backup file (zip or directory)
3. Configure import options:
   - **Import Agents**: Import agent definitions
   - **Import Workflows**: Import workflow definitions
   - **Import Tools**: Import tool definitions
   - **Import Scheduled Tasks**: Import scheduled tasks
   - **Import Memory**: Import agent conversation history
   - **Overwrite Existing**: Replace existing entities with same names
   - **Dry Run**: Test import without making changes
4. Click "Import Backup"

### Managing Backups

- **View Backups**: See all available backups with metadata
- **Download**: Download backup as zip file
- **Delete**: Remove unwanted backups
- **Refresh**: Update the backup list

## API Usage

### Export Backup

```bash
curl -X POST http://localhost:8000/backup/export \
  -H "Content-Type: application/json" \
  -d '{
    "export_path": "backups",
    "include_memory": false,
    "include_config": true,
    "include_tools": true,
    "include_scheduled_tasks": true,
    "create_zip": true,
    "backup_name": "my_backup"
  }'
```

### Import Backup

```bash
curl -X POST http://localhost:8000/backup/import \
  -F "file=@backup_file.zip" \
  -F 'options={"import_agents": true, "import_workflows": true, "overwrite_existing": false}'
```

### List Backups

```bash
curl http://localhost:8000/backup/list
```

### Download Backup

```bash
curl -O http://localhost:8000/backup/download/backup_name
```

### Delete Backup

```bash
curl -X DELETE http://localhost:8000/backup/delete/backup_name
```

## Backup Structure

Each backup contains the following files:

```
backup_name/
├── metadata.json          # Backup metadata and summary
├── agents.json            # Agent definitions and configurations
├── workflows.json         # Workflow definitions
├── tools.json             # Tool definitions
├── scheduled_tasks.json   # Scheduled task definitions
└── configuration.json     # System configuration (if included)
```

### Metadata File

The `metadata.json` file contains:

```json
{
  "backup_name": "backup_20241201_143022",
  "timestamp": "2024-12-01T14:30:22",
  "export_version": "1.0",
  "framework_version": "agentic_ai_framework",
  "includes": {
    "agents": true,
    "workflows": true,
    "tools": true,
    "scheduled_tasks": true,
    "configuration": true,
    "memory": false
  },
  "summary": {
    "agents": 3,
    "workflows": 2,
    "tools": 5,
    "scheduled_tasks": 1
  }
}
```

## Configuration

### Backup Directory

Backups are stored in the `backups/` directory by default. You can change this by:

1. Setting the `export_path` parameter in the export request
2. Modifying the `DEFAULT_BACKUP_DIR` in the web UI

### File Size Limits

- Maximum file upload size: 100MB (configurable)
- Recommended backup size: < 50MB for optimal performance

## Best Practices

### Regular Backups

- Create backups before major configuration changes
- Schedule regular backups using the scheduling system
- Keep multiple backup versions for rollback capability

### Backup Storage

- Store backups in a secure location
- Consider cloud storage for important backups
- Use descriptive backup names with timestamps

### Import Safety

- Always use dry run mode first for large imports
- Review import options carefully
- Test imports in a development environment first

### Memory Management

- Only include memory when necessary (increases backup size)
- Consider memory retention policies
- Clean up old memory entries regularly

## Troubleshooting

### Common Issues

**Import Fails with "Entity Already Exists"**
- Use `overwrite_existing: true` option
- Or delete existing entities first

**Backup File Too Large**
- Exclude memory from export
- Split large configurations into multiple backups
- Use compression (zip files)

**Import Validation Errors**
- Check backup file integrity
- Verify backup format compatibility
- Review error messages for specific issues

**Web UI Not Loading Backups**
- Check server is running
- Verify backup directory permissions
- Refresh the page

### Error Messages

- `"Backup not found"`: Backup file or directory doesn't exist
- `"Invalid backup format"`: Backup metadata is missing or corrupted
- `"Import failed"`: Check server logs for detailed error information
- `"Permission denied"`: Check file system permissions

## Security Considerations

- Backup files may contain sensitive configuration data
- Store backups securely with appropriate access controls
- Consider encryption for sensitive backups
- Regularly rotate backup storage credentials
- Validate backup integrity before restoration

## Migration Between Environments

When migrating between different environments:

1. Export complete backup with all components
2. Verify backup integrity
3. Import to target environment
4. Test functionality in new environment
5. Update environment-specific configurations if needed

## Support

For issues with backup functionality:

1. Check the server logs for error details
2. Verify backup file integrity
3. Test with a simple backup first
4. Review this documentation
5. Check the API documentation at `/docs` 