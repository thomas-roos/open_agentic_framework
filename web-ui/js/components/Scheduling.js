// js/components/Scheduling.js - Scheduling Component

const Scheduling = () => {
    const { useState, useEffect } = React;

    const [scheduledTasks, setScheduledTasks] = useState([]);
    const [agents, setAgents] = useState([]);
    const [workflows, setWorkflows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingTask, setEditingTask] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [tasksData, agentsData, workflowsData] = await Promise.allSettled([
                api.getScheduledTasks(),
                api.getAgents(),
                api.getWorkflows()
            ]);

            setScheduledTasks(tasksData.status === 'fulfilled' ? tasksData.value : []);
            setAgents(agentsData.status === 'fulfilled' ? agentsData.value : []);
            setWorkflows(workflowsData.status === 'fulfilled' ? workflowsData.value : []);
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

    const getTaskStatusBadge = (status) => {
        const statusMap = {
            'pending': { class: 'status-warning', text: 'Pending' },
            'running': { class: 'status-online', text: 'Running' },
            'completed': { class: 'status-online', text: 'Completed' },
            'failed': { class: 'status-offline', text: 'Failed' },
            'cancelled': { class: 'status-offline', text: 'Cancelled' }
        };
        
        const statusInfo = statusMap[status] || { class: 'status-warning', text: status };
        return React.createElement('span', {
            className: `status ${statusInfo.class}`
        }, statusInfo.text);
    };

    const formatDateTime = (dateString) => {
        try {
            return new Date(dateString).toLocaleString();
        } catch {
            return dateString;
        }
    };

    const isTaskOverdue = (scheduledTime, status) => {
        if (status !== 'pending') return false;
        try {
            return new Date(scheduledTime) < new Date();
        } catch {
            return false;
        }
    };

    if (loading) return React.createElement(Loading, { message: "Loading scheduled tasks..." });

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
                React.createElement('div', {
                    key: 'debug',
                    className: 'debug-info'
                }, `Debug: ${scheduledTasks.length} scheduled tasks, ${agents.length} agents, ${workflows.length} workflows available`),

                scheduledTasks.length === 0 ? 
                    React.createElement('div', {
                        key: 'empty',
                        className: 'empty-state'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-calendar-alt'
                        }),
                        React.createElement('h3', { key: 'title' }, 'No scheduled tasks'),
                        React.createElement('p', { key: 'description' }, 'Schedule your first agent or workflow to run automatically!'),
                        React.createElement('button', {
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
                        key: 'tasks-list'
                    }, [
                        // Summary Stats
                        React.createElement('div', {
                            key: 'stats',
                            className: 'stats-grid',
                            style: { marginBottom: '24px' }
                        }, [
                            React.createElement('div', { 
                                key: 'pending',
                                className: 'stat-card' 
                            }, [
                                React.createElement('div', { 
                                    key: 'value',
                                    className: 'stat-value' 
                                }, scheduledTasks.filter(t => t.status === 'pending').length),
                                React.createElement('div', { 
                                    key: 'label',
                                    className: 'stat-label' 
                                }, 'Pending Tasks')
                            ]),
                            React.createElement('div', { 
                                key: 'completed',
                                className: 'stat-card' 
                            }, [
                                React.createElement('div', { 
                                    key: 'value',
                                    className: 'stat-value' 
                                }, scheduledTasks.filter(t => t.status === 'completed').length),
                                React.createElement('div', { 
                                    key: 'label',
                                    className: 'stat-label' 
                                }, 'Completed')
                            ]),
                            React.createElement('div', { 
                                key: 'failed',
                                className: 'stat-card' 
                            }, [
                                React.createElement('div', { 
                                    key: 'value',
                                    className: 'stat-value' 
                                }, scheduledTasks.filter(t => t.status === 'failed').length),
                                React.createElement('div', { 
                                    key: 'label',
                                    className: 'stat-label' 
                                }, 'Failed')
                            ]),
                            React.createElement('div', { 
                                key: 'overdue',
                                className: 'stat-card' 
                            }, [
                                React.createElement('div', { 
                                    key: 'value',
                                    className: 'stat-value',
                                    style: { color: '#ef4444' }
                                }, scheduledTasks.filter(t => isTaskOverdue(t.scheduled_time, t.status)).length),
                                React.createElement('div', { 
                                    key: 'label',
                                    className: 'stat-label' 
                                }, 'Overdue')
                            ])
                        ]),

                        // Tasks List
                        React.createElement('div', {
                            key: 'list',
                            className: 'item-list'
                        }, scheduledTasks.map(task => 
                            React.createElement('div', {
                                key: task.id,
                                className: 'item-card',
                                style: {
                                    borderLeft: isTaskOverdue(task.scheduled_time, task.status) ? 
                                        '4px solid #ef4444' : 
                                        task.status === 'completed' ? '4px solid #10b981' :
                                        task.status === 'failed' ? '4px solid #ef4444' :
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
                                            style: { margin: 0 }
                                        }, task.task_type === 'agent' ? 
                                            `Agent: ${task.agent_name}` : 
                                            `Workflow: ${task.workflow_name}`),
                                        getTaskStatusBadge(task.status),
                                        isTaskOverdue(task.scheduled_time, task.status) && 
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
                                        }, `⏰ Scheduled: ${formatDateTime(task.scheduled_time)}`),
                                        task.executed_at && React.createElement('div', { 
                                            key: 'executed' 
                                        }, `✅ Executed: ${formatDateTime(task.executed_at)}`),
                                        task.result && React.createElement('div', { 
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
                                    className: 'item-actions' 
                                }, [
                                    React.createElement('button', {
                                        key: 'edit',
                                        className: 'btn btn-secondary',
                                        onClick: () => handleEditTask(task),
                                        disabled: task.status === 'running'
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-edit' 
                                        }),
                                        ' Edit'
                                    ]),
                                    React.createElement('button', {
                                        key: 'delete',
                                        className: 'btn btn-danger',
                                        onClick: () => handleDeleteTask(task.id),
                                        disabled: task.status === 'running'
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-trash' 
                                        }),
                                        ' Delete'
                                    ])
                                ])
                            ])
                        ))
                    ])
            ])
        ]),

        // Modal
        showModal && React.createElement(ScheduleTaskModal, {
            key: 'modal',
            task: editingTask,
            agents: agents,
            workflows: workflows,
            onClose: () => setShowModal(false),
            onSave: loadData
        })
    ]);
};

// Make component globally available
window.Scheduling = Scheduling;