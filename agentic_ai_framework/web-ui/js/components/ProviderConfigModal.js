// js/components/ProviderConfigModal.js - Provider Configuration Modal

const ProviderConfigModal = ({ provider, onClose, onSave }) => {
    const { useState, useEffect } = React;

    const [formData, setFormData] = useState({
        provider_name: '',
        enabled: true,
        api_key: '',
        base_url: '',
        default_model: '',
        timeout: 120,
        aws_access_key_id: '',
        aws_secret_access_key: ''
    });
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (provider) {
            loadProviderConfig();
        }
    }, [provider]);

    // Update form when provider_name changes (for new providers)
    useEffect(() => {
        if (!provider && formData.provider_name) {
            updateFormData('base_url', getDefaultBaseUrl(formData.provider_name));
        }
    }, [formData.provider_name, provider]);

    const loadProviderConfig = async () => {
        try {
            setLoading(true);
            const config = await api.request(`/providers/${provider}/config`);
            setFormData({
                enabled: config.config.enabled !== false,
                api_key: config.config.api_key || '',
                base_url: config.config.base_url || getDefaultBaseUrl(provider),
                default_model: config.config.default_model || '',
                timeout: config.config.timeout || 120,
                aws_access_key_id: config.config.aws_access_key_id || '',
                aws_secret_access_key: config.config.aws_secret_access_key || ''
            });
        } catch (error) {
            console.error('Failed to load provider config:', error);
            // Set defaults for new provider
            setFormData({
                enabled: true,
                api_key: '',
                base_url: getDefaultBaseUrl(provider),
                default_model: '',
                timeout: 120,
                aws_access_key_id: '',
                aws_secret_access_key: ''
            });
        } finally {
            setLoading(false);
        }
    };

    const getDefaultBaseUrl = (providerName) => {
        switch (providerName) {
            case 'ollama':
                return 'http://localhost:11434';
            case 'openai':
                return 'https://api.openai.com/v1';
            case 'openrouter':
                return 'https://openrouter.ai/api/v1';
            case 'bedrock':
                return 'us-east-1';
            default:
                return '';
        }
    };

    const getProviderDocumentation = (providerName) => {
        switch (providerName) {
            case 'ollama':
                return {
                    description: 'Local AI models running on your machine',
                    apiKeyRequired: false,
                    baseUrlDefault: 'http://localhost:11434',
                    notes: 'Make sure Ollama is running locally'
                };
            case 'openai':
                return {
                    description: 'OpenAI GPT models (GPT-4, GPT-3.5, etc.)',
                    apiKeyRequired: true,
                    baseUrlDefault: 'https://api.openai.com/v1',
                    notes: 'Requires OpenAI API key from platform.openai.com'
                };
            case 'openrouter':
                return {
                    description: 'Access to multiple AI models through OpenRouter',
                    apiKeyRequired: true,
                    baseUrlDefault: 'https://openrouter.ai/api/v1',
                    notes: 'Requires OpenRouter API key from openrouter.ai'
                };
            case 'bedrock':
                return {
                    description: 'AWS Bedrock models (Claude, Titan, Llama)',
                    apiKeyRequired: true,
                    baseUrlDefault: 'us-east-1',
                    notes: 'Requires AWS credentials. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables or use IAM roles.'
                };
            default:
                return {
                    description: 'Custom AI provider',
                    apiKeyRequired: true,
                    baseUrlDefault: '',
                    notes: 'Configure according to your provider documentation'
                };
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!provider && !formData.provider_name) {
            alert('Provider name is required');
            return;
        }

        try {
            setSaving(true);
            
            const providerName = provider || formData.provider_name;
            await api.request(`/providers/${providerName}/configure`, {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            alert(`Provider "${providerName}" configured successfully!`);
            await onSave();
            onClose();
        } catch (error) {
            alert(`Failed to configure provider: ${error.message}`);
        } finally {
            setSaving(false);
        }
    };

    const handleReloadProviders = async () => {
        try {
            await api.request('/providers/reload', { method: 'POST' });
            alert('All providers reloaded successfully!');
            await onSave();
        } catch (error) {
            alert(`Failed to reload providers: ${error.message}`);
        }
    };

    const updateFormData = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const providerInfo = getProviderDocumentation(provider || formData.provider_name || 'custom');

    if (loading) {
        return React.createElement('div', {
            className: 'modal-overlay',
            onClick: onClose
        }, 
            React.createElement('div', {
                className: 'modal',
                onClick: e => e.stopPropagation()
            }, React.createElement(Loading, { message: "Loading provider configuration..." }))
        );
    }

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
                }, provider ? `Configure ${provider}` : 'Add New Provider'),
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
                    // Provider Info
                    React.createElement('div', {
                        key: 'info',
                        style: {
                            padding: '16px',
                            background: '#f8fafc',
                            borderRadius: '8px',
                            marginBottom: '20px',
                            border: '1px solid #e2e8f0'
                        }
                    }, [
                        React.createElement('h4', {
                            key: 'title',
                            style: { margin: '0 0 8px 0', color: '#374151' }
                        }, provider || 'Custom Provider'),
                        React.createElement('p', {
                            key: 'description',
                            style: { margin: '0 0 8px 0', fontSize: '14px', color: '#64748b' }
                        }, providerInfo.description),
                        React.createElement('p', {
                            key: 'notes',
                            style: { margin: 0, fontSize: '12px', color: '#6b7280' }
                        }, `💡 ${providerInfo.notes}`)
                    ]),

                    // Provider Name (for new providers)
                    !provider && React.createElement('div', { 
                        key: 'name-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Provider Name'),
                        React.createElement('select', {
                            key: 'select',
                            className: 'form-select',
                            value: formData.provider_name || '',
                            onChange: e => updateFormData('provider_name', e.target.value),
                            required: true
                        }, [
                            React.createElement('option', { key: 'empty', value: '' }, 'Select provider type'),
                            React.createElement('option', { key: 'ollama', value: 'ollama' }, 'Ollama (Local)'),
                            React.createElement('option', { key: 'openai', value: 'openai' }, 'OpenAI'),
                            React.createElement('option', { key: 'openrouter', value: 'openrouter' }, 'OpenRouter'),
                            React.createElement('option', { key: 'bedrock', value: 'bedrock' }, 'AWS Bedrock')
                        ])
                    ]),

                    // Enabled Toggle
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
                            }, 'Enable this provider')
                        ])
                    ),

                    // API Key (if required and not Bedrock)
                    providerInfo.apiKeyRequired && (provider || formData.provider_name) !== 'bedrock' && React.createElement('div', { 
                        key: 'apikey-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'API Key'),
                        React.createElement('input', {
                            key: 'input',
                            className: 'form-input',
                            type: 'password',
                            value: formData.api_key,
                            onChange: e => updateFormData('api_key', e.target.value),
                            placeholder: 'Enter your API key',
                            required: providerInfo.apiKeyRequired
                        })
                    ]),

                    // AWS Credentials (for Bedrock)
                    (provider || formData.provider_name) === 'bedrock' && React.createElement('div', { 
                        key: 'aws-credentials',
                        style: { marginBottom: '20px' }
                    }, [
                        React.createElement('h4', {
                            key: 'title',
                            style: { margin: '0 0 12px 0', color: '#374151', fontSize: '16px' }
                        }, 'AWS Credentials'),
                        React.createElement('div', { 
                            key: 'access-key-group',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'AWS Access Key ID'),
                            React.createElement('input', {
                                key: 'input',
                                className: 'form-input',
                                type: 'text',
                                value: formData.aws_access_key_id || '',
                                onChange: e => updateFormData('aws_access_key_id', e.target.value),
                                placeholder: 'Enter your AWS Access Key ID',
                                required: true
                            })
                        ]),
                        React.createElement('div', { 
                            key: 'secret-key-group',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'AWS Secret Access Key'),
                            React.createElement('input', {
                                key: 'input',
                                className: 'form-input',
                                type: 'password',
                                value: formData.aws_secret_access_key || '',
                                onChange: e => updateFormData('aws_secret_access_key', e.target.value),
                                placeholder: 'Enter your AWS Secret Access Key',
                                required: true
                            })
                        ])
                    ]),

                    // Base URL
                    React.createElement('div', { 
                        key: 'baseurl-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Base URL'),
                        React.createElement('input', {
                            key: 'input',
                            className: 'form-input',
                            type: 'url',
                            value: formData.base_url,
                            onChange: e => updateFormData('base_url', e.target.value),
                            placeholder: providerInfo.baseUrlDefault,
                            required: true
                        })
                    ]),

                    // Default Model
                    React.createElement('div', { 
                        key: 'model-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Default Model (Optional)'),
                        React.createElement('input', {
                            key: 'input',
                            className: 'form-input',
                            type: 'text',
                            value: formData.default_model,
                            onChange: e => updateFormData('default_model', e.target.value),
                            placeholder: 'e.g., gpt-4, llama3.2:3b'
                        })
                    ]),

                    // Timeout
                    React.createElement('div', { 
                        key: 'timeout-group',
                        className: 'form-group' 
                    }, [
                        React.createElement('label', { 
                            key: 'label',
                            className: 'form-label' 
                        }, 'Timeout (seconds)'),
                        React.createElement('input', {
                            key: 'input',
                            className: 'form-input',
                            type: 'number',
                            min: '30',
                            max: '600',
                            value: formData.timeout,
                            onChange: e => updateFormData('timeout', parseInt(e.target.value)),
                            required: true
                        })
                    ])
                ]),

                // Modal Footer
                React.createElement('div', { 
                    key: 'footer',
                    className: 'modal-footer' 
                }, [
                    React.createElement('button', {
                        key: 'reload',
                        type: 'button',
                        className: 'btn btn-secondary',
                        onClick: handleReloadProviders
                    }, [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-sync' 
                        }),
                        ' Reload All'
                    ]),
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
                    ] : [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-save' 
                        }),
                        ' Save Configuration'
                    ])
                ])
            ])
        ])
    );
};

// Make component globally available
window.ProviderConfigModal = ProviderConfigModal;