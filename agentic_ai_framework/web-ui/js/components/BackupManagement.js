// js/components/BackupManagement.js - Backup and Restore Management Component

const BackupManagement = () => {
    const { useState, useEffect } = React;

    const [backups, setBackups] = useState([]);
    const [loading, setLoading] = useState(false);
    const [exportModalOpen, setExportModalOpen] = useState(false);
    const [importModalOpen, setImportModalOpen] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [exportOptions, setExportOptions] = useState({
        export_path: 'backups',
        include_memory: false,
        include_config: true,
        include_tools: true,
        include_scheduled_tasks: true,
        create_zip: true,
        backup_name: ''
    });
    const [importOptions, setImportOptions] = useState({
        import_agents: true,
        import_workflows: true,
        import_tools: true,
        import_scheduled_tasks: true,
        import_memory: false,
        overwrite_existing: false,
        dry_run: false
    });

    // Load backups on component mount
    useEffect(() => {
        loadBackups();
    }, []);

    const loadBackups = async () => {
        try {
            setLoading(true);
            const response = await fetch('/backup/list');
            const data = await response.json();
            setBackups(data.backups || []);
        } catch (error) {
            console.error('Error loading backups:', error);
            showNotification('Error loading backups', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        try {
            setLoading(true);
            const response = await fetch('/backup/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(exportOptions)
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                showNotification('Backup exported successfully!', 'success');
                setExportModalOpen(false);
                loadBackups(); // Refresh the list
            } else {
                showNotification(`Export failed: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Export error:', error);
            showNotification('Export failed', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleImport = async () => {
        if (!selectedFile) {
            showNotification('Please select a backup file', 'error');
            return;
        }

        try {
            setLoading(true);
            
            // Create FormData for file upload
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            // Add import options as JSON string
            formData.append('options', JSON.stringify(importOptions));

            const response = await fetch('/backup/import', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.status === 'success' || result.status === 'dry_run_completed') {
                const message = result.status === 'dry_run_completed' 
                    ? 'Dry run completed successfully!' 
                    : 'Backup imported successfully!';
                showNotification(message, 'success');
                setImportModalOpen(false);
                setSelectedFile(null);
            } else {
                showNotification(`Import failed: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Import error:', error);
            showNotification('Import failed', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleFileSelect = (event) => {
        const file = event.target.files[0];
        setSelectedFile(file);
    };

    const downloadBackup = async (backup) => {
        try {
            const response = await fetch(`/backup/download/${backup.name}`);
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${backup.name}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Download error:', error);
            showNotification('Download failed', 'error');
        }
    };

    const deleteBackup = async (backupName) => {
        if (!confirm(`Are you sure you want to delete backup "${backupName}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/backup/delete/${backupName}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                showNotification('Backup deleted successfully', 'success');
                loadBackups();
            } else {
                showNotification('Failed to delete backup', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            showNotification('Delete failed', 'error');
        }
    };

    const showNotification = (message, type = 'info') => {
        // Simple notification - you can enhance this with a proper notification system
        alert(`${type.toUpperCase()}: ${message}`);
    };

    const formatDate = (timestamp) => {
        return new Date(timestamp).toLocaleString();
    };

    return React.createElement('div', { className: 'backup-management' }, [
        // Header
        React.createElement('div', { 
            key: 'header',
            className: 'page-header' 
        }, [
            React.createElement('h2', { key: 'title' }, 'Backup & Restore'),
            React.createElement('p', { key: 'description' }, 
                'Export and import your agents, workflows, and configuration settings'
            ),
            React.createElement('div', { 
                key: 'actions',
                className: 'header-actions' 
            }, [
                React.createElement('button', {
                    key: 'export',
                    className: 'btn btn-primary',
                    onClick: () => setExportModalOpen(true),
                    disabled: loading
                }, [
                    React.createElement('i', { key: 'icon', className: 'fas fa-download' }),
                    ' Export Backup'
                ]),
                React.createElement('button', {
                    key: 'import',
                    className: 'btn btn-secondary',
                    onClick: () => setImportModalOpen(true),
                    disabled: loading
                }, [
                    React.createElement('i', { key: 'icon', className: 'fas fa-upload' }),
                    ' Import Backup'
                ]),
                React.createElement('button', {
                    key: 'refresh',
                    className: 'btn btn-outline',
                    onClick: loadBackups,
                    disabled: loading
                }, [
                    React.createElement('i', { key: 'icon', className: 'fas fa-sync-alt' }),
                    ' Refresh'
                ])
            ])
        ]),

        // Backups List
        React.createElement('div', { 
            key: 'backups-list',
            className: 'backups-list' 
        }, [
            React.createElement('h3', { key: 'title' }, 'Available Backups'),
            
            loading ? React.createElement('div', { 
                key: 'loading',
                className: 'loading-state' 
            }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-spinner fa-spin' }),
                ' Loading backups...'
            ]) : backups.length === 0 ? React.createElement('div', { 
                key: 'empty',
                className: 'empty-state' 
            }, [
                React.createElement('i', { key: 'icon', className: 'fas fa-archive' }),
                React.createElement('h4', { key: 'title' }, 'No backups found'),
                React.createElement('p', { key: 'description' }, 
                    'Create your first backup to get started'
                )
            ]) : React.createElement('div', { 
                key: 'backups-grid',
                className: 'backups-grid' 
            }, backups.map(backup => 
                React.createElement('div', {
                    key: backup.name,
                    className: 'backup-card'
                }, [
                    React.createElement('div', { 
                        key: 'header',
                        className: 'backup-header' 
                    }, [
                        React.createElement('h4', { key: 'name' }, backup.name),
                        React.createElement('span', { 
                            key: 'type',
                            className: `backup-type ${backup.type}` 
                        }, backup.type)
                    ]),
                    
                    React.createElement('div', { 
                        key: 'metadata',
                        className: 'backup-metadata' 
                    }, [
                        React.createElement('p', { key: 'timestamp' }, 
                            `Created: ${formatDate(backup.metadata?.timestamp || 'Unknown')}`
                        ),
                        React.createElement('p', { key: 'summary' }, 
                            `Backup: ${backup.metadata?.backup_name || backup.name}, ` +
                            `Version: ${backup.metadata?.version || 'Unknown'}`
                        )
                    ]),
                    
                    React.createElement('div', { 
                        key: 'actions',
                        className: 'backup-actions' 
                    }, [
                        React.createElement('button', {
                            key: 'download',
                            className: 'btn btn-sm btn-outline',
                            onClick: () => downloadBackup(backup),
                            title: 'Download backup'
                        }, React.createElement('i', { className: 'fas fa-download' })),
                        React.createElement('button', {
                            key: 'import',
                            className: 'btn btn-sm btn-primary',
                            onClick: () => {
                                setSelectedFile({ name: backup.name, path: backup.path });
                                setImportModalOpen(true);
                            },
                            title: 'Import this backup'
                        }, React.createElement('i', { className: 'fas fa-upload' })),
                        React.createElement('button', {
                            key: 'delete',
                            className: 'btn btn-sm btn-danger',
                            onClick: () => deleteBackup(backup.name),
                            title: 'Delete backup'
                        }, React.createElement('i', { className: 'fas fa-trash' }))
                    ])
                ])
            ))
        ]),

        // Export Modal
        exportModalOpen && React.createElement('div', {
            key: 'export-modal',
            className: 'modal-overlay'
        }, [
            React.createElement('div', { 
                key: 'modal',
                className: 'modal' 
            }, [
                React.createElement('div', { 
                    key: 'header',
                    className: 'modal-header' 
                }, [
                    React.createElement('h3', { key: 'title' }, 'Export Backup'),
                    React.createElement('button', {
                        key: 'close',
                        className: 'modal-close',
                        onClick: () => setExportModalOpen(false)
                    }, React.createElement('i', { className: 'fas fa-times' }))
                ]),
                
                React.createElement('div', { 
                    key: 'body',
                    className: 'modal-body' 
                }, [
                    React.createElement('div', { key: 'form' }, [
                        React.createElement('div', { key: 'name', className: 'form-group' }, [
                            React.createElement('label', { key: 'label' }, 'Backup Name'),
                            React.createElement('input', {
                                key: 'input',
                                type: 'text',
                                value: exportOptions.backup_name,
                                onChange: (e) => setExportOptions({
                                    ...exportOptions,
                                    backup_name: e.target.value
                                }),
                                placeholder: 'Enter backup name (optional)'
                            })
                        ]),
                        
                        React.createElement('div', { key: 'options', className: 'form-group' }, [
                            React.createElement('label', { key: 'label' }, 'Export Options'),
                            React.createElement('div', { key: 'checkboxes', className: 'checkbox-group' }, [
                                React.createElement('label', { key: 'memory' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: exportOptions.include_memory,
                                        onChange: (e) => setExportOptions({
                                            ...exportOptions,
                                            include_memory: e.target.checked
                                        })
                                    }),
                                    ' Include agent memory/conversation history'
                                ]),
                                React.createElement('label', { key: 'config' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: exportOptions.include_config,
                                        onChange: (e) => setExportOptions({
                                            ...exportOptions,
                                            include_config: e.target.checked
                                        })
                                    }),
                                    ' Include system configuration'
                                ]),
                                React.createElement('label', { key: 'tools' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: exportOptions.include_tools,
                                        onChange: (e) => setExportOptions({
                                            ...exportOptions,
                                            include_tools: e.target.checked
                                        })
                                    }),
                                    ' Include tool definitions'
                                ]),
                                React.createElement('label', { key: 'tasks' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: exportOptions.include_scheduled_tasks,
                                        onChange: (e) => setExportOptions({
                                            ...exportOptions,
                                            include_scheduled_tasks: e.target.checked
                                        })
                                    }),
                                    ' Include scheduled tasks'
                                ]),
                                React.createElement('label', { key: 'zip' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: exportOptions.create_zip,
                                        onChange: (e) => setExportOptions({
                                            ...exportOptions,
                                            create_zip: e.target.checked
                                        })
                                    }),
                                    ' Create zip file'
                                ])
                            ])
                        ])
                    ])
                ]),
                
                React.createElement('div', { 
                    key: 'footer',
                    className: 'modal-footer' 
                }, [
                    React.createElement('button', {
                        key: 'cancel',
                        className: 'btn btn-secondary',
                        onClick: () => setExportModalOpen(false)
                    }, 'Cancel'),
                    React.createElement('button', {
                        key: 'export',
                        className: 'btn btn-primary',
                        onClick: handleExport,
                        disabled: loading
                    }, loading ? 'Exporting...' : 'Export Backup')
                ])
            ])
        ]),

        // Import Modal
        importModalOpen && React.createElement('div', {
            key: 'import-modal',
            className: 'modal-overlay'
        }, [
            React.createElement('div', { 
                key: 'modal',
                className: 'modal' 
            }, [
                React.createElement('div', { 
                    key: 'header',
                    className: 'modal-header' 
                }, [
                    React.createElement('h3', { key: 'title' }, 'Import Backup'),
                    React.createElement('button', {
                        key: 'close',
                        className: 'modal-close',
                        onClick: () => setImportModalOpen(false)
                    }, React.createElement('i', { className: 'fas fa-times' }))
                ]),
                
                React.createElement('div', { 
                    key: 'body',
                    className: 'modal-body' 
                }, [
                    React.createElement('div', { key: 'form' }, [
                        React.createElement('div', { key: 'file', className: 'form-group' }, [
                            React.createElement('label', { key: 'label' }, 'Backup File'),
                            selectedFile ? React.createElement('div', { 
                                key: 'selected',
                                className: 'file-selected' 
                            }, [
                                React.createElement('i', { key: 'icon', className: 'fas fa-file-archive' }),
                                React.createElement('span', { key: 'name' }, selectedFile.name),
                                React.createElement('button', {
                                    key: 'remove',
                                    className: 'btn btn-sm btn-danger',
                                    onClick: () => setSelectedFile(null)
                                }, React.createElement('i', { className: 'fas fa-times' }))
                            ]) : React.createElement('input', {
                                key: 'input',
                                type: 'file',
                                accept: '.zip,.json',
                                onChange: handleFileSelect
                            })
                        ]),
                        
                        React.createElement('div', { key: 'options', className: 'form-group' }, [
                            React.createElement('label', { key: 'label' }, 'Import Options'),
                            React.createElement('div', { key: 'checkboxes', className: 'checkbox-group' }, [
                                React.createElement('label', { key: 'agents' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: importOptions.import_agents,
                                        onChange: (e) => setImportOptions({
                                            ...importOptions,
                                            import_agents: e.target.checked
                                        })
                                    }),
                                    ' Import agents'
                                ]),
                                React.createElement('label', { key: 'workflows' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: importOptions.import_workflows,
                                        onChange: (e) => setImportOptions({
                                            ...importOptions,
                                            import_workflows: e.target.checked
                                        })
                                    }),
                                    ' Import workflows'
                                ]),
                                React.createElement('label', { key: 'tools' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: importOptions.import_tools,
                                        onChange: (e) => setImportOptions({
                                            ...importOptions,
                                            import_tools: e.target.checked
                                        })
                                    }),
                                    ' Import tools'
                                ]),
                                React.createElement('label', { key: 'tasks' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: importOptions.import_scheduled_tasks,
                                        onChange: (e) => setImportOptions({
                                            ...importOptions,
                                            import_scheduled_tasks: e.target.checked
                                        })
                                    }),
                                    ' Import scheduled tasks'
                                ]),
                                React.createElement('label', { key: 'memory' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: importOptions.import_memory,
                                        onChange: (e) => setImportOptions({
                                            ...importOptions,
                                            import_memory: e.target.checked
                                        })
                                    }),
                                    ' Import agent memory'
                                ]),
                                React.createElement('label', { key: 'overwrite' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: importOptions.overwrite_existing,
                                        onChange: (e) => setImportOptions({
                                            ...importOptions,
                                            overwrite_existing: e.target.checked
                                        })
                                    }),
                                    ' Overwrite existing entities'
                                ]),
                                React.createElement('label', { key: 'dry-run' }, [
                                    React.createElement('input', {
                                        key: 'input',
                                        type: 'checkbox',
                                        checked: importOptions.dry_run,
                                        onChange: (e) => setImportOptions({
                                            ...importOptions,
                                            dry_run: e.target.checked
                                        })
                                    }),
                                    ' Dry run (don\'t actually import)'
                                ])
                            ])
                        ])
                    ])
                ]),
                
                React.createElement('div', { 
                    key: 'footer',
                    className: 'modal-footer' 
                }, [
                    React.createElement('button', {
                        key: 'cancel',
                        className: 'btn btn-secondary',
                        onClick: () => setImportModalOpen(false)
                    }, 'Cancel'),
                    React.createElement('button', {
                        key: 'import',
                        className: 'btn btn-primary',
                        onClick: handleImport,
                        disabled: loading || !selectedFile
                    }, loading ? 'Importing...' : 'Import Backup')
                ])
            ])
        ])
    ]);
};

// Make component globally available
window.BackupManagement = BackupManagement; 