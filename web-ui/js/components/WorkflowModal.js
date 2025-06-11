// js/components/WorkflowModal.js - Enhanced Workflow Modal Component with Input Support

const WorkflowModal = ({ workflow, agents = [], tools = [], onClose, onSave }) => {
    const { useState } = React;

    const [formData, setFormData] = useState({
        name: workflow?.name || '',
        description: workflow?.description || '',
        input_schema: workflow?.input_schema || {
            type: 'object',
            properties: {},
            required: []
        },
        steps: workflow?.steps || [],
        enabled: workflow?.enabled !== false
    });
    const [saving, setSaving] = useState(false);

    const addInputField = () => {
        const fieldName = prompt('Enter field name:');
        if (!fieldName) return;

        const fieldType = prompt('Enter field type (string, number, boolean, object, array):', 'string');
        if (!fieldType) return;

        const isRequired = confirm('Is this field required?');

        setFormData(prev => ({
            ...prev,
            input_schema: {
                ...prev.input_schema,
                properties: {
                    ...prev.input_schema.properties,
                    [fieldName]: {
                        type: fieldType,
                        description: `${fieldName} input field`
                    }
                },
                required: isRequired ? 
                    [...prev.input_schema.required, fieldName] : 
                    prev.input_schema.required
            }
        }));
    };

    const removeInputField = (fieldName) => {
        setFormData(prev => {
            const newProperties = { ...prev.input_schema.properties };
            delete newProperties[fieldName];
            
            return {
                ...prev,
                input_schema: {
                    ...prev.input_schema,
                    properties: newProperties,
                    required: prev.input_schema.required.filter(name => name !== fieldName)
                }
            };
        });
    };

    const addStep = (type) => {
        const newStep = {
            id: Date.now(),
            type,
            name: '',
            task: type === 'agent' ? '' : undefined,
            parameters: type === 'tool' ? {} : undefined,
            context_key: '',
            use_previous_output: false
        };
        setFormData(prev => ({
            ...prev,
            steps: [...prev.steps, newStep]
        }));
    };

    const updateStep = (index, updates) => {
        setFormData(prev => ({
            ...prev,
            steps: prev.steps.map((step, i) => 
                i === index ? { ...step, ...updates } : step
            )
        }));
    };

    const removeStep = (index) => {
        setFormData(prev => ({
            ...prev,
            steps: prev.steps.filter((_, i) => i !== index)
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.name.trim()) {
            alert('Workflow name is required');
            return;
        }

        if (formData.steps.length === 0) {
            alert('At least one step is required');
            return;
        }

        try {
            setSaving(true);
            // Remove the temporary id field from steps
            const workflowData = {
                ...formData,
                steps: formData.steps.map(({ id, ...step }) => step)
            };
            
            if (workflow) {
                await api.updateWorkflow(workflow.name, workflowData);
            } else {
                await api.createWorkflow(workflowData);
            }
            await onSave();
            onClose();
        } catch (error) {
            alert('Failed to save workflow: ' + error.message);
        } finally {
            setSaving(false);
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
                }, workflow ? 'Edit Workflow' : 'Create Workflow'),
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
                    // Basic Info Section
                    React.createElement('div', { 
                        key: 'basic-info',
                        style: {
                            background: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            borderRadius: '8px',
                            padding: '16px',
                            marginBottom: '20px'
                        }
                    }, [
                        React.createElement('h4', { 
                            key: 'title',
                            style: { margin: '0 0 16px 0', color: '#374151' }
                        }, '📋 Basic Information'),
                        
                        React.createElement('div', { 
                            key: 'name-group',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'Workflow Name'),
                            React.createElement('input', {
                                key: 'input',
                                className: 'form-input',
                                type: 'text',
                                value: formData.name,
                                onChange: e => setFormData(prev => ({ ...prev, name: e.target.value })),
                                placeholder: 'Enter workflow name',
                                required: true
                            })
                        ]),

                        React.createElement('div', { 
                            key: 'description-group',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'Description'),
                            React.createElement('textarea', {
                                key: 'textarea',
                                className: 'form-textarea',
                                value: formData.description,
                                onChange: e => setFormData(prev => ({ ...prev, description: e.target.value })),
                                placeholder: 'Describe what this workflow does',
                                required: true
                            })
                        ])
                    ]),

                    // Input Schema Section
                    React.createElement('div', { 
                        key: 'input-schema',
                        style: {
                            background: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            borderRadius: '8px',
                            padding: '16px',
                            marginBottom: '20px'
                        }
                    }, [
                        React.createElement('div', {
                            key: 'header',
                            style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }
                        }, [
                            React.createElement('h4', { 
                                key: 'title',
                                style: { margin: 0, color: '#374151' }
                            }, '🔧 Workflow Input Schema'),
                            React.createElement('button', {
                                key: 'add-field',
                                type: 'button',
                                className: 'btn btn-secondary',
                                onClick: addInputField,
                                style: { fontSize: '12px', padding: '4px 8px' }
                            }, [
                                React.createElement('i', { 
                                    key: 'icon',
                                    className: 'fas fa-plus' 
                                }),
                                ' Add Field'
                            ])
                        ]),

                        React.createElement('div', {
                            key: 'info',
                            style: {
                                background: '#dbeafe',
                                border: '1px solid #93c5fd',
                                borderRadius: '6px',
                                padding: '12px',
                                marginBottom: '16px'
                            }
                        }, [
                            React.createElement('p', {
                                key: 'desc',
                                style: { margin: 0, color: '#1e40af', fontSize: '12px' }
                            }, '💡 Define what inputs this workflow expects when executed. These will be prompted for or passed via API.')
                        ]),

                        Object.keys(formData.input_schema.properties).length === 0 ? 
                            React.createElement('div', {
                                key: 'empty-inputs',
                                style: {
                                    textAlign: 'center',
                                    padding: '20px',
                                    color: '#64748b',
                                    border: '2px dashed #e2e8f0',
                                    borderRadius: '8px'
                                }
                            }, 'No input fields defined. This workflow will run without input.') :
                            React.createElement('div', {
                                key: 'input-fields'
                            }, Object.entries(formData.input_schema.properties).map(([fieldName, field]) => 
                                React.createElement('div', {
                                    key: fieldName,
                                    style: {
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '12px',
                                        padding: '8px',
                                        background: 'white',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '6px',
                                        marginBottom: '8px'
                                    }
                                }, [
                                    React.createElement('div', {
                                        key: 'info',
                                        style: { flex: 1 }
                                    }, [
                                        React.createElement('strong', { key: 'name' }, fieldName),
                                        React.createElement('span', { 
                                            key: 'type',
                                            style: { marginLeft: '8px', fontSize: '12px', color: '#64748b' }
                                        }, `(${field.type})`),
                                        formData.input_schema.required.includes(fieldName) && 
                                            React.createElement('span', {
                                                key: 'required',
                                                style: { marginLeft: '8px', fontSize: '11px', color: '#ef4444' }
                                            }, 'required')
                                    ]),
                                    React.createElement('button', {
                                        key: 'remove',
                                        type: 'button',
                                        className: 'btn btn-danger',
                                        onClick: () => removeInputField(fieldName),
                                        style: { fontSize: '11px', padding: '2px 6px' }
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-trash' 
                                        })
                                    ])
                                ])
                            ))
                    ]),

                    // Steps Section
                    React.createElement('div', { 
                        key: 'steps-section',
                        style: {
                            background: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            borderRadius: '8px',
                            padding: '16px',
                            marginBottom: '20px'
                        }
                    }, [
                        React.createElement('div', {
                            key: 'header',
                            style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }
                        }, [
                            React.createElement('h4', { 
                                key: 'title',
                                style: { margin: 0, color: '#374151' }
                            }, '⚡ Workflow Steps'),
                            React.createElement('div', {
                                key: 'step-buttons'
                            }, [
                                React.createElement('button', {
                                    key: 'add-agent',
                                    type: 'button',
                                    className: 'btn btn-secondary',
                                    onClick: () => addStep('agent'),
                                    style: { marginRight: '8px', fontSize: '12px', padding: '4px 8px' }
                                }, [
                                    React.createElement('i', { 
                                        key: 'icon',
                                        className: 'fas fa-robot' 
                                    }),
                                    ' Add Agent'
                                ]),
                                React.createElement('button', {
                                    key: 'add-tool',
                                    type: 'button',
                                    className: 'btn btn-secondary',
                                    onClick: () => addStep('tool'),
                                    style: { fontSize: '12px', padding: '4px 8px' }
                                }, [
                                    React.createElement('i', { 
                                        key: 'icon',
                                        className: 'fas fa-tools' 
                                    }),
                                    ' Add Tool'
                                ])
                            ])
                        ]),

                        // Steps List
                        formData.steps.length === 0 ? 
                            React.createElement('div', {
                                key: 'empty-steps',
                                style: {
                                    textAlign: 'center',
                                    padding: '40px',
                                    color: '#64748b',
                                    border: '2px dashed #e2e8f0',
                                    borderRadius: '8px'
                                }
                            }, 'Add steps to build your workflow') :
                            formData.steps.map((step, index) => 
                                React.createElement('div', {
                                    key: step.id,
                                    style: {
                                        background: 'white',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '8px',
                                        padding: '16px',
                                        marginBottom: '12px',
                                        position: 'relative'
                                    }
                                }, [
                                    React.createElement('div', {
                                        key: 'step-number',
                                        style: {
                                            position: 'absolute',
                                            top: '-10px',
                                            left: '16px',
                                            background: '#3b82f6',
                                            color: 'white',
                                            width: '24px',
                                            height: '24px',
                                            borderRadius: '50%',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: '12px',
                                            fontWeight: '600'
                                        }
                                    }, index + 1),
                                    React.createElement('div', {
                                        key: 'step-header',
                                        style: {
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            marginBottom: '16px',
                                            paddingTop: '8px'
                                        }
                                    }, [
                                        React.createElement('h4', { 
                                            key: 'title',
                                            style: { margin: 0 }
                                        }, `Step ${index + 1}: ${step.type === 'agent' ? '🤖 Agent' : '🔧 Tool'}`),
                                        React.createElement('button', {
                                            key: 'remove',
                                            type: 'button',
                                            className: 'btn btn-danger',
                                            onClick: () => removeStep(index),
                                            style: { padding: '4px 8px', fontSize: '12px' }
                                        }, [
                                            React.createElement('i', { 
                                                key: 'icon',
                                                className: 'fas fa-trash' 
                                            })
                                        ])
                                    ]),

                                    React.createElement('div', {
                                        key: 'step-content',
                                        className: 'grid grid-2'
                                    }, [
                                        React.createElement('div', { 
                                            key: 'name-field',
                                            className: 'form-group' 
                                        }, [
                                            React.createElement('label', { 
                                                key: 'label',
                                                className: 'form-label' 
                                            }, step.type === 'agent' ? 'Select Agent' : 'Select Tool'),
                                            React.createElement('select', {
                                                key: 'select',
                                                className: 'form-select',
                                                value: step.name,
                                                onChange: e => updateStep(index, { name: e.target.value }),
                                                required: true
                                            }, [
                                                React.createElement('option', { 
                                                    key: 'placeholder',
                                                    value: '' 
                                                }, `Choose ${step.type}`),
                                                ...(step.type === 'agent' ? agents : tools).map(item => 
                                                    React.createElement('option', {
                                                        key: item.name,
                                                        value: item.name
                                                    }, item.name)
                                                )
                                            ])
                                        ]),

                                        React.createElement('div', { 
                                            key: 'context-field',
                                            className: 'form-group' 
                                        }, [
                                            React.createElement('label', { 
                                                key: 'label',
                                                className: 'form-label' 
                                            }, 'Output Key'),
                                            React.createElement('input', {
                                                key: 'input',
                                                className: 'form-input',
                                                type: 'text',
                                                value: step.context_key,
                                                onChange: e => updateStep(index, { context_key: e.target.value }),
                                                placeholder: 'e.g., website_status, analysis_result'
                                            })
                                        ])
                                    ]),

                                    // Input Source for this step
                                    React.createElement('div', {
                                        key: 'input-source',
                                        className: 'form-group'
                                    }, [
                                        React.createElement('label', {
                                            key: 'label',
                                            className: 'form-label'
                                        }, 'Input Source'),
                                        React.createElement('div', {
                                            key: 'options',
                                            style: { display: 'flex', gap: '16px', flexWrap: 'wrap' }
                                        }, [
                                            React.createElement('label', {
                                                key: 'workflow-input',
                                                style: { display: 'flex', alignItems: 'center', gap: '6px' }
                                            }, [
                                                React.createElement('input', {
                                                    key: 'radio',
                                                    type: 'radio',
                                                    name: `input-source-${index}`,
                                                    checked: !step.use_previous_output,
                                                    onChange: () => updateStep(index, { use_previous_output: false })
                                                }),
                                                React.createElement('span', { key: 'text' }, 'Use workflow input')
                                            ]),
                                            index > 0 && React.createElement('label', {
                                                key: 'previous-output',
                                                style: { display: 'flex', alignItems: 'center', gap: '6px' }
                                            }, [
                                                React.createElement('input', {
                                                    key: 'radio',
                                                    type: 'radio',
                                                    name: `input-source-${index}`,
                                                    checked: step.use_previous_output,
                                                    onChange: () => updateStep(index, { use_previous_output: true })
                                                }),
                                                React.createElement('span', { key: 'text' }, 'Use previous step output')
                                            ])
                                        ])
                                    ]),

                                    // Task description for agent steps
                                    step.type === 'agent' && React.createElement('div', {
                                        key: 'task-field',
                                        className: 'form-group'
                                    }, [
                                        React.createElement('label', {
                                            key: 'label',
                                            className: 'form-label'
                                        }, 'Task Description'),
                                        React.createElement('textarea', {
                                            key: 'textarea',
                                            className: 'form-textarea',
                                            value: step.task || '',
                                            onChange: e => updateStep(index, { task: e.target.value }),
                                            placeholder: 'Describe what this agent should do with the input',
                                            style: { minHeight: '60px' }
                                        })
                                    ])
                                ])
                            )
                    ]),

                    // Enabled Checkbox
                    React.createElement('div', { 
                        key: 'enabled-group',
                        className: 'form-group' 
                    }, 
                        React.createElement('label', {
                            style: {
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            }
                        }, [
                            React.createElement('input', {
                                key: 'checkbox',
                                type: 'checkbox',
                                checked: formData.enabled,
                                onChange: e => setFormData(prev => ({ ...prev, enabled: e.target.checked }))
                            }),
                            React.createElement('span', { 
                                key: 'label' 
                            }, 'Enable this workflow')
                        ])
                    )
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
                        disabled: saving
                    }, saving ? [
                        React.createElement('div', { 
                            key: 'spinner',
                            className: 'spinner',
                            style: { width: '12px', height: '12px' }
                        }),
                        'Saving...'
                    ] : (workflow ? 'Update Workflow' : 'Create Workflow'))
                ])
            ])
        ])
    );
};

// Make component globally available
window.WorkflowModal = WorkflowModal;