// js/components/ModelInstallModal.js - Model Install Modal Component

const ModelInstallModal = ({ onClose, onInstall }) => {
    const { useState } = React;

    const [modelName, setModelName] = useState('');
    const [waitForCompletion, setWaitForCompletion] = useState(false);
    const [installing, setInstalling] = useState(false);

    const popularModels = [
        { name: 'tinyllama:1.1b', description: 'Tiny 1.1B parameter model - very fast' },
        { name: 'granite3.2:2b', description: 'IBM Granite 3.2B - good balance of speed and quality' },
        { name: 'phi3:mini', description: 'Microsoft Phi-3 Mini - efficient and capable' },
        { name: 'deepseek-r1:1.5b', description: 'DeepSeek R1 1.5B - reasoning focused' },
        { name: 'llama3.2:1b', description: 'Meta Llama 3.2 1B - latest from Meta' },
        { name: 'llama3.2:3b', description: 'Meta Llama 3.2 3B - more capable version' },
        { name: 'qwen2.5:1.5b', description: 'Qwen 2.5 1.5B - multilingual support' },
        { name: 'gemma2:2b', description: 'Google Gemma 2 2B - efficient and powerful' }
    ];

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!modelName.trim()) {
            alert('Please enter a model name');
            return;
        }

        try {
            setInstalling(true);
            
            const response = await api.request('/models/install', {
                method: 'POST',
                body: JSON.stringify({
                    model_name: modelName.trim(),
                    wait_for_completion: waitForCompletion
                })
            });

            if (waitForCompletion) {
                alert(`Model "${modelName}" installed successfully!`);
            } else {
                alert(`Model "${modelName}" installation started in background. Check the logs for progress.`);
            }

            await onInstall();
            onClose();
        } catch (error) {
            alert(`Failed to install model: ${error.message}`);
        } finally {
            setInstalling(false);
        }
    };

    const selectModel = (model) => {
        setModelName(model.name);
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
                }, 'Install New Model'),
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
                    // Popular Models Section
                    React.createElement('div', { 
                        key: 'popular-section',
                        style: { marginBottom: '24px' }
                    }, [
                        React.createElement('h4', { 
                            key: 'title',
                            style: { marginBottom: '16px' }
                        }, 'Popular Models'),
                        React.createElement('div', {
                            key: 'models-grid',
                            style: {
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                                gap: '12px'
                            }
                        }, popularModels.map(model => 
                            React.createElement('div', {
                                key: model.name,
                                className: 'card',
                                style: {
                                    padding: '12px',
                                    cursor: 'pointer',
                                    border: modelName === model.name ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                                    background: modelName === model.name ? '#f0f9ff' : 'white'
                                },
                                onClick: () => selectModel(model)
                            }, [
                                React.createElement('h5', { 
                                    key: 'name',
                                    style: { 
                                        margin: '0 0 4px 0', 
                                        fontSize: '14px',
                                        fontWeight: '600' 
                                    }
                                }, model.name),
                                React.createElement('p', {
                                    key: 'description',
                                    style: { 
                                        margin: 0, 
                                        fontSize: '12px', 
                                        color: '#64748b' 
                                    }
                                }, model.description)
                            ])
                        ))
                    ]),

                    // Custom Model Input
                    React.createElement('div', { 
                        key: 'custom-section' 
                    }, [
                        React.createElement('h4', { 
                            key: 'title',
                            style: { marginBottom: '16px' }
                        }, 'Or Enter Custom Model'),
                        React.createElement('div', { 
                            key: 'model-group',
                            className: 'form-group' 
                        }, [
                            React.createElement('label', { 
                                key: 'label',
                                className: 'form-label' 
                            }, 'Model Name'),
                            React.createElement('input', {
                                key: 'input',
                                className: 'form-input',
                                type: 'text',
                                value: modelName,
                                onChange: e => setModelName(e.target.value),
                                placeholder: 'e.g., llama3.2:3b, codellama:7b, mistral:7b',
                                required: true
                            }),
                            React.createElement('small', {
                                key: 'help',
                                style: { color: '#64748b', fontSize: '12px' }
                            }, 'Enter the model name as it appears in the Ollama library')
                        ]),

                        // Options
                        React.createElement('div', { 
                            key: 'options-group',
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
                                    checked: waitForCompletion,
                                    onChange: e => setWaitForCompletion(e.target.checked)
                                }),
                                React.createElement('span', { 
                                    key: 'label' 
                                }, 'Wait for installation to complete'),
                                React.createElement('small', {
                                    key: 'help',
                                    style: { color: '#64748b', fontSize: '11px' }
                                }, '(recommended for smaller models)')
                            ])
                        ),

                        // Warning
                        React.createElement('div', {
                            key: 'warning',
                            style: {
                                padding: '12px',
                                background: '#fef3c7',
                                border: '1px solid #f59e0b',
                                borderRadius: '6px',
                                marginTop: '16px'
                            }
                        }, [
                            React.createElement('p', {
                                key: 'text',
                                style: { 
                                    margin: 0, 
                                    fontSize: '12px', 
                                    color: '#92400e' 
                                }
                            }, '⚠️ Large models may take several minutes to download and require significant disk space. Ensure you have sufficient storage and a stable internet connection.')
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
                        disabled: installing || !modelName.trim()
                    }, installing ? [
                        React.createElement('div', { 
                            key: 'spinner',
                            className: 'spinner',
                            style: { width: '12px', height: '12px' }
                        }),
                        'Installing...'
                    ] : [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-download' 
                        }),
                        ' Install Model'
                    ])
                ])
            ])
        ])
    );
};

// Make component globally available
window.ModelInstallModal = ModelInstallModal;