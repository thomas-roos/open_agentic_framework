// js/components/AgentModal.js - Agent Modal Component

const AgentModal = ({ agent, tools = [], models = [], onClose, onSave }) => {
    const { useState } = React;

    const [formData, setFormData] = useState({
        name: agent?.name || '',
        role: agent?.role || '',
        goals: agent?.goals || '',
        backstory: agent?.backstory || '',
        ollama_model: agent?.ollama_model || (models[0]?.name || 'granite3.2:2b'),
        tools: agent?.tools || [],
        enabled: agent?.enabled !== false
    });
    
    const [saving, setSaving] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.name.trim()) {
            alert('Agent name is required');
            return;
        }

        try {
            setSaving(true);
            if (agent) {
                await api.updateAgent(agent.name, formData);
            } else {
                await api.createAgent(formData);
            }
            await onSave();
            onClose();
        } catch (error) {
            alert('Failed to save agent: ' + error.message);
        } finally {
            setSaving(false);
        }
    };

    const handleToolToggle = (toolName) => {
        setFormData(prev => ({
            ...prev,
            tools: prev.tools.includes(toolName)
                ? prev.tools.filter(t => t !== toolName)
                : [...prev.tools, toolName]
        }));
    };

    const updateFormData = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    // Debug info
    console.log('AgentModal - Models received:', models);
    console.log('AgentModal - Tools received:', tools);

    return React.createElement('div', {
        className: 'modal-overlay',
        onClick: onClose
    }, 
        React.createElement('div', {
            className: 'modal',
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
                }, agent ? 'Edit Agent' : 'Create Agent'),
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
                    // Debug Info
                    React.createElement('div', {
                        key: 'debug',
                        className: 'debug-info'
                    }, `Debug: ${models.length} models, ${tools.length} tools available`),

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
                            onChange: e => updateFormData('name', e.target.value),
                            placeholder: 'Enter agent name',
                            required: true
                        })
                    ]),

                    // Role Field
                    React.createElement('div', { 
                        key: 'role-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Role'),
                        React.createElement('input', {
                            key: 'input',
                            className: 'form-input',
                            type: 'text',
                            value: formData.role,
                            onChange: e => updateFormData('role', e.target.value),
                            placeholder: 'e.g., Website Monitoring Specialist',
                            required: true
                        })
                    ]),

                    // Goals Field
                    React.createElement('div', { 
                        key: 'goals-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Goals'),
                        React.createElement('textarea', {
                            key: 'textarea',
                            className: 'form-textarea',
                            value: formData.goals,
                            onChange: e => updateFormData('goals', e.target.value),
                            placeholder: 'Describe what this agent should accomplish',
                            required: true
                        })
                    ]),

                    // Backstory Field
                    React.createElement('div', { 
                        key: 'backstory-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Backstory'),
                        React.createElement('textarea', {
                            key: 'textarea',
                            className: 'form-textarea',
                            value: formData.backstory,
                            onChange: e => updateFormData('backstory', e.target.value),
                            placeholder: 'Give the agent some context and personality',
                            required: true
                        })
                    ]),

                    // Model Selection Field
                    React.createElement('div', { 
                        key: 'model-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Model'),
                        React.createElement('select', {
                            key: 'select',
                            className: 'form-select',
                            value: formData.ollama_model,
                            onChange: e => updateFormData('ollama_model', e.target.value)
                        }, [
                            React.createElement('option', { 
                                key: 'placeholder',
                                value: '' 
                            }, 'Select a model'),
                            ...models.map(model => 
                                React.createElement('option', {
                                    key: model.name,
                                    value: model.name
                                }, `${model.display_name || model.name} (${model.provider})`)
                            )
                        ])
                    ]),

                    // Tools Selection
                    React.createElement('div', { 
                        key: 'tools-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Available Tools'),
                        React.createElement('div', {
                            key: 'tools-grid',
                            style: {
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                                gap: '8px'
                            }
                        }, tools.map(tool => 
                            React.createElement('label', {
                                key: tool.name,
                                style: {
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    padding: '8px',
                                    background: '#f8fafc',
                                    borderRadius: '6px',
                                    border: '1px solid #e2e8f0'
                                }
                            }, [
                                React.createElement('input', {
                                    key: 'checkbox',
                                    type: 'checkbox',
                                    checked: formData.tools.includes(tool.name),
                                    onChange: () => handleToolToggle(tool.name)
                                }),
                                React.createElement('span', { 
                                    key: 'name',
                                    style: { fontSize: '14px' }
                                }, tool.name)
                            ])
                        ))
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
                                onChange: e => updateFormData('enabled', e.target.checked)
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
                    ] : (agent ? 'Update Agent' : 'Create Agent'))
                ])
            ])
        ])
    );
};

// Make component globally available
window.AgentModal = AgentModal;