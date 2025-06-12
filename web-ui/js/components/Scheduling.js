// js/components/Scheduling.js - Fixed timezone display

// Live Time Display Component
const LiveTimeDisplay = () => {
    const { useState, useEffect } = React;
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        // Update time every second
        const interval = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    const formatTimeDisplay = (date) => {
        const utcTime = date.toISOString();
        const localTime = date.toLocaleString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        
        return {
            utc: utcTime.slice(0, 19) + 'Z', // Format: 2024-01-15T14:30:25Z
            local: localTime,
            timezone: timezone
        };
    };

    const timeInfo = formatTimeDisplay(currentTime);

    return React.createElement('div', {
        style: {
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            fontSize: '11px',
            color: '#64748b',
            fontFamily: 'monospace',
            background: '#f8fafc',
            padding: '8px 12px',
            borderRadius: '6px',
            border: '1px solid #e2e8f0',
            minWidth: '200px'
        }
    }, [
        React.createElement('div', {
            key: 'utc-time',
            style: { 
                fontWeight: '600',
                marginBottom: '2px',
                color: '#374151'
            }
        }, [
            React.createElement('span', {
                key: 'label',
                style: { color: '#6b7280', marginRight: '6px' }
            }, 'UTC:'),
            timeInfo.utc
        ]),
        React.createElement('div', {
            key: 'local-time',
            style: { 
                fontWeight: '500',
                color: '#1f2937'
            }
        }, [
            React.createElement('span', {
                key: 'label',
                style: { color: '#6b7280', marginRight: '6px' }
            }, 'Local:'),
            timeInfo.local
        ]),
        React.createElement('div', {
            key: 'timezone',
            style: { 
                fontSize: '10px',
                marginTop: '2px',
                color: '#9ca3af'
            }
        }, `(${timeInfo.timezone})`)
    ]);
};

const Scheduling = () => {
    const { useState, useEffect } = React;

    const [scheduledTasks, setScheduledTasks] = useState([]);
    const [agents, setAgents] = useState([]);
    const [workflows, setWorkflows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingTask, setEditingTask] = useState(null);
    const [statistics, setStatistics] = useState(null);
    const [selectedTaskExecutions, setSelectedTaskExecutions] = useState(null);
    const [showExecutions, setShowExecutions] = useState(false);
    const [filterType, setFilterType] = useState('all'); // all, one-time, recurring, active, disabled

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [tasksData, agentsData, workflowsData, statsData] = await Promise.allSettled([
                api.getScheduledTasks(),
                api.getAgents(),
                api.getWorkflows(),
                api.getScheduleStatistics().catch(() => null) // Optional endpoint
            ]);

            setScheduledTasks(tasksData.status === 'fulfilled' ? tasksData.value : []);
            setAgents(agentsData.status === 'fulfilled' ? agentsData.value : []);
            setWorkflows(workflowsData.status === 'fulfilled' ? workflowsData.value : []);
            setStatistics(statsData.status === 'fulfilled' ? statsData.value : null);
        } catch (error) {
            console.error('Failed to load scheduling data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateTask = () => {
        setEditingTask(null);
        setShowModal(true);
    };

    const handleEditTask = (task) => {
        setEditingTask(task);
        setShowModal(true);
    };

    const handleDeleteTask = async (taskId) => {
        if (!confirm('Are you sure you want to delete this scheduled task?')) return;

        try {
            await api.deleteScheduledTask(taskId);
            await loadData();
        } catch (error) {
            alert(`Failed to delete task: ${error.message}`);
        }
    };

    const handleToggleTask = async (taskId, currentEnabled) => {
        try {
            if (currentEnabled) {
                await api.disableScheduledTask(taskId);
            } else {
                await api.enableScheduledTask(taskId);
            }
            await loadData();
        } catch (error) {
            alert(`Failed to ${currentEnabled ? 'disable' : 'enable'} task: ${error.message}`);
        }
    };

    const handleViewExecutions = async (taskId) => {
        try {
            const executions = await api.getTaskExecutions(taskId, 20);
            setSelectedTaskExecutions(executions);
            setShowExecutions(true);
        } catch (error) {
            alert(`Failed to load execution history: ${error.message}`);
        }
    };

    const getTaskStatusBadge = (task) => {
        const { status, enabled, is_recurring } = task;
        
        if (!enabled) {
            return React.createElement('span', {
                className: 'status status-offline'
            }, 'Disabled');
        }
        
        if (is_recurring) {
            return React.createElement('span', {
                className: 'status status-online'
            }, 'Active');
        }
        
        const statusMap = {
            'pending': { class: 'status-warning', text: 'Pending' },
            'running': { class: 'status-online', text: 'Running' },
            'completed': { class: 'status-online', text: 'Completed' },
            'failed': { class: 'status-offline', text: 'Failed' }
        };
        
        const statusInfo = statusMap[status] || { class: 'status-warning', text: status };
        return React.createElement('span', {
            className: `status ${statusInfo.class}`
        }, statusInfo.text);
    };

    // FIXED: Proper timezone-aware date formatting
    const formatDateTime = (dateString, options = {}) => {
        if (!dateString) return 'N/A';
        
        try {
            const utcDate = new Date(dateString);
            
            // Check if date is valid
            if (isNaN(utcDate.getTime())) {
                console.warn('Invalid date string:', dateString);
                return dateString;
            }
            
            // Format options
            const formatOptions = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: true,
                ...options
            };
            
            // Convert UTC to local time and format
            const localString = utcDate.toLocaleString(undefined, formatOptions);
            
            // Add timezone info if requested
            if (options.showTimezone) {
                const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                return `${localString} (${timezone})`;
            }
            
            return localString;
            
        } catch (error) {
            console.error('Error formatting date:', error, dateString);
            return dateString;
        }
    };

    // Enhanced date formatting with relative time
    const formatDateTimeWithRelative = (dateString) => {
        if (!dateString) return 'N/A';
        
        try {
            const utcDate = new Date(dateString);
            const now = new Date();
            const diffMs = utcDate.getTime() - now.getTime();
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMins / 60);
            const diffDays = Math.floor(diffHours / 24);
            
            let relativeText = '';
            if (Math.abs(diffMs) < 60000) { // Less than 1 minute
                relativeText = diffMs > 0 ? 'in <1min' : '<1min ago';
            } else if (Math.abs(diffMins) < 60) { // Less than 1 hour
                relativeText = diffMins > 0 ? `in ${diffMins}m` : `${Math.abs(diffMins)}m ago`;
            } else if (Math.abs(diffHours) < 24) { // Less than 1 day
                const mins = Math.abs(diffMins % 60);
                relativeText = diffHours > 0 ? 
                    `in ${diffHours}h ${mins}m` : 
                    `${Math.abs(diffHours)}h ${mins}m ago`;
            } else { // Days
                relativeText = diffDays > 0 ? `in ${diffDays}d` : `${Math.abs(diffDays)}d ago`;
            }
            
            const localString = formatDateTime(dateString);
            return `${localString} (${relativeText})`;
            
        } catch (error) {
            return formatDateTime(dateString);
        }
    };

    const isTaskOverdue = (scheduledTime, status, isRecurring) => {
        if (isRecurring || status !== 'pending') return false;
        try {
            return new Date(scheduledTime) < new Date();
        } catch {
            return false;
        }
    };

    const getFilteredTasks = () => {
        let filtered = scheduledTasks;
        
        switch (filterType) {
            case 'one-time':
                filtered = scheduledTasks.filter(task => !task.is_recurring);
                break;
            case 'recurring':
                filtered = scheduledTasks.filter(task => task.is_recurring);
                break;
            case 'active':
                filtered = scheduledTasks.filter(task => task.enabled);
                break;
            case 'disabled':
                filtered = scheduledTasks.filter(task => !task.enabled);
                break;
            default:
                // 'all' - no filtering
                break;
        }
        
        return filtered;
    };

    const getNextExecutionDisplay = (task) => {
        if (!task.is_recurring) return null;
        
        if (!task.enabled) return 'Disabled';
        if (!task.next_execution) return 'Not scheduled';
        
        const nextTime = new Date(task.next_execution);
        const now = new Date();
        
        if (nextTime <= now) return 'Due now';
        
        const diffMs = nextTime - now;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffDays > 0) return `in ${diffDays}d ${diffHours % 24}h`;
        if (diffHours > 0) return `in ${diffHours}h ${diffMins % 60}m`;
        return `in ${diffMins}m`;
    };

    if (loading) return React.createElement(Loading, { message: "Loading scheduled tasks..." });

    const filteredTasks = getFilteredTasks();

    return React.createElement('div', {}, [
        React.createElement('div', { 
            key: 'main-card',
            className: 'card' 
        }, [
            React.createElement('div', { 
                key: 'header',
                className: 'card-header' 
            }, [
                React.createElement('h3', { 
                    key: 'title',
                    className: 'card-title' 
                }, 'Scheduled Tasks'),
                React.createElement('div', {
                    key: 'actions',
                    style: { display: 'flex', gap: '8px' }
                }, [
                    React.createElement('button', {
                        key: 'refresh',
                        className: 'btn btn-secondary',
                        onClick: loadData,
                        title: 'Refresh'
                    }, React.createElement('i', { className: 'fas fa-refresh' })),
                    React.createElement('button', {
                        key: 'create',
                        className: 'btn btn-primary',
                        onClick: handleCreateTask
                    }, [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-plus' 
                        }),
                        ' Schedule Task'
                    ])
                ])
            ]),
            React.createElement('div', { 
                key: 'content',
                className: 'card-content' 
            }, [
                // Current Time Display (for reference)
                React.createElement('div', {
                    key: 'current-time',
                    style: {
                        padding: '8px 12px',
                        background: '#f8fafc',
                        borderRadius: '6px',
                        marginBottom: '16px',
                        fontSize: '12px',
                        color: '#64748b',
                        border: '1px solid #e2e8f0'
                    }
                }, [
                    React.createElement('i', {
                        key: 'icon',
                        className: 'fas fa-clock',
                        style: { marginRight: '6px' }
                    }),
                    `Current time: ${formatDateTime(new Date().toISOString(), { showTimezone: true })}`
                ]),

                // Task Filter Tabs with Time Display
                React.createElement('div', {
                    key: 'filters',
                    style: { 
                        marginBottom: '24px',
                        borderBottom: '1px solid #e2e8f0',
                        paddingBottom: '16px'
                    }
                }, [
                    React.createElement('div', {
                        key: 'filter-header',
                        style: { 
                            display: 'flex', 
                            justifyContent: 'space-between', 
                            alignItems: 'center',
                            marginBottom: '12px',
                            flexWrap: 'wrap',
                            gap: '16px'
                        }
                    }, [
                        React.createElement('div', {
                            key: 'filter-buttons',
                            style: { display: 'flex', gap: '8px', flexWrap: 'wrap' }
                        }, [
                            { key: 'all', label: 'All Tasks', count: scheduledTasks.length },
                            { key: 'one-time', label: 'One-time', count: scheduledTasks.filter(t => !t.is_recurring).length },
                            { key: 'recurring', label: 'Recurring', count: scheduledTasks.filter(t => t.is_recurring).length },
                            { key: 'active', label: 'Active', count: scheduledTasks.filter(t => t.enabled).length },
                            { key: 'disabled', label: 'Disabled', count: scheduledTasks.filter(t => !t.enabled).length }
                        ].map(filter => 
                            React.createElement('button', {
                                key: filter.key,
                                className: `btn ${filterType === filter.key ? 'btn-primary' : 'btn-secondary'}`,
                                onClick: () => setFilterType(filter.key),
                                style: { fontSize: '12px' }
                            }, `${filter.label} (${filter.count})`)
                        )),
                        
                        // Live Time Display
                        React.createElement(LiveTimeDisplay, { key: 'live-time' })
                    ])
                ]),

                // Statistics (if available)
                statistics && React.createElement('div', {
                    key: 'stats',
                    className: 'stats-grid',
                    style: { marginBottom: '24px' }
                }, [
                    React.createElement('div', { 
                        key: 'total',
                        className: 'stat-card' 
                    }, [
                        React.createElement('div', { 
                            key: 'value',
                            className: 'stat-value' 
                        }, statistics.total_tasks),
                        React.createElement('div', { 
                            key: 'label',
                            className: 'stat-label' 
                        }, 'Total Tasks')
                    ]),
                    React.createElement('div', { 
                        key: 'recurring',
                        className: 'stat-card' 
                    }, [
                        React.createElement('div', { 
                            key: 'value',
                            className: 'stat-value' 
                        }, statistics.active_recurring),
                        React.createElement('div', { 
                            key: 'label',
                            className: 'stat-label' 
                        }, 'Active Recurring')
                    ]),
                    React.createElement('div', { 
                        key: 'executions',
                        className: 'stat-card' 
                    }, [
                        React.createElement('div', { 
                            key: 'value',
                            className: 'stat-value' 
                        }, statistics.total_executions),
                        React.createElement('div', { 
                            key: 'label',
                            className: 'stat-label' 
                        }, 'Total Executions')
                    ]),
                    React.createElement('div', { 
                        key: 'success-rate',
                        className: 'stat-card' 
                    }, [
                        React.createElement('div', { 
                            key: 'value',
                            className: 'stat-value',
                            style: { color: statistics.successful_executions > statistics.failed_executions ? '#10b981' : '#ef4444' }
                        }, statistics.total_executions > 0 ? 
                            `${Math.round((statistics.successful_executions / statistics.total_executions) * 100)}%` : 
                            '0%'),
                        React.createElement('div', { 
                            key: 'label',
                            className: 'stat-label' 
                        }, 'Success Rate')
                    ])
                ]),

                filteredTasks.length === 0 ? 
                    React.createElement('div', {
                        key: 'empty',
                        className: 'empty-state'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-calendar-alt'
                        }),
                        React.createElement('h3', { key: 'title' }, 
                            filterType === 'all' ? 'No scheduled tasks' : `No ${filterType} tasks`),
                        React.createElement('p', { key: 'description' }, 
                            filterType === 'all' ? 
                                'Schedule your first agent or workflow to run automatically!' :
                                `Try switching to a different filter or create a new task.`),
                        filterType === 'all' && React.createElement('button', {
                            key: 'cta',
                            className: 'btn btn-primary',
                            onClick: handleCreateTask
                        }, [
                            React.createElement('i', { 
                                key: 'icon',
                                className: 'fas fa-plus' 
                            }),
                            ' Schedule Your First Task'
                        ])
                    ]) :
                    React.createElement('div', {
                        key: 'tasks-list',
                        className: 'item-list'
                    }, filteredTasks.map(task => 
                        React.createElement('div', {
                            key: task.id,
                            className: 'item-card',
                            style: {
                                borderLeft: !task.enabled ? '4px solid #9ca3af' :
                                    isTaskOverdue(task.scheduled_time, task.status, task.is_recurring) ? '4px solid #ef4444' : 
                                    task.status === 'completed' ? '4px solid #10b981' :
                                    task.status === 'failed' ? '4px solid #ef4444' :
                                    task.is_recurring ? '4px solid #8b5cf6' :
                                    '4px solid #3b82f6'
                            }
                        }, [
                            React.createElement('div', { 
                                key: 'info',
                                className: 'item-info' 
                            }, [
                                React.createElement('div', {
                                    key: 'header',
                                    style: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }
                                }, [
                                    React.createElement('h4', { 
                                        key: 'name',
                                        style: { margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }
                                    }, [
                                        task.is_recurring && React.createElement('i', {
                                            key: 'recurring-icon',
                                            className: 'fas fa-sync-alt',
                                            style: { color: '#8b5cf6', fontSize: '14px' },
                                            title: 'Recurring task'
                                        }),
                                        task.task_type === 'agent' ? 
                                            `Agent: ${task.agent_name}` : 
                                            `Workflow: ${task.workflow_name}`
                                    ]),
                                    getTaskStatusBadge(task),
                                    isTaskOverdue(task.scheduled_time, task.status, task.is_recurring) && 
                                        React.createElement('span', {
                                            key: 'overdue',
                                            style: { 
                                                fontSize: '11px', 
                                                color: '#ef4444',
                                                fontWeight: '600'
                                            }
                                        }, '⚠️ OVERDUE')
                                ]),
                                React.createElement('p', { 
                                    key: 'description' 
                                }, task.task_description || 'No description'),
                                React.createElement('div', {
                                    key: 'details',
                                    style: { fontSize: '12px', color: '#64748b', marginTop: '8px' }
                                }, [
                                    React.createElement('div', { 
                                        key: 'scheduled' 
                                    }, `⏰ ${task.is_recurring ? 'First execution' : 'Scheduled'}: ${formatDateTimeWithRelative(task.scheduled_time)}`),
                                    
                                    task.is_recurring && React.createElement('div', { 
                                        key: 'pattern' 
                                    }, `🔄 Pattern: ${task.recurrence_pattern} (${task.recurrence_type})`),
                                    
                                    task.is_recurring && task.next_execution && React.createElement('div', { 
                                        key: 'next' 
                                    }, `⏭️ Next execution: ${formatDateTimeWithRelative(task.next_execution)}`),
                                    
                                    task.is_recurring && React.createElement('div', { 
                                        key: 'executions' 
                                    }, `📊 Executions: ${task.execution_count}${task.max_executions ? `/${task.max_executions}` : ''} (${task.failure_count} failures)`),
                                    
                                    task.last_execution && React.createElement('div', { 
                                        key: 'last' 
                                    }, `✅ Last: ${formatDateTimeWithRelative(task.last_execution)}`),
                                    
                                    task.result && !task.is_recurring && React.createElement('div', { 
                                        key: 'result',
                                        style: { 
                                            marginTop: '4px',
                                            padding: '4px 8px',
                                            background: task.status === 'failed' ? '#fee2e2' : '#f0fdf4',
                                            borderRadius: '4px',
                                            maxWidth: '300px',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                        }
                                    }, `Result: ${task.result}`)
                                ])
                            ]),
                            React.createElement('div', { 
                                key: 'actions',
                                className: 'item-actions',
                                style: { display: 'flex', flexDirection: 'column', gap: '4px' }
                            }, [
                                React.createElement('div', {
                                    key: 'top-actions',
                                    style: { display: 'flex', gap: '4px' }
                                }, [
                                    React.createElement('button', {
                                        key: 'toggle',
                                        className: `btn ${task.enabled ? 'btn-warning' : 'btn-success'}`,
                                        onClick: () => handleToggleTask(task.id, task.enabled),
                                        disabled: task.status === 'running',
                                        style: { fontSize: '12px', padding: '4px 8px' },
                                        title: task.enabled ? 'Disable task' : 'Enable task'
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: task.enabled ? 'fas fa-pause' : 'fas fa-play'
                                        }),
                                        ' ', task.enabled ? 'Disable' : 'Enable'
                                    ]),
                                    
                                    React.createElement('button', {
                                        key: 'edit',
                                        className: 'btn btn-secondary',
                                        onClick: () => handleEditTask(task),
                                        disabled: task.status === 'running',
                                        style: { fontSize: '12px', padding: '4px 8px' }
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-edit' 
                                        }),
                                        ' Edit'
                                    ])
                                ]),
                                
                                React.createElement('div', {
                                    key: 'bottom-actions',
                                    style: { display: 'flex', gap: '4px' }
                                }, [
                                    task.is_recurring && React.createElement('button', {
                                        key: 'history',
                                        className: 'btn btn-secondary',
                                        onClick: () => handleViewExecutions(task.id),
                                        style: { fontSize: '12px', padding: '4px 8px' }
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-history' 
                                        }),
                                        ' History'
                                    ]),
                                    
                                    React.createElement('button', {
                                        key: 'delete',
                                        className: 'btn btn-danger',
                                        onClick: () => handleDeleteTask(task.id),
                                        disabled: task.status === 'running',
                                        style: { fontSize: '12px', padding: '4px 8px' }
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-trash' 
                                        }),
                                        ' Delete'
                                    ])
                                ])
                            ])
                        ])
                    ))
            ])
        ]),

        // Task Creation/Edit Modal
        showModal && React.createElement(ScheduleTaskModal, {
            key: 'modal',
            task: editingTask,
            agents: agents,
            workflows: workflows,
            onClose: () => setShowModal(false),
            onSave: loadData
        }),

        // Execution History Modal
        showExecutions && React.createElement('div', {
            key: 'executions-modal',
            className: 'modal-overlay',
            onClick: () => setShowExecutions(false)
        }, React.createElement('div', {
            className: 'modal large',
            onClick: e => e.stopPropagation(),
            style: { maxWidth: '800px' }
        }, [
            React.createElement('div', { 
                key: 'header',
                className: 'modal-header' 
            }, [
                React.createElement('h3', { 
                    key: 'title',
                    className: 'modal-title' 
                }, `Execution History - Task ${selectedTaskExecutions?.task_id}`),
                React.createElement('button', {
                    key: 'close',
                    className: 'modal-close',
                    onClick: () => setShowExecutions(false)
                }, React.createElement('i', { className: 'fas fa-times' }))
            ]),
            
            React.createElement('div', { 
                key: 'content',
                className: 'modal-content',
                style: { maxHeight: '500px', overflowY: 'auto' }
            }, [
                selectedTaskExecutions?.executions?.length === 0 ? 
                    React.createElement('div', {
                        key: 'empty',
                        className: 'empty-state'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-history'
                        }),
                        React.createElement('h3', { key: 'title' }, 'No execution history'),
                        React.createElement('p', { key: 'description' }, 'This task has not been executed yet.')
                    ]) :
                    React.createElement('div', {
                        key: 'executions-list',
                        className: 'item-list'
                    }, selectedTaskExecutions?.executions?.map((execution, index) => 
                        React.createElement('div', {
                            key: execution.id,
                            className: 'item-card',
                            style: {
                                borderLeft: execution.status === 'completed' ? '4px solid #10b981' : '4px solid #ef4444'
                            }
                        }, [
                            React.createElement('div', {
                                key: 'execution-info',
                                style: { fontSize: '14px' }
                            }, [
                                React.createElement('div', {
                                    key: 'header',
                                    style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }
                                }, [
                                    React.createElement('strong', { key: 'title' }, `Execution #${selectedTaskExecutions.executions.length - index}`),
                                    React.createElement('span', {
                                        key: 'status',
                                        className: `status ${execution.status === 'completed' ? 'status-online' : 'status-offline'}`
                                    }, execution.status === 'completed' ? 'Success' : 'Failed')
                                ]),
                                React.createElement('div', {
                                    key: 'details',
                                    style: { fontSize: '12px', color: '#64748b' }
                                }, [
                                    React.createElement('div', { key: 'time' }, `🕐 ${formatDateTimeWithRelative(execution.execution_time)}`),
                                    execution.duration_seconds && React.createElement('div', { key: 'duration' }, `⏱️ Duration: ${execution.duration_seconds}s`),
                                    execution.result && React.createElement('div', { 
                                        key: 'result',
                                        style: { marginTop: '4px', wordBreak: 'break-word' }
                                    }, execution.status === 'completed' ? 
                                        `✅ Result: ${execution.result.length > 100 ? execution.result.substring(0, 100) + '...' : execution.result}` :
                                        `❌ Error: ${execution.error_message || execution.result}`
                                    )
                                ])
                            ])
                        ])
                    ))
            ]),
            
            React.createElement('div', { 
                key: 'footer',
                className: 'modal-footer' 
            }, [
                React.createElement('button', {
                    key: 'close-btn',
                    className: 'btn btn-secondary',
                    onClick: () => setShowExecutions(false)
                }, 'Close')
            ])
        ]))
    ]);
};

// Make component globally available
window.Scheduling = Scheduling;