// js/components/ProviderManagement.js - Provider Management Component

const ProviderManagement = () => {
    const { useState, useEffect } = React;

    const [providers, setProviders] = useState({});
    const [models, setModels] = useState([]);
    const [modelStatus, setModelStatus] = useState({});
    const [loading, setLoading] = useState(true);
    const [showInstallModal, setShowInstallModal] = useState(false);
    const [showProviderModal, setShowProviderModal] = useState(false);
    const [selectedProvider, setSelectedProvider] = useState(null);
    const [installing, setInstalling] = useState(null);
    const [testing, setTesting] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [providersData, modelsData, statusData] = await Promise.allSettled([
                api.getProviders(),
                api.getModels(),
                api.request('/models/status')
            ]);

            if (providersData.status === 'fulfilled') {
                setProviders(providersData.value.providers || {});
            }

            if (modelsData.status === 'fulfilled') {
                setModels(modelsData.value || []);
            }

            if (statusData.status === 'fulfilled') {
                setModelStatus(statusData.value || {});
            }
        } catch (error) {
            console.error('Failed to load provider data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTestModel = async (modelName) => {
        try {
            setTesting(modelName);
            const result = await api.request(`/models/test/${encodeURIComponent(modelName)}`, {
                method: 'POST'
            });
            
            if (result.test_successful) {
                alert(`Model test successful!\n\nResponse: ${result.response}`);
            } else {
                alert(`Model test failed!\n\nError: ${result.error}`);
            }
        } catch (error) {
            alert(`Model test failed: ${error.message}`);
        } finally {
            setTesting(null);
        }
    };

    const handleDeleteModel = async (modelName) => {
        if (!confirm(`Are you sure you want to delete model "${modelName}"?`)) return;

        try {
            await api.request(`/models/${encodeURIComponent(modelName)}`, {
                method: 'DELETE'
            });
            alert(`Model "${modelName}" deleted successfully!`);
            await loadData();
        } catch (error) {
            alert(`Failed to delete model: ${error.message}`);
        }
    };

    const handleReloadModels = async () => {
        try {
            await api.request('/providers/reload-models', { method: 'POST' });
            alert('Models reloaded successfully!');
            await loadData();
        } catch (error) {
            alert(`Failed to reload models: ${error.message}`);
        }
    };

    const handleProviderHealthCheck = async (providerName) => {
        try {
            const result = await api.request(`/providers/${providerName}/health-check`, {
                method: 'POST'
            });
            alert(`Provider health check:\n${providerName}: ${result.is_healthy ? 'Healthy' : 'Unhealthy'}`);
        } catch (error) {
            alert(`Health check failed: ${error.message}`);
        }
    };

    if (loading) return React.createElement(Loading, { message: "Loading providers..." });

    return React.createElement('div', {}, [
        // Providers Section
        React.createElement('div', { 
            key: 'providers-card',
            className: 'card' 
        }, [
            React.createElement('div', { 
                key: 'header',
                className: 'card-header' 
            }, [
                React.createElement('h3', { 
                    key: 'title',
                    className: 'card-title' 
                }, 'LLM Providers'),
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
                        key: 'reload-models',
                        className: 'btn btn-secondary',
                        onClick: handleReloadModels
                    }, [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-sync' 
                        }),
                        ' Reload Models'
                    ]),
                    React.createElement('button', {
                        key: 'configure',
                        className: 'btn btn-primary',
                        onClick: () => setShowProviderModal(true)
                    }, [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-cog' 
                        }),
                        ' Configure Provider'
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
                }, `Debug: ${Object.keys(providers).length} providers, ${models.length} models`),

                Object.keys(providers).length === 0 ? 
                    React.createElement('div', {
                        key: 'empty',
                        className: 'empty-state'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-server'
                        }),
                        React.createElement('h3', { key: 'title' }, 'No providers configured'),
                        React.createElement('p', { key: 'description' }, 'Configure your first LLM provider to get started!')
                    ]) :
                    React.createElement('div', {
                        key: 'providers-grid',
                        className: 'grid grid-3'
                    }, Object.entries(providers).map(([name, provider]) => 
                        React.createElement('div', {
                            key: name,
                            className: 'card'
                        }, [
                            React.createElement('div', { 
                                key: 'header',
                                className: 'card-header' 
                            }, [
                                React.createElement('h4', { 
                                    key: 'title',
                                    className: 'card-title' 
                                }, name),
                                React.createElement('span', {
                                    key: 'status',
                                    className: `status ${provider.is_healthy ? 'status-online' : 'status-offline'}`
                                }, provider.is_healthy ? 'Healthy' : 'Offline')
                            ]),
                            React.createElement('div', { 
                                key: 'content',
                                className: 'card-content' 
                            }, [
                                React.createElement('p', {
                                    key: 'models',
                                    style: { marginBottom: '12px' }
                                }, `${provider.model_count || 0} models available`),
                                React.createElement('p', {
                                    key: 'status',
                                    style: { fontSize: '12px', color: '#64748b' }
                                }, `Initialized: ${provider.is_initialized ? 'Yes' : 'No'}`),
                                React.createElement('div', {
                                    key: 'actions',
                                    style: { marginTop: '16px', display: 'flex', gap: '8px' }
                                }, [
                                    React.createElement('button', {
                                        key: 'health',
                                        className: 'btn btn-secondary',
                                        onClick: () => handleProviderHealthCheck(name),
                                        style: { fontSize: '12px', padding: '4px 8px' }
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-heartbeat' 
                                        }),
                                        ' Health'
                                    ]),
                                    React.createElement('button', {
                                        key: 'configure',
                                        className: 'btn btn-primary',
                                        onClick: () => {
                                            setSelectedProvider(name);
                                            setShowProviderModal(true);
                                        },
                                        style: { fontSize: '12px', padding: '4px 8px' }
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-cog' 
                                        }),
                                        ' Config'
                                    ])
                                ])
                            ])
                        ])
                    ))
            ])
        ]),

        // Models Section
        React.createElement('div', { 
            key: 'models-card',
            className: 'card' 
        }, [
            React.createElement('div', { 
                key: 'header',
                className: 'card-header' 
            }, [
                React.createElement('h3', { 
                    key: 'title',
                    className: 'card-title' 
                }, 'Available Models'),
                React.createElement('button', {
                    key: 'install',
                    className: 'btn btn-primary',
                    onClick: () => setShowInstallModal(true)
                }, [
                    React.createElement('i', { 
                        key: 'icon',
                        className: 'fas fa-download' 
                    }),
                    ' Install Model'
                ])
            ]),
            React.createElement('div', { 
                key: 'content',
                className: 'card-content' 
            }, 
                models.length === 0 ? 
                    React.createElement('div', {
                        key: 'empty',
                        className: 'empty-state'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-brain'
                        }),
                        React.createElement('h3', { key: 'title' }, 'No models available'),
                        React.createElement('p', { key: 'description' }, 'Install your first model to get started!')
                    ]) :
                    React.createElement('div', {
                        key: 'models-grid',
                        className: 'grid grid-2'
                    }, models.map(model => 
                        React.createElement('div', {
                            key: model.name || model,
                            className: 'card'
                        }, [
                            React.createElement('div', { 
                                key: 'header',
                                className: 'card-header' 
                            }, [
                                React.createElement('h4', { 
                                    key: 'title',
                                    className: 'card-title' 
                                }, typeof model === 'string' ? model : model.name),
                                React.createElement('span', {
                                    key: 'provider',
                                    className: 'status status-online'
                                }, typeof model === 'string' ? 'ollama' : model.provider)
                            ]),
                            React.createElement('div', { 
                                key: 'content',
                                className: 'card-content' 
                            }, [
                                typeof model !== 'string' && model.description && React.createElement('p', {
                                    key: 'description',
                                    style: { marginBottom: '12px', fontSize: '14px', color: '#64748b' }
                                }, model.description),
                                
                                React.createElement('div', {
                                    key: 'actions',
                                    style: { display: 'flex', gap: '8px', flexWrap: 'wrap' }
                                }, [
                                    React.createElement('button', {
                                        key: 'test',
                                        className: 'btn btn-success',
                                        onClick: () => handleTestModel(typeof model === 'string' ? model : model.name),
                                        disabled: testing === (typeof model === 'string' ? model : model.name)
                                    }, testing === (typeof model === 'string' ? model : model.name) ? [
                                        React.createElement('div', {
                                            key: 'spinner',
                                            className: 'spinner',
                                            style: { width: '12px', height: '12px' }
                                        }),
                                        'Testing...'
                                    ] : [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-play' 
                                        }),
                                        ' Test'
                                    ]),
                                    React.createElement('button', {
                                        key: 'delete',
                                        className: 'btn btn-danger',
                                        onClick: () => handleDeleteModel(typeof model === 'string' ? model : model.name)
                                    }, [
                                        React.createElement('i', { 
                                            key: 'icon',
                                            className: 'fas fa-trash' 
                                        }),
                                        ' Delete'
                                    ])
                                ])
                            ])
                        ])
                    ))
            )
        ]),

        // Modals
        showInstallModal && React.createElement(ModelInstallModal, {
            key: 'install-modal',
            onClose: () => setShowInstallModal(false),
            onInstall: loadData
        }),

        showProviderModal && React.createElement(ProviderConfigModal, {
            key: 'provider-modal',
            provider: selectedProvider,
            onClose: () => {
                setShowProviderModal(false);
                setSelectedProvider(null);
            },
            onSave: loadData
        })
    ]);
};

// Make component globally available
window.ProviderManagement = ProviderManagement;