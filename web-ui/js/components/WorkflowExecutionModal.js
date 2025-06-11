// js/components/WorkflowExecutionModal.js - Workflow Execution Modal Component

const WorkflowExecutionModal = ({ workflow, onClose, onExecute }) => {
    const { useState, useEffect } = React;
    const [inputData, setInputData] = useState({});
    const [executing, setExecuting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Validate required fields
        const requiredFields = workflow.input_schema?.required || [];
        const missingFields = requiredFields.filter(field => {
            const value = inputData[field];
            return value === undefined || value === null || value === '';
        });

        if (missingFields.length > 0) {
            alert(`Please fill in required fields: ${missingFields.join(', ')}`);
            return;
        }

        try {
            setExecuting(true);
            await onExecute(inputData);
            onClose();
        } catch (error) {
            alert('Execution failed: ' + error.message);
        } finally {
            setExecuting(false);
        }
    };

    const updateInputData = (field, value) => {
        setInputData(prev => ({ ...prev, [field]: value }));
    };

    const parseJsonValue = (value, fieldName) => {
        try {
            return JSON.parse(value || '{}');
        } catch (error) {
            alert(`Invalid JSON in field "${fieldName}": ${error.message}`);
            return null;
        }
    };

    const hasInputs = workflow.input_schema && 
                      Object.keys(workflow.input_schema.properties || {}).length > 0;

    // If no inputs required, execute immediately
    useEffect(() => {
        if (!hasInputs) {
            onExecute({});
            onClose();
        }
    }, [hasInputs, onExecute, onClose]);

    if (!hasInputs) {
        return null; // Component will unmount after useEffect runs
    }

    return React.createElement('div', {
        className: 'modal-overlay',
        onClick: onClose
    }, 
        React.createElement('div', {
            className: 'modal',
            style: { maxWidth: '600px' },
            onClick: e => e.stopPropagation()
        }, [
            React.createElement('div', { 
                key: 'header',
                className: 'modal-header' 
            }, [
                React.createElement('h3', { 
                    key: 'title',
                    className: 'modal-title' 
                }, [
                    React.createElement('i', { 
                        key: 'icon',
                        className: 'fas fa-play',
                        style: { marginRight: '8px', color: '#10b981' }
                    }),
                    `Execute: ${workflow.name}`
                ]),
                React.createElement('button', {
                    key: 'close',
                    className: 'modal-close',
                    onClick: onClose
                }, React.createElement('i', { className: 'fas fa-times' }))
            ]),
            
            React.createElement('form', { 
                key: 'form',
                onSubmit: handleSubmit 
            }, [
                React.createElement('div', { 
                    key: 'content',
                    className: 'modal-content' 
                }, [
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
                        React.createElement('h4', { 
                            key: 'title',
                            style: { margin: '0 0 8px 0', color: '#1e40af', fontSize: '14px' }
                        }, 'Workflow Input Required'),
                        React.createElement('p', { 
                            key: 'desc',
                            style: { margin: 0, color: '#1e40af', fontSize: '12px' }
                        }, workflow.description)
                    ]),

                    // Input Fields
                    Object.entries(workflow.input_schema.properties || {}).map(([fieldName, field]) => 
                        React.createElement('div', {
                            key: fieldName,
                            className: 'form-group'
                        }, [
                            React.createElement('label', {
                                key: 'label',
                                className: 'form-label'
                            }, [
                                fieldName,
                                workflow.input_schema.required?.includes(fieldName) && 
                                    React.createElement('span', {
                                        key: 'required',
                                        style: { color: '#ef4444', marginLeft: '4px' }
                                    }, '*'),
                                React.createElement('span', {
                                    key: 'type',
                                    style: { 
                                        marginLeft: '8px', 
                                        fontSize: '11px', 
                                        color: '#64748b',
                                        fontWeight: 'normal'
                                    }
                                }, `(${field.type})`)
                            ]),
                            
                            // Render different input types
                            (() => {
                                switch (field.type) {
                                    case 'boolean':
                                        return React.createElement('label', {
                                            key: 'checkbox-label',
                                            style: {
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '8px',
                                                marginTop: '4px'
                                            }
                                        }, [
                                            React.createElement('input', {
                                                key: 'checkbox',
                                                type: 'checkbox',
                                                checked: inputData[fieldName] || false,
                                                onChange: e => updateInputData(fieldName, e.target.checked)
                                            }),
                                            React.createElement('span', { 
                                                key: 'text',
                                                style: { fontSize: '14px' }
                                            }, field.description || `Enable ${fieldName}`)
                                        ]);
                                    
                                    case 'number':
                                        return React.createElement('input', {
                                            key: 'number-input',
                                            className: 'form-input',
                                            type: 'number',
                                            step: 'any',
                                            value: inputData[fieldName] || '',
                                            onChange: e => updateInputData(fieldName, parseFloat(e.target.value) || 0),
                                            placeholder: field.description || `Enter ${fieldName}`,
                                            required: workflow.input_schema.required?.includes(fieldName)
                                        });
                                    
                                    case 'object':
                                    case 'array':
                                        return React.createElement('div', {
                                            key: 'json-container'
                                        }, [
                                            React.createElement('textarea', {
                                                key: 'json-textarea',
                                                className: 'form-textarea',
                                                value: inputData[fieldName] ? 
                                                       JSON.stringify(inputData[fieldName], null, 2) : 
                                                       (field.type === 'array' ? '[]' : '{}'),
                                                onChange: e => {
                                                    const parsed = parseJsonValue(e.target.value, fieldName);
                                                    if (parsed !== null) {
                                                        updateInputData(fieldName, parsed);
                                                    }
                                                },
                                                placeholder: field.type === 'array' ? '[]' : '{}',
                                                required: workflow.input_schema.required?.includes(fieldName),
                                                style: { 
                                                    fontFamily: 'monospace', 
                                                    fontSize: '12px',
                                                    minHeight: '80px'
                                                }
                                            }),
                                            React.createElement('small', {
                                                key: 'json-help',
                                                style: { color: '#64748b', fontSize: '11px' }
                                            }, `Enter valid JSON ${field.type}`)
                                        ]);
                                    
                                    case 'string':
                                    default:
                                        return React.createElement('input', {
                                            key: 'text-input',
                                            className: 'form-input',
                                            type: 'text',
                                            value: inputData[fieldName] || '',
                                            onChange: e => updateInputData(fieldName, e.target.value),
                                            placeholder: field.description || `Enter ${fieldName}`,
                                            required: workflow.input_schema.required?.includes(fieldName)
                                        });
                                }
                            })(),
                            
                            field.description && React.createElement('small', {
                                key: 'help',
                                style: { color: '#64748b', fontSize: '12px', marginTop: '4px', display: 'block' }
                            }, field.description)
                        ])
                    ),

                    // Input Preview
                    Object.keys(inputData).length > 0 && React.createElement('div', {
                        key: 'preview',
                        style: { marginTop: '20px' }
                    }, [
                        React.createElement('label', {
                            key: 'label',
                            className: 'form-label'
                        }, 'Input Preview'),
                        React.createElement('div', {
                            key: 'preview-content',
                            style: {
                                background: '#f1f5f9',
                                border: '1px solid #cbd5e1',
                                borderRadius: '6px',
                                padding: '12px',
                                fontFamily: 'monospace',
                                fontSize: '12px',
                                whiteSpace: 'pre-wrap',
                                maxHeight: '200px',
                                overflowY: 'auto'
                            }
                        }, JSON.stringify(inputData, null, 2))
                    ])
                ]),

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
                        className: 'btn btn-success',
                        disabled: executing
                    }, executing ? [
                        React.createElement('div', { 
                            key: 'spinner',
                            className: 'spinner',
                            style: { width: '12px', height: '12px' }
                        }),
                        'Executing...'
                    ] : [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-play' 
                        }),
                        ' Execute Workflow'
                    ])
                ])
            ])
        ])
    );
};

// Make component globally available
window.WorkflowExecutionModal = WorkflowExecutionModal;