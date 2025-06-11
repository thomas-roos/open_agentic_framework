// js/components/ScheduleTaskModal.js - Schedule Task Modal Component

const ScheduleTaskModal = ({ task, agents = [], workflows = [], onClose, onSave }) => {
    const { useState } = React;

    const [formData, setFormData] = useState({
        task_type: task?.task_type || 'agent',
        agent_name: task?.agent_name || '',
        workflow_name: task?.workflow_name || '',
        task_description: task?.task_description || '',
        scheduled_time: task?.scheduled_time ? 
            new Date(task.scheduled_time).toISOString().slice(0, 16) : 
            new Date(Date.now() + 60000).toISOString().slice(0, 16), // 1 minute from now
        context: task?.context ? JSON.stringify(task.context, null, 2) : '{}'
    });
    const [saving, setSaving] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Validation
        if (formData.task_type === 'agent' && !formData.agent_name) {
            alert('Please select an agent');
            return;
        }
        
        if (formData.task_type === 'workflow' && !formData.workflow_name) {
            alert('Please select a workflow');
            return;
        }

        if (!formData.task_description.trim()) {
            alert('Please enter a task description');
            return;
        }

        if (new Date(formData.scheduled_time) <= new Date()) {
            alert('Scheduled time must be in the future');
            return;
        }

        try {
            setSaving(true);
            
            // Parse context JSON
            let contextObj = {};
            try {
                contextObj = JSON.parse(formData.context);
            } catch (error) {
                alert('Invalid JSON in context field');
                return;
            }

            const taskData = {
                task_type: formData.task_type,
                agent_name: formData.task_type === 'agent' ? formData.agent_name : undefined,
                workflow_name: formData.task_type === 'workflow' ? formData.workflow_name : undefined,
                task_description: formData.task_description,
                scheduled_time: new Date(formData.scheduled_time).toISOString(),
                context: contextObj
            };

            if (task) {
                // Update existing task (if your API supports it)
                alert('Task update not yet implemented in the API');
            } else {
                // Create new task
                await api.scheduleTask(taskData);
                alert('Task scheduled successfully!');
            }

            await onSave();
            onClose();
        } catch (error) {
            alert(`Failed to schedule task: ${error.message}`);
        } finally {
            setSaving(false);
        }
    };

    const updateFormData = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const getQuickTimeOptions = () => {
        const now = new Date();
        return [
            { label: '5 minutes', value: new Date(now.getTime() + 5 * 60000) },
            { label: '15 minutes', value: new Date(now.getTime() + 15 * 60000) },
            { label: '1 hour', value: new Date(now.getTime() + 60 * 60000) },
            { label: '6 hours', value: new Date(now.getTime() + 6 * 60 * 60000) },
            { label: '24 hours', value: new Date(now.getTime() + 24 * 60 * 60000) }
        ];
    };

    const setQuickTime = (date) => {
        updateFormData('scheduled_time', date.toISOString().slice(0, 16));
    };

    const generateSampleContext = () => {
        if (formData.task_type === 'agent') {
            return JSON.stringify({
                "priority": "high",
                "additional_instructions": "Be extra careful with this task",
                "notify_on_completion": true
            }, null, 2);
        } else {
            return JSON.stringify({
                "environment": "production",
                "max_retries": 3,
                "timeout": 300
            }, null, 2);
        }
    };

    return React.createElement('div', {
        className: 'modal-overlay',
        onClick: onClose
    }, 
        React.createElement('div', {
            className: 'modal large',
            onClick: e => e.stopPropagation()
        }, [
            // Modal Header
            React.createElement('div', { 
                key: 'header',
                className: 'modal-header' 
            }, [
                React.createElement('h3', { 
                    key: 'title',
                    className: 'modal-title' 
                }, task ? 'Edit Scheduled Task' : 'Schedule New Task'),
                React.createElement('button', {
                    key: 'close',
                    className: 'modal-close',
                    onClick: onClose
                }, React.createElement('i', { className: 'fas fa-times' }))
            ]),
            
            // Modal Form
            React.createElement('form', { 
                key: 'form',
                onSubmit: handleSubmit 
            }, [
                React.createElement('div', { 
                    key: 'content',
                    className: 'modal-content' 
                }, [
                    // Task Type Selection
                    React.createElement('div', { 
                        key: 'type-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Task Type'),
                        React.createElement('div', {
                            key: 'radio-group',
                            style: { display: 'flex', gap: '16px' }
                        }, [
                            React.createElement('label', {
                                key: 'agent-option',
                                style: { display: 'flex', alignItems: 'center', gap: '8px' }
                            }, [
                                React.createElement('input', {
                                    key: 'radio',
                                    type: 'radio',
                                    name: 'task_type',
                                    value: 'agent',
                                    checked: formData.task_type === 'agent',
                                    onChange: e => updateFormData('task_type', e.target.value)
                                }),
                                React.createElement('i', { 
                                    key: 'icon',
                                    className: 'fas fa-robot' 
                                }),
                                'Execute Agent'
                            ]),
                            React.createElement('label', {
                                key: 'workflow-option',
                                style: { display: 'flex', alignItems: 'center', gap: '8px' }
                            }, [
                                React.createElement('input', {
                                    key: 'radio',
                                    type: 'radio',
                                    name: 'task_type',
                                    value: 'workflow',
                                    checked: formData.task_type === 'workflow',
                                    onChange: e => updateFormData('task_type', e.target.value)
                                }),
                                React.createElement('i', { 
                                    key: 'icon',
                                    className: 'fas fa-project-diagram' 
                                }),
                                'Execute Workflow'
                            ])
                        ])
                    ]),

                    // Agent/Workflow Selection
                    formData.task_type === 'agent' ? 
                        React.createElement('div', { 
                            key: 'agent-group',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'Select Agent'),
                            React.createElement('select', {
                                key: 'select',
                                className: 'form-select',
                                value: formData.agent_name,
                                onChange: e => updateFormData('agent_name', e.target.value),
                                required: true
                            }, [
                                React.createElement('option', { 
                                    key: 'placeholder',
                                    value: '' 
                                }, 'Choose an agent'),
                                ...agents.map(agent => 
                                    React.createElement('option', {
                                        key: agent.name,
                                        value: agent.name
                                    }, `${agent.name} - ${agent.role}`)
                                )
                            ])
                        ]) :
                        React.createElement('div', { 
                            key: 'workflow-group',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'Select Workflow'),
                            React.createElement('select', {
                                key: 'select',
                                className: 'form-select',
                                value: formData.workflow_name,
                                onChange: e => updateFormData('workflow_name', e.target.value),
                                required: true
                            }, [
                                React.createElement('option', { 
                                    key: 'placeholder',
                                    value: '' 
                                }, 'Choose a workflow'),
                                ...workflows.map(workflow => 
                                    React.createElement('option', {
                                        key: workflow.name,
                                        value: workflow.name
                                    }, `${workflow.name} - ${workflow.description}`)
                                )
                            ])
                        ]),

                    // Task Description
                    React.createElement('div', { 
                        key: 'description-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Task Description'),
                        React.createElement('textarea', {
                            key: 'textarea',
                            className: 'form-textarea',
                            value: formData.task_description,
                            onChange: e => updateFormData('task_description', e.target.value),
                            placeholder: formData.task_type === 'agent' ? 
                                'Describe the task for the agent to perform...' :
                                'Describe what this workflow execution should accomplish...',
                            required: true,
                            rows: 3
                        })
                    ]),

                    // Scheduled Time
                    React.createElement('div', { 
                        key: 'time-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Scheduled Time'),
                        React.createElement('input', {
                            key: 'input',
                            className: 'form-input',
                            type: 'datetime-local',
                            value: formData.scheduled_time,
                            onChange: e => updateFormData('scheduled_time', e.target.value),
                            min: new Date(Date.now() + 60000).toISOString().slice(0, 16), // 1 minute from now
                            required: true
                        }),
                        React.createElement('div', {
                            key: 'quick-options',
                            style: { marginTop: '8px' }
                        }, [
                            React.createElement('small', {
                                key: 'label',
                                style: { color: '#64748b', marginRight: '8px' }
                            }, 'Quick options:'),
                            ...getQuickTimeOptions().map((option, index) => 
                                React.createElement('button', {
                                    key: option.label,
                                    type: 'button',
                                    className: 'btn btn-secondary',
                                    onClick: () => setQuickTime(option.value),
                                    style: { 
                                        fontSize: '11px', 
                                        padding: '2px 6px', 
                                        marginRight: '4px',
                                        marginBottom: '4px'
                                    }
                                }, option.label)
                            )
                        ])
                    ]),

                    // Context (Advanced)
                    React.createElement('div', { 
                        key: 'context-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Context (JSON) - Optional'),
                        React.createElement('div', {
                            key: 'context-actions',
                            style: { marginBottom: '8px' }
                        }, [
                            React.createElement('button', {
                                key: 'sample',
                                type: 'button',
                                className: 'btn btn-secondary',
                                onClick: () => updateFormData('context', generateSampleContext()),
                                style: { fontSize: '12px', padding: '4px 8px' }
                            }, 'Use Sample Context'),
                            React.createElement('button', {
                                key: 'clear',
                                type: 'button',
                                className: 'btn btn-secondary',
                                onClick: () => updateFormData('context', '{}'),
                                style: { fontSize: '12px', padding: '4px 8px', marginLeft: '8px' }
                            }, 'Clear')
                        ]),
                        React.createElement('textarea', {
                            key: 'textarea',
                            className: 'form-textarea',
                            value: formData.context,
                            onChange: e => updateFormData('context', e.target.value),
                            placeholder: '{\n  "key": "value"\n}',
                            style: { 
                                fontFamily: 'monospace', 
                                fontSize: '12px',
                                minHeight: '100px'
                            }
                        }),
                        React.createElement('small', {
                            key: 'help',
                            style: { color: '#64748b', fontSize: '11px' }
                        }, 'Additional parameters to pass to the agent or workflow. Must be valid JSON.')
                    ]),

                    // Preview Section
                    React.createElement('div', {
                        key: 'preview',
                        style: {
                            padding: '16px',
                            background: '#f8fafc',
                            borderRadius: '8px',
                            border: '1px solid #e2e8f0',
                            marginTop: '16px'
                        }
                    }, [
                        React.createElement('h4', {
                            key: 'title',
                            style: { margin: '0 0 12px 0', color: '#374151' }
                        }, 'Task Preview'),
                        React.createElement('div', {
                            key: 'details',
                            style: { fontSize: '14px', color: '#64748b' }
                        }, [
                            React.createElement('p', { key: 'type' }, 
                                `🎯 Type: ${formData.task_type === 'agent' ? 'Agent Execution' : 'Workflow Execution'}`),
                            React.createElement('p', { key: 'target' }, 
                                `📋 Target: ${formData.task_type === 'agent' ? 
                                    (formData.agent_name || 'No agent selected') : 
                                    (formData.workflow_name || 'No workflow selected')}`),
                            React.createElement('p', { key: 'time' }, 
                                `⏰ Scheduled: ${formData.scheduled_time ? 
                                    new Date(formData.scheduled_time).toLocaleString() : 
                                    'No time set'}`),
                            React.createElement('p', { key: 'description' }, 
                                `📝 Task: ${formData.task_description || 'No description'}`),
                            React.createElement('p', { key: 'context' }, 
                                `⚙️ Context: ${formData.context !== '{}' ? 'Custom parameters provided' : 'No additional parameters'}`)
                        ])
                    ])
                ]),

                // Modal Footer
                React.createElement('div', { 
                    key: 'footer',
                    className: 'modal-footer' 
                }, [
                    React.createElement('button', {
                        key: 'cancel',
                        type: 'button',
                        className: 'btn btn-secondary',
                        onClick: onClose
                    }, 'Cancel'),
                    React.createElement('button', {
                        key: 'submit',
                        type: 'submit',
                        className: 'btn btn-primary',
                        disabled: saving || 
                            (formData.task_type === 'agent' && !formData.agent_name) ||
                            (formData.task_type === 'workflow' && !formData.workflow_name) ||
                            !formData.task_description.trim()
                    }, saving ? [
                        React.createElement('div', { 
                            key: 'spinner',
                            className: 'spinner',
                            style: { width: '12px', height: '12px' }
                        }),
                        'Scheduling...'
                    ] : [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-calendar-plus' 
                        }),
                        task ? ' Update Task' : ' Schedule Task'
                    ])
                ])
            ])
        ])
    );
};

// Make component globally available
window.ScheduleTaskModal = ScheduleTaskModal;