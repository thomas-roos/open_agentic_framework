// js/components/WorkflowModal.js - Complete Enhanced Workflow Modal with Standardized Parameter System

const WorkflowModal = ({ workflow, agents = [], tools = [], onClose, onSave }) => {
    const { useState, useEffect } = React;

    const [formData, setFormData] = useState({
        name: workflow?.name || '',
        description: workflow?.description || '',
        input_schema: workflow?.input_schema || {
            type: 'object',
            properties: {},
            required: []
        },
        steps: workflow?.steps || [],
        enabled: workflow?.enabled !== false,
        output_spec: workflow?.output_spec || { extractions: [] }
    });
    const [saving, setSaving] = useState(false);
    const [showAdvancedOutputSpec, setShowAdvancedOutputSpec] = useState(false);

    // Update form data when workflow prop changes
    useEffect(() => {
        if (workflow) {
            setFormData({
                name: workflow.name || '',
                description: workflow.description || '',
                input_schema: workflow.input_schema || {
                    type: 'object',
                    properties: {},
                    required: []
                },
                steps: workflow.steps || [],
                enabled: workflow.enabled !== false,
                output_spec: workflow.output_spec || { extractions: [] }
            });
        }
    }, [workflow]);

    // Standardized Parameter Renderer
    const ParameterRenderer = {
        
        // Main entry point - renders any parameter based on its schema
        render(step, stepIndex, paramName, paramSchema, isRequired, updateStep) {
            const currentValue = step.parameters && step.parameters[paramName] !== undefined 
                ? step.parameters[paramName] 
                : paramSchema.default;

            const updateParameter = (value) => {
                updateStep(stepIndex, {
                    parameters: {
                        ...(step.parameters || {}),
                        [paramName]: value
                    }
                });
            };

            // Determine parameter complexity and render accordingly
            if (paramSchema.type === 'array' && paramSchema.items?.type === 'object') {
                return this.renderComplexArray(paramName, paramSchema, currentValue, updateParameter);
            } else if (paramSchema.type === 'object' && paramSchema.properties) {
                return this.renderComplexObject(paramName, paramSchema, currentValue, updateParameter);
            } else {
                return this.renderSimpleParameter(paramName, paramSchema, currentValue, updateParameter, isRequired);
            }
        },

        // Simple parameters: string, number, boolean, simple arrays/objects
        renderSimpleParameter(paramName, paramSchema, currentValue, updateParameter, isRequired) {
            const commonInputStyle = { fontSize: '12px', width: '100%' };
            
            // Special handling for source_data parameter (should be JSON)
            if (paramName === 'source_data') {
                return React.createElement('div', { key: 'source-data-input' }, [
                    React.createElement('textarea', {
                        key: 'source-data-textarea',
                        className: 'form-textarea',
                        value: currentValue || '',
                        onChange: e => updateParameter(e.target.value || undefined),
                        placeholder: paramSchema.description || 'Enter JSON data or variable reference like {{previous_step.output}}',
                        required: isRequired,
                        style: { fontSize: '11px', fontFamily: 'monospace', minHeight: '80px' }
                    }),
                    React.createElement('small', {
                        key: 'help',
                        style: { color: '#6b7280', fontSize: '10px' }
                    }, 'Enter JSON data or use {{variable}} syntax to reference previous step outputs')
                ]);
            }
            
            // Special handling for email_data parameter (should be email object reference)
            if (paramName === 'email_data') {
                return React.createElement('div', { key: 'email-data-input' }, [
                    React.createElement('textarea', {
                        key: 'email-data-textarea',
                        className: 'form-textarea',
                        value: currentValue || '',
                        onChange: e => updateParameter(e.target.value || undefined),
                        placeholder: paramSchema.description || 'Enter email data object or variable reference like {{email_checker.email}}',
                        required: isRequired,
                        style: { fontSize: '11px', fontFamily: 'monospace', minHeight: '80px' }
                    }),
                    React.createElement('small', {
                        key: 'help',
                        style: { color: '#6b7280', fontSize: '10px' }
                    }, 'Enter email data object or use {{variable}} syntax to reference previous step outputs')
                ]);
            }
            
            // Special handling for attachment_filenames parameter (should be array of filenames)
            if (paramName === 'attachment_filenames') {
                return React.createElement('div', { key: 'attachment-filenames-input' }, [
                    React.createElement('textarea', {
                        key: 'attachment-filenames-textarea',
                        className: 'form-textarea',
                        value: currentValue ? JSON.stringify(currentValue, null, 2) : '[]',
                        onChange: e => {
                            try {
                                const parsed = JSON.parse(e.target.value || '[]');
                                updateParameter(parsed);
                            } catch (err) {
                                // Keep text for validation later
                            }
                        },
                        placeholder: paramSchema.description || 'Enter array of filenames like ["file1.json", "file2.pdf"] or leave empty for all',
                        required: isRequired,
                        style: { fontSize: '11px', fontFamily: 'monospace', minHeight: '60px' }
                    }),
                    React.createElement('small', {
                        key: 'help',
                        style: { color: '#6b7280', fontSize: '10px' }
                    }, 'Enter JSON array of filenames or leave empty to download all attachments')
                ]);
            }
            
            // Special handling for download_path parameter (should be directory path)
            if (paramName === 'download_path') {
                return React.createElement('div', { key: 'download-path-input' }, [
                    React.createElement('input', {
                        key: 'download-path-input-field',
                        className: 'form-input',
                        type: 'text',
                        value: currentValue || '',
                        onChange: e => updateParameter(e.target.value || undefined),
                        placeholder: paramSchema.description || 'Enter custom download path or leave empty for temp directory',
                        required: isRequired,
                        style: commonInputStyle
                    }),
                    React.createElement('small', {
                        key: 'help',
                        style: { color: '#6b7280', fontSize: '10px' }
                    }, 'Enter custom download directory path or leave empty to use temporary directory')
                ]);
            }
            
            switch (paramSchema.type) {
                case 'boolean':
                    return React.createElement('label', {
                        key: 'boolean-input',
                        style: { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }
                    }, [
                        React.createElement('input', {
                            key: 'checkbox',
                            type: 'checkbox',
                            checked: currentValue || false,
                            onChange: e => updateParameter(e.target.checked)
                        }),
                        React.createElement('span', { key: 'label' }, 
                            paramSchema.description || `Enable ${paramName}`
                        )
                    ]);

                case 'integer':
                    return React.createElement('input', {
                        key: 'integer-input',
                        className: 'form-input',
                        type: 'number',
                        step: '1',
                        value: currentValue !== undefined ? currentValue : '',
                        onChange: e => updateParameter(e.target.value ? parseInt(e.target.value) : undefined),
                        placeholder: paramSchema.description || `Enter ${paramName}`,
                        required: isRequired,
                        style: commonInputStyle
                    });

                case 'number':
                    return React.createElement('input', {
                        key: 'number-input',
                        className: 'form-input',
                        type: 'number',
                        step: 'any',
                        value: currentValue !== undefined ? currentValue : '',
                        onChange: e => updateParameter(e.target.value ? parseFloat(e.target.value) : undefined),
                        placeholder: paramSchema.description || `Enter ${paramName}`,
                        required: isRequired,
                        style: commonInputStyle
                    });

                case 'string':
                    if (paramSchema.enum) {
                        return React.createElement('select', {
                            key: 'enum-select',
                            className: 'form-select',
                            value: currentValue || '',
                            onChange: e => updateParameter(e.target.value || undefined),
                            required: isRequired,
                            style: commonInputStyle
                        }, [
                            React.createElement('option', { key: 'empty', value: '' }, 
                                `Choose ${paramName}`
                            ),
                            ...paramSchema.enum.map(option =>
                                React.createElement('option', { key: option, value: option }, option)
                            )
                        ]);
                    } else {
                        return React.createElement('input', {
                            key: 'string-input',
                            className: 'form-input',
                            type: 'text',
                            value: currentValue || '',
                            onChange: e => updateParameter(e.target.value || undefined),
                            placeholder: paramSchema.description || `Enter ${paramName}`,
                            required: isRequired,
                            style: commonInputStyle
                        });
                    }

                case 'array':
                    return React.createElement('div', { key: 'simple-array' }, [
                        React.createElement('textarea', {
                            key: 'array-textarea',
                            className: 'form-textarea',
                            value: currentValue ? JSON.stringify(currentValue, null, 2) : '[]',
                            onChange: e => {
                                try {
                                    const parsed = JSON.parse(e.target.value || '[]');
                                    updateParameter(parsed);
                                } catch (err) {
                                    // Keep text for validation later
                                }
                            },
                            placeholder: paramSchema.description || 'Enter JSON array',
                            style: { fontSize: '11px', fontFamily: 'monospace', minHeight: '60px' }
                        }),
                        React.createElement('small', {
                            key: 'help',
                            style: { color: '#6b7280', fontSize: '10px' }
                        }, 'Enter valid JSON array format')
                    ]);

                case 'object':
                    return React.createElement('div', { key: 'simple-object' }, [
                        React.createElement('textarea', {
                            key: 'object-textarea',
                            className: 'form-textarea',
                            value: currentValue ? JSON.stringify(currentValue, null, 2) : '{}',
                            onChange: e => {
                                try {
                                    const parsed = JSON.parse(e.target.value || '{}');
                                    updateParameter(parsed);
                                } catch (err) {
                                    // Keep text for validation later
                                }
                            },
                            placeholder: paramSchema.description || 'Enter JSON object',
                            style: { fontSize: '11px', fontFamily: 'monospace', minHeight: '60px' }
                        }),
                        React.createElement('small', {
                            key: 'help',
                            style: { color: '#6b7280', fontSize: '10px' }
                        }, 'Enter valid JSON object format')
                    ]);

                default:
                    return React.createElement('input', {
                        key: 'default-input',
                        className: 'form-input',
                        type: 'text',
                        value: currentValue || '',
                        onChange: e => updateParameter(e.target.value || undefined),
                        placeholder: paramSchema.description || `Enter ${paramName}`,
                        style: commonInputStyle
                    });
            }
        },

        // Complex object parameters with defined properties
        renderComplexObject(paramName, paramSchema, currentValue, updateParameter) {
            const objValue = currentValue || {};
            const properties = paramSchema.properties || {};

            const updateObjectField = (fieldName, value) => {
                updateParameter({
                    ...objValue,
                    [fieldName]: value
                });
            };

            return React.createElement('div', {
                key: 'complex-object',
                style: {
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    padding: '12px',
                    background: '#f9fafb'
                }
            }, [
                React.createElement('div', {
                    key: 'object-header',
                    style: { marginBottom: '12px' }
                }, React.createElement('span', {
                    style: { fontSize: '12px', fontWeight: '600', color: '#374151' }
                }, `${paramName} Configuration`)),

                React.createElement('div', {
                    key: 'object-fields'
                }, Object.entries(properties).map(([fieldName, fieldSchema]) =>
                    React.createElement('div', {
                        key: fieldName,
                        style: { marginBottom: '8px' }
                    }, [
                        React.createElement('label', {
                            key: 'field-label',
                            style: { fontSize: '11px', color: '#6b7280', display: 'block', marginBottom: '2px' }
                        }, fieldName),
                        this.renderSimpleParameter(
                            fieldName, 
                            fieldSchema, 
                            objValue[fieldName], 
                            value => updateObjectField(fieldName, value),
                            false
                        )
                    ])
                ))
            ]);
        },

        // Complex array parameters (like data_extractor extractions)
        renderComplexArray(paramName, paramSchema, currentValue, updateParameter) {
            const items = Array.isArray(currentValue) ? currentValue : [];
            const itemSchema = paramSchema.items;

            const addItem = () => {
                const newItem = {};
                // Set default values for extractions
                if (paramName === 'extractions') {
                    newItem.name = 'extraction_' + (items.length + 1);
                    newItem.type = 'path';
                    newItem.query = '';
                    newItem.default = '';
                    newItem.format = 'text';
                } else if (itemSchema.properties) {
                    Object.entries(itemSchema.properties).forEach(([propName, propSchema]) => {
                        if (propSchema.default !== undefined) {
                            newItem[propName] = propSchema.default;
                        }
                    });
                }
                updateParameter([...items, newItem]);
            };

            const removeItem = (index) => {
                updateParameter(items.filter((_, i) => i !== index));
            };

            const updateItem = (index, field, value) => {
                const newItems = [...items];
                newItems[index] = { ...newItems[index], [field]: value };
                updateParameter(newItems);
            };

            return React.createElement('div', {
                key: 'complex-array',
                style: {
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    padding: '12px',
                    background: '#f8fafc'
                }
            }, [
                // Array header with add button
                React.createElement('div', {
                    key: 'array-header',
                    style: { 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        marginBottom: '12px' 
                    }
                }, [
                    React.createElement('span', {
                        key: 'title',
                        style: { fontSize: '12px', fontWeight: '600', color: '#374151' }
                    }, `${paramName} (${items.length} items)`),
                    React.createElement('button', {
                        key: 'add-btn',
                        type: 'button',
                        className: 'btn btn-secondary',
                        onClick: addItem,
                        style: { fontSize: '11px', padding: '4px 8px' }
                    }, [
                        React.createElement('i', { key: 'icon', className: 'fas fa-plus' }),
                        ' Add Item'
                    ])
                ]),

                // Render array items
                React.createElement('div', {
                    key: 'array-items'
                }, items.map((item, itemIndex) =>
                    React.createElement('div', {
                        key: itemIndex,
                        style: {
                            border: '1px solid #d1d5db',
                            borderRadius: '4px',
                            padding: '8px',
                            marginBottom: '8px',
                            background: 'white',
                            position: 'relative'
                        }
                    }, [
                        React.createElement('button', {
                            key: 'remove-btn',
                            type: 'button',
                            className: 'btn btn-danger',
                            onClick: () => removeItem(itemIndex),
                            style: {
                                position: 'absolute',
                                top: '4px',
                                right: '4px',
                                fontSize: '10px',
                                padding: '2px 6px'
                            }
                        }, '×'),

                        React.createElement('div', {
                            key: 'item-fields',
                            style: { paddingRight: '30px' }
                        }, itemSchema.properties ? Object.entries(itemSchema.properties).map(([fieldName, fieldSchema]) =>
                            React.createElement('div', {
                                key: fieldName,
                                style: { marginBottom: '6px' }
                            }, [
                                React.createElement('label', {
                                    key: 'field-label',
                                    style: { 
                                        fontSize: '10px', 
                                        color: '#6b7280', 
                                        display: 'block',
                                        marginBottom: '2px'
                                    }
                                }, fieldName),
                                this.renderSimpleParameter(
                                    fieldName,
                                    fieldSchema,
                                    item[fieldName],
                                    value => updateItem(itemIndex, fieldName, value),
                                    itemSchema.required?.includes(fieldName)
                                )
                            ])
                        ) : null)
                    ])
                )),

                // JSON fallback with better styling
                React.createElement('details', {
                    key: 'json-fallback',
                    style: { marginTop: '8px' }
                }, [
                    React.createElement('summary', {
                        key: 'summary',
                        style: { fontSize: '10px', color: '#6b7280', cursor: 'pointer' }
                    }, '🔧 Edit as JSON (Advanced)'),
                    React.createElement('textarea', {
                        key: 'json-editor',
                        className: 'form-textarea',
                        value: JSON.stringify(items, null, 2),
                        onChange: e => {
                            try {
                                updateParameter(JSON.parse(e.target.value));
                            } catch (err) {
                                // Keep for validation
                            }
                        },
                        style: { 
                            fontSize: '10px', 
                            fontFamily: 'monospace', 
                            minHeight: '80px',
                            marginTop: '4px'
                        }
                    })
                ])
            ]);
        }
    };

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

    const renderToolParameters = (step, index) => {
        if (step.type !== 'tool' || !step.name) return null;

        const tool = tools.find(t => t.name === step.name);
        if (!tool?.parameters_schema?.properties) {
            console.warn(`Tool ${step.name} not found or missing parameters_schema:`, tool);
            return null;
        }

        const properties = tool.parameters_schema.properties;
        const required = tool.parameters_schema.required || [];

        return React.createElement('div', {
            key: 'tool-params',
            style: {
                marginTop: '16px',
                padding: '12px',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '6px'
            }
        }, [
            React.createElement('h5', {
                key: 'title',
                style: { margin: '0 0 12px 0', color: '#374151', fontSize: '14px' }
            }, '🔧 Tool Parameters'),
            
            React.createElement('div', {
                key: 'params-container',
                style: { display: 'grid', gap: '12px' }
            }, Object.entries(properties).map(([paramName, paramSchema]) =>
                React.createElement('div', {
                    key: paramName,
                    className: 'form-group'
                }, [
                    React.createElement('label', {
                        key: 'param-label',
                        className: 'form-label',
                        style: { fontSize: '13px', marginBottom: '4px' }
                    }, [
                        paramName,
                        required.includes(paramName) && React.createElement('span', {
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
                        }, `(${paramSchema.type})`)
                    ]),
                    ParameterRenderer.render(
                        step, 
                        index, 
                        paramName, 
                        paramSchema, 
                        required.includes(paramName),
                        updateStep
                    )
                ])
            ))
        ]);
    };

    // Output Spec Handlers
    const handleOutputSpecJsonChange = (e) => {
        try {
            const parsed = JSON.parse(e.target.value || '{}');
            setFormData(prev => ({ ...prev, output_spec: parsed }));
        } catch (err) {
            // Ignore parse errors for now
        }
    };
    const handleAddExtraction = () => {
        setFormData(prev => ({
            ...prev,
            output_spec: {
                ...prev.output_spec,
                extractions: [...(prev.output_spec?.extractions || []), {
                    name: '',
                    type: 'path',
                    query: '',
                    default: '',
                    format: 'text',
                    find_criteria: {}
                }]
            }
        }));
    };
    const handleUpdateExtraction = (idx, updates) => {
        setFormData(prev => ({
            ...prev,
            output_spec: {
                ...prev.output_spec,
                extractions: prev.output_spec.extractions.map((ex, i) => i === idx ? { ...ex, ...updates } : ex)
            }
        }));
    };
    const handleRemoveExtraction = (idx) => {
        setFormData(prev => ({
            ...prev,
            output_spec: {
                ...prev.output_spec,
                extractions: prev.output_spec.extractions.filter((_, i) => i !== idx)
            }
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
                steps: formData.steps.map(({ id, ...step }) => step),
                output_spec: formData.output_spec
            };
            
            if (workflow) {
                await window.api.updateWorkflow(workflow.name, workflowData);
            } else {
                await window.api.createWorkflow(workflowData);
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
                                    ]),

                                    // Tool parameters section
                                    renderToolParameters(step, index)
                                ])
                            )
                    ]),

                    // Output Spec Section
                    React.createElement('div', {
                        key: 'output-spec-section',
                        className: 'form-group',
                        style: { marginTop: '24px', marginBottom: '24px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }
                    }, [
                        React.createElement('div', { key: 'header', style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between' } }, [
                            React.createElement('label', { key: 'label', className: 'form-label', style: { fontWeight: 600 } }, 'Workflow Output Spec (Optional)'),
                            React.createElement('button', {
                                key: 'toggle',
                                type: 'button',
                                className: 'btn btn-secondary',
                                style: { fontSize: '11px', padding: '2px 8px' },
                                onClick: () => setShowAdvancedOutputSpec(v => !v)
                            }, showAdvancedOutputSpec ? 'Simple JSON Editor' : 'Advanced Editor')
                        ]),
                        !showAdvancedOutputSpec && React.createElement('div', { key: 'json-editor', style: { marginTop: '8px' } }, [
                            React.createElement('textarea', {
                                key: 'textarea',
                                className: 'form-textarea',
                                value: JSON.stringify(formData.output_spec || {}, null, 2),
                                onChange: handleOutputSpecJsonChange,
                                placeholder: '{\n  "extractions": [ ... ]\n}'
                            }),
                            React.createElement('small', { key: 'help', style: { color: '#6b7280', fontSize: '10px' } }, 'Edit output_spec as JSON. Must be an object with an "extractions" array.')
                        ]),
                        showAdvancedOutputSpec && React.createElement('div', { key: 'advanced', style: { marginTop: '8px' } }, [
                            React.createElement('div', { key: 'extractions-header', style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' } }, [
                                React.createElement('span', { key: 'title', style: { fontWeight: 500 } }, 'Extractions'),
                                React.createElement('button', {
                                    key: 'add',
                                    type: 'button',
                                    className: 'btn btn-secondary',
                                    style: { fontSize: '11px', padding: '2px 8px' },
                                    onClick: handleAddExtraction
                                }, React.createElement('i', { className: 'fas fa-plus', style: { marginRight: '4px' } }), 'Add Extraction')
                            ]),
                            (formData.output_spec?.extractions || []).length === 0 ? React.createElement('div', { key: 'empty', style: { color: '#64748b', fontSize: '12px', margin: '8px 0' } }, 'No extractions defined.') :
                            formData.output_spec.extractions.map((ex, idx) => React.createElement('div', {
                                key: idx,
                                style: { border: '1px solid #d1d5db', borderRadius: '4px', padding: '8px', marginBottom: '8px', background: 'white', position: 'relative' }
                            }, [
                                React.createElement('button', {
                                    key: 'remove',
                                    type: 'button',
                                    className: 'btn btn-danger',
                                    onClick: () => handleRemoveExtraction(idx),
                                    style: { position: 'absolute', top: '4px', right: '4px', fontSize: '10px', padding: '2px 6px' }
                                }, '×'),
                                React.createElement('div', { key: 'fields', style: { display: 'grid', gap: '6px', paddingRight: '30px' } }, [
                                    React.createElement('input', {
                                        key: 'name',
                                        className: 'form-input',
                                        type: 'text',
                                        value: ex.name,
                                        onChange: e => handleUpdateExtraction(idx, { name: e.target.value }),
                                        placeholder: 'Extraction name (output key)',
                                        style: { fontSize: '12px' }
                                    }),
                                    React.createElement('select', {
                                        key: 'type',
                                        className: 'form-select',
                                        value: ex.type,
                                        onChange: e => handleUpdateExtraction(idx, { type: e.target.value }),
                                        style: { fontSize: '12px' }
                                    }, [
                                        React.createElement('option', { key: 'path', value: 'path' }, 'Path'),
                                        React.createElement('option', { key: 'regex', value: 'regex' }, 'Regex'),
                                        React.createElement('option', { key: 'literal', value: 'literal' }, 'Literal'),
                                        React.createElement('option', { key: 'find', value: 'find' }, 'Find')
                                    ]),
                                    React.createElement('input', {
                                        key: 'query',
                                        className: 'form-input',
                                        type: 'text',
                                        value: ex.query,
                                        onChange: e => handleUpdateExtraction(idx, { query: e.target.value }),
                                        placeholder: 'Query (path, regex, or value)',
                                        style: { fontSize: '12px' }
                                    }),
                                    React.createElement('input', {
                                        key: 'default',
                                        className: 'form-input',
                                        type: 'text',
                                        value: ex.default,
                                        onChange: e => handleUpdateExtraction(idx, { default: e.target.value }),
                                        placeholder: 'Default value',
                                        style: { fontSize: '12px' }
                                    }),
                                    React.createElement('select', {
                                        key: 'format',
                                        className: 'form-select',
                                        value: ex.format,
                                        onChange: e => handleUpdateExtraction(idx, { format: e.target.value }),
                                        style: { fontSize: '12px' }
                                    }, [
                                        React.createElement('option', { key: 'text', value: 'text' }, 'Text'),
                                        React.createElement('option', { key: 'number', value: 'number' }, 'Number'),
                                        React.createElement('option', { key: 'boolean', value: 'boolean' }, 'Boolean')
                                    ]),
                                    ex.type === 'find' && React.createElement('textarea', {
                                        key: 'find_criteria',
                                        className: 'form-textarea',
                                        value: JSON.stringify(ex.find_criteria || {}, null, 2),
                                        onChange: e => {
                                            try {
                                                handleUpdateExtraction(idx, { find_criteria: JSON.parse(e.target.value) });
                                            } catch (err) {}
                                        },
                                        placeholder: '{ "array_path": "results", "match_field": "name", ... }',
                                        style: { fontSize: '11px', fontFamily: 'monospace', minHeight: '40px' }
                                    })
                                ])
                            ]))
                        ])
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