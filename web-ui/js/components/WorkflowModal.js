// js/components/WorkflowModal.js - Workflow Modal Component

const WorkflowModal = ({ workflow, agents = [], tools = [], onClose, onSave }) => {
    const { useState } = React;

    const [formData, setFormData] = useState({
        name: workflow?.name || '',
        description: workflow?.description || '',
        steps: workflow?.steps || [],
        enabled: workflow?.enabled !== false
    });
    const [saving, setSaving] = useState(false);

    const addStep = (type) => {
        const newStep = {
            id: Date.now(),
            type,
            name: '',
            task: type === 'agent' ? '' : undefined,
            parameters: type === 'tool' ? {} : undefined,
            context_key: ''
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
                    // Name Field
                    React.createElement('div', { 
                        key: 'name-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Name'),
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

                    // Description Field
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
                    ]),

                    // Steps Section
                    React.createElement('div', { 
                        key: 'steps-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Steps'),
                        React.createElement('div', {
                            key: 'step-buttons',
                            style: { marginBottom: '16px' }
                        }, [
                            React.createElement('button', {
                                key: 'add-agent',
                                type: 'button',
                                className: 'btn btn-secondary',
                                onClick: () => addStep('agent'),
                                style: { marginRight: '8px' }
                            }, [
                                React.createElement('i', { 
                                    key: 'icon',
                                    className: 'fas fa-robot' 
                                }),
                                ' Add Agent Step'
                            ]),
                            React.createElement('button', {
                                key: 'add-tool',
                                type: 'button',
                                className: 'btn btn-secondary',
                                onClick: () => addStep('tool')
                            }, [
                                React.createElement('i', { 
                                    key: 'icon',
                                    className: 'fas fa-tools' 
                                }),
                                ' Add Tool Step'
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
                                    className: 'workflow-step'
                                }, [
                                    React.createElement('div', {
                                        key: 'step-number',
                                        className: 'workflow-step-number'
                                    }, index + 1),
                                    React.createElement('div', {
                                        key: 'step-header',
                                        className: 'workflow-step-header'
                                    }, [
                                        React.createElement('h4', { 
                                            key: 'title' 
                                        }, `Step ${index + 1}: ${step.type === 'agent' ? 'Agent' : 'Tool'}`),
                                        React.createElement('button', {
                                            key: 'remove',
                                            type: 'button',
                                            className: 'btn btn-danger',
                                            onClick: () => removeStep(index),
                                            style: { padding: '4px 8px', fontSize: '12px' }
                                        }, React.createElement('i', { className: 'fas fa-trash' }))
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
                                            }, step.type === 'agent' ? 'Agent' : 'Tool'),
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
                                                }, `Select ${step.type}`),
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
                                            }, 'Context Key'),
                                            React.createElement('input', {
                                                key: 'input',
                                                className: 'form-input',
                                                type: 'text',
                                                value: step.context_key,
                                                onChange: e => updateStep(index, { context_key: e.target.value }),
                                                placeholder: 'e.g., website_status'
                                            })
                                        ])
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
                            }, 'Enabled')
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