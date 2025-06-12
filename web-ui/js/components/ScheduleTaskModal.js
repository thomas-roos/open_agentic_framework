// js/components/ScheduleTaskModal.js - Enhanced Schedule Task Modal with Recurring Support

const ScheduleTaskModal = ({ task, agents = [], workflows = [], onClose, onSave }) => {
    const { useState, useEffect } = React;

    const [formData, setFormData] = useState({
        task_type: task?.task_type || 'agent',
        agent_name: task?.agent_name || '',
        workflow_name: task?.workflow_name || '',
        task_description: task?.task_description || '',
        scheduled_time: task?.scheduled_time ? 
            new Date(task.scheduled_time).toISOString().slice(0, 16) : 
            new Date(Date.now() + 60000).toISOString().slice(0, 16), // 1 minute from now
        context: task?.context ? JSON.stringify(task.context, null, 2) : '{}',
        // NEW: Recurring fields
        is_recurring: task?.is_recurring || false,
        recurrence_type: task?.recurrence_type || 'simple',
        recurrence_pattern: task?.recurrence_pattern || '',
        max_executions: task?.max_executions || '',
        max_failures: task?.max_failures || 3
    });
    
    const [saving, setSaving] = useState(false);
    const [patternSuggestions, setPatternSuggestions] = useState({ simple_patterns: [], cron_patterns: [] });
    const [patternValidation, setPatternValidation] = useState(null);
    const [showAdvanced, setShowAdvanced] = useState(task?.is_recurring || false);

    useEffect(() => {
        loadPatternSuggestions();
    }, []);

    useEffect(() => {
        if (formData.is_recurring && formData.recurrence_pattern) {
            validatePattern();
        } else {
            setPatternValidation(null);
        }
    }, [formData.recurrence_pattern, formData.recurrence_type, formData.is_recurring]);

    const loadPatternSuggestions = async () => {
        try {
            const suggestions = await api.getRecurrencePatternSuggestions();
            setPatternSuggestions(suggestions);
        } catch (error) {
            console.error('Failed to load pattern suggestions:', error);
        }
    };

    const validatePattern = async () => {
        if (!formData.recurrence_pattern.trim()) {
            setPatternValidation(null);
            return;
        }

        try {
            const validation = await api.validateRecurrencePattern(
                formData.recurrence_pattern,
                formData.recurrence_type
            );
            setPatternValidation(validation);
        } catch (error) {
            setPatternValidation({
                is_valid: false,
                error: error.message
            });
        }
    };

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

        // Recurring validation
        if (formData.is_recurring) {
            if (!formData.recurrence_pattern.trim()) {
                alert('Recurrence pattern is required for recurring tasks');
                return;
            }
            
            if (patternValidation && !patternValidation.is_valid) {
                alert('Please fix the recurrence pattern before saving');
                return;
            }
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
                context: contextObj,
                is_recurring: formData.is_recurring,
                recurrence_pattern: formData.is_recurring ? formData.recurrence_pattern : undefined,
                recurrence_type: formData.is_recurring ? formData.recurrence_type : undefined,
                max_executions: formData.max_executions ? parseInt(formData.max_executions) : undefined,
                max_failures: parseInt(formData.max_failures)
            };

            if (task) {
                // Update existing task (if your API supports it)
                alert('Task update not yet fully implemented in the API');
            } else {
                // Create new task
                await api.scheduleTask(taskData);
                const message = formData.is_recurring ? 
                    'Recurring task scheduled successfully!' : 
                    'Task scheduled successfully!';
                alert(message);
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

    const setQuickPattern = (pattern, type) => {
        updateFormData('recurrence_pattern', pattern);
        updateFormData('recurrence_type', type);
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

    const getCurrentPatternSuggestions = () => {
        return formData.recurrence_type === 'cron' ? 
            patternSuggestions.cron_patterns : 
            patternSuggestions.simple_patterns;
    };

    return React.createElement('div', {
        className: 'modal-overlay',
        onClick: onClose
    }, 
        React.createElement('div', {
            className: 'modal large',
            onClick: e => e.stopPropagation(),
            style: { maxWidth: '700px', maxHeight: '90vh', overflowY: 'auto' }
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

                    // NEW: Recurring Task Toggle
                    React.createElement('div', { 
                        key: 'recurring-toggle',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', {
                            key: 'checkbox-label',
                            style: { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }
                        }, [
                            React.createElement('input', {
                                key: 'checkbox',
                                type: 'checkbox',
                                checked: formData.is_recurring,
                                onChange: e => {
                                    updateFormData('is_recurring', e.target.checked);
                                    setShowAdvanced(e.target.checked);
                                }
                            }),
                            React.createElement('i', { 
                                key: 'icon',
                                className: 'fas fa-sync-alt' 
                            }),
                            React.createElement('strong', { key: 'text' }, 'Make this a recurring task'),
                            React.createElement('small', {
                                key: 'help',
                                style: { color: '#64748b', marginLeft: '8px' }
                            }, '(execute automatically on a schedule)')
                        ])
                    ]),

                    // Scheduled Time
                    React.createElement('div', { 
                        key: 'time-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, formData.is_recurring ? 'First Execution Time' : 'Scheduled Time'),
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

                    // NEW: Recurrence Configuration (shown when recurring is enabled)
                    formData.is_recurring && React.createElement('div', {
                        key: 'recurrence-config',
                        style: {
                            padding: '16px',
                            background: '#f8fafc',
                            borderRadius: '8px',
                            border: '1px solid #e2e8f0',
                            marginBottom: '16px'
                        }
                    }, [
                        React.createElement('h4', {
                            key: 'title',
                            style: { margin: '0 0 16px 0', color: '#374151' }
                        }, 'Recurrence Settings'),

                        // Pattern Type Selection
                        React.createElement('div', { 
                            key: 'pattern-type',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'Pattern Type'),
                            React.createElement('div', {
                                key: 'radio-group',
                                style: { display: 'flex', gap: '16px' }
                            }, [
                                React.createElement('label', {
                                    key: 'simple-option',
                                    style: { display: 'flex', alignItems: 'center', gap: '8px' }
                                }, [
                                    React.createElement('input', {
                                        key: 'radio',
                                        type: 'radio',
                                        name: 'recurrence_type',
                                        value: 'simple',
                                        checked: formData.recurrence_type === 'simple',
                                        onChange: e => updateFormData('recurrence_type', e.target.value)
                                    }),
                                    'Simple (5m, 1h, 1d)'
                                ]),
                                React.createElement('label', {
                                    key: 'cron-option',
                                    style: { display: 'flex', alignItems: 'center', gap: '8px' }
                                }, [
                                    React.createElement('input', {
                                        key: 'radio',
                                        type: 'radio',
                                        name: 'recurrence_type',
                                        value: 'cron',
                                        checked: formData.recurrence_type === 'cron',
                                        onChange: e => updateFormData('recurrence_type', e.target.value)
                                    }),
                                    'Cron Expression'
                                ])
                            ])
                        ]),

                        // Pattern Input
                        React.createElement('div', { 
                            key: 'pattern-input',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'Recurrence Pattern'),
                            React.createElement('input', {
                                key: 'input',
                                className: `form-input ${patternValidation && !patternValidation.is_valid ? 'error' : ''}`,
                                type: 'text',
                                value: formData.recurrence_pattern,
                                onChange: e => updateFormData('recurrence_pattern', e.target.value),
                                placeholder: formData.recurrence_type === 'simple' ? 
                                    'e.g., 5m, 1h, 2d' : 
                                    'e.g., 0 */6 * * * (every 6 hours)',
                                required: formData.is_recurring
                            }),
                            
                            // Pattern validation feedback
                            patternValidation && React.createElement('div', {
                                key: 'validation',
                                style: {
                                    marginTop: '4px',
                                    fontSize: '12px',
                                    color: patternValidation.is_valid ? '#10b981' : '#ef4444'
                                }
                            }, [
                                React.createElement('i', {
                                    key: 'icon',
                                    className: patternValidation.is_valid ? 'fas fa-check' : 'fas fa-exclamation-triangle'
                                }),
                                ' ',
                                patternValidation.is_valid ? 'Valid pattern' : (patternValidation.error || 'Invalid pattern'),
                                patternValidation.next_executions_preview && React.createElement('div', {
                                    key: 'preview',
                                    style: { marginTop: '4px', fontSize: '11px', color: '#64748b' }
                                }, [
                                    'Next executions: ',
                                    patternValidation.next_executions_preview.slice(0, 2).map(time => 
                                        new Date(time).toLocaleString()
                                    ).join(', ')
                                ])
                            ])
                        ]),

                        // Pattern Suggestions
                        React.createElement('div', {
                            key: 'suggestions',
                            style: { marginTop: '8px' }
                        }, [
                            React.createElement('small', {
                                key: 'label',
                                style: { color: '#64748b', marginRight: '8px' }
                            }, 'Common patterns:'),
                            React.createElement('div', {
                                key: 'buttons',
                                style: { marginTop: '4px' }
                            }, getCurrentPatternSuggestions().slice(0, 6).map(suggestion => 
                                React.createElement('button', {
                                    key: suggestion.pattern,
                                    type: 'button',
                                    className: 'btn btn-secondary',
                                    onClick: () => setQuickPattern(suggestion.pattern, formData.recurrence_type),
                                    style: { 
                                        fontSize: '11px', 
                                        padding: '2px 6px', 
                                        marginRight: '4px',
                                        marginBottom: '4px'
                                    },
                                    title: suggestion.description
                                }, suggestion.pattern)
                            ))
                        ]),

                        // Advanced Recurring Options
                        React.createElement('div', {
                            key: 'advanced-options',
                            style: { display: 'flex', gap: '16px', marginTop: '16px' }
                        }, [
                            React.createElement('div', { 
                                key: 'max-executions',
                                className: 'form-group',
                                style: { flex: 1 }
                            }, [
                                React.createElement('label', { 
                                    key: 'label',
                                    className: 'form-label' 
                                }, 'Max Executions (optional)'),
                                React.createElement('input', {
                                    key: 'input',
                                    className: 'form-input',
                                    type: 'number',
                                    min: '1',
                                    value: formData.max_executions,
                                    onChange: e => updateFormData('max_executions', e.target.value),
                                    placeholder: 'Unlimited'
                                })
                            ]),
                            
                            React.createElement('div', { 
                                key: 'max-failures',
                                className: 'form-group',
                                style: { flex: 1 }
                            }, [
                                React.createElement('label', { 
                                    key: 'label',
                                    className: 'form-label' 
                                }, 'Max Consecutive Failures'),
                                React.createElement('input', {
                                    key: 'input',
                                    className: 'form-input',
                                    type: 'number',
                                    min: '1',
                                    max: '10',
                                    value: formData.max_failures,
                                    onChange: e => updateFormData('max_failures', e.target.value),
                                    required: formData.is_recurring
                                })
                            ])
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

                    // Enhanced Preview Section
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
                                `🎯 Type: ${formData.task_type === 'agent' ? 'Agent Execution' : 'Workflow Execution'}${formData.is_recurring ? ' (Recurring)' : ''}`),
                            React.createElement('p', { key: 'target' }, 
                                `📋 Target: ${formData.task_type === 'agent' ? 
                                    (formData.agent_name || 'No agent selected') : 
                                    (formData.workflow_name || 'No workflow selected')}`),
                            React.createElement('p', { key: 'time' }, 
                                `⏰ ${formData.is_recurring ? 'First execution' : 'Scheduled'}: ${formData.scheduled_time ? 
                                    new Date(formData.scheduled_time).toLocaleString() : 
                                    'No time set'}`),
                            formData.is_recurring && formData.recurrence_pattern && React.createElement('p', { key: 'pattern' }, 
                                `🔄 Repeats: ${formData.recurrence_pattern} (${formData.recurrence_type})`),
                            React.createElement('p', { key: 'description' }, 
                                `📝 Task: ${formData.task_description || 'No description'}`),
                            React.createElement('p', { key: 'context' }, 
                                `⚙️ Context: ${formData.context !== '{}' ? 'Custom parameters provided' : 'No additional parameters'}`),
                            formData.is_recurring && React.createElement('p', { key: 'limits' },
                                `⚡ Limits: ${formData.max_executions ? `Max ${formData.max_executions} executions` : 'Unlimited executions'}, stop after ${formData.max_failures} consecutive failures`)
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
                            !formData.task_description.trim() ||
                            (formData.is_recurring && !formData.recurrence_pattern.trim()) ||
                            (patternValidation && !patternValidation.is_valid)
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
                        task ? ' Update Task' : (formData.is_recurring ? ' Schedule Recurring Task' : ' Schedule Task')
                    ])
                ])
            ])
        ])
    );
};

// Make component globally available
window.ScheduleTaskModal = ScheduleTaskModal;