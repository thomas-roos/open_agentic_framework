// js/components/AgentManagement.js - Agent Management Component

const AgentManagement = () => {
    const { useState, useEffect } = React;

    const [agents, setAgents] = useState([]);
    const [tools, setTools] = useState([]);
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingAgent, setEditingAgent] = useState(null);
    const [executing, setExecuting] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            console.log('Loading agents, tools, and models...');
            
            // Load all data in parallel
            const [agentsData, toolsData, modelsData] = await Promise.allSettled([
                api.getAgents(),
                api.getTools(),
                api.getModels()
            ]);

            // Process agents
            if (agentsData.status === 'fulfilled') {
                const agents = Array.isArray(agentsData.value) ? agentsData.value : [];
                console.log('Agents loaded:', agents);
                setAgents(agents);
            } else {
                console.error('Failed to load agents:', agentsData.reason);
                setAgents([]);
            }

            // Process tools
            if (toolsData.status === 'fulfilled') {
                const tools = Array.isArray(toolsData.value) ? toolsData.value : [];
                console.log('Tools loaded:', tools);
                setTools(tools);
            } else {
                console.error('Failed to load tools:', toolsData.reason);
                setTools([]);
            }

            // Process models
            if (modelsData.status === 'fulfilled') {
                const models = Array.isArray(modelsData.value) ? modelsData.value : [];
                console.log('Models loaded:', models);
                setModels(models);
            } else {
                console.error('Failed to load models:', modelsData.reason);
                // Use fallback models
                setModels(api.getFallbackModels());
            }
            
        } catch (error) {
            console.error('Failed to load data:', error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateAgent = () => {
        setEditingAgent(null);
        setShowModal(true);
    };

    const handleEditAgent = (agent) => {
        setEditingAgent(agent);
        setShowModal(true);
    };

    const handleDeleteAgent = async (agentName) => {
        if (confirm(`Are you sure you want to delete agent "${agentName}"?`)) {
            try {
                await api.deleteAgent(agentName);
                await loadData();
            } catch (error) {
                alert('Failed to delete agent: ' + error.message);
            }
        }
    };

    const handleExecuteAgent = async (agentName) => {
        const task = prompt('Enter task for the agent:');
        if (!task) return;

        try {
            setExecuting(agentName);
            const result = await api.executeAgent(agentName, task);
            alert(`Agent executed successfully!\n\nResult: ${result.result || JSON.stringify(result, null, 2)}`);
        } catch (error) {
            alert('Failed to execute agent: ' + error.message);
        } finally {
            setExecuting(null);
        }
    };

    if (loading) return React.createElement(Loading);

    if (error) {
        return React.createElement('div', { className: 'card' },
            React.createElement('div', { className: 'card-content' },
                React.createElement('div', {
                    style: {
                        textAlign: 'center',
                        padding: '40px',
                        color: '#ef4444'
                    }
                }, [
                    React.createElement('i', {
                        key: 'icon',
                        className: 'fas fa-exclamation-triangle',
                        style: { fontSize: '48px', marginBottom: '16px' }
                    }),
                    React.createElement('p', { key: 'message' }, `Error loading data: ${error}`),
                    React.createElement('button', {
                        key: 'retry',
                        className: 'btn btn-primary',
                        onClick: loadData,
                        style: { marginTop: '16px' }
                    }, [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-refresh' 
                        }),
                        ' Retry'
                    ])
                ])
            )
        );
    }

    return React.createElement('div', {}, [
        React.createElement('div', { 
            key: 'main-card',
            className: 'card' 
        }, [
            React.createElement('div', { 
                key: 'header',
                className: 'card-header' 
            }, [
                React.createElement('h3', { 
                    key: 'title',
                    className: 'card-title' 
                }, 'AI Agents'),
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
                        key: 'create',
                        className: 'btn btn-primary',
                        onClick: handleCreateAgent
                    }, [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-plus' 
                        }),
                        ' Create Agent'
                    ])
                ])
            ]),
            React.createElement('div', { 
                key: 'content',
                className: 'card-content' 
            }, [
                // Debug Info
                React.createElement('div', {
                    key: 'debug',
                    className: 'debug-info'
                }, `Debug: Loaded ${agents.length} agents, ${tools.length} tools, ${models.length} models`),

                // Agents List or Empty State
                agents.length === 0 
                    ? React.createElement('div', {
                        key: 'empty',
                        className: 'empty-state'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-robot'
                        }),
                        React.createElement('h3', { 
                            key: 'title' 
                        }, 'No agents created yet'),
                        React.createElement('p', { 
                            key: 'description' 
                        }, 'Create your first agent to get started!'),
                        React.createElement('button', {
                            key: 'cta',
                            className: 'btn btn-primary',
                            onClick: handleCreateAgent
                        }, [
                            React.createElement('i', { 
                                key: 'icon',
                                className: 'fas fa-plus' 
                            }),
                            ' Create Your First Agent'
                        ])
                    ])
                    : React.createElement('div', {
                        key: 'list',
                        className: 'item-list'
                    }, agents.map(agent => 
                        React.createElement('div', {
                            key: agent.id || agent.name,
                            className: 'item-card'
                        }, [
                            React.createElement('div', { 
                                key: 'info',
                                className: 'item-info' 
                            }, [
                                React.createElement('h4', { key: 'name' }, agent.name),
                                React.createElement('p', { key: 'role' }, agent.role),
                                React.createElement('p', {
                                    key: 'details',
                                    style: { fontSize: '12px', color: '#64748b' }
                                }, [
                                    `Model: ${agent.ollama_model || 'Not specified'}`,
                                    React.createElement('br', { key: 'br' }),
                                    `Tools: ${agent.tools?.length ? agent.tools.join(', ') : 'None'}`
                                ])
                            ]),
                            React.createElement('div', { 
                                key: 'actions',
                                className: 'item-actions' 
                            }, [
                                React.createElement('button', {
                                    key: 'execute',
                                    className: 'btn btn-success',
                                    onClick: () => handleExecuteAgent(agent.name),
                                    disabled: executing === agent.name
                                }, executing === agent.name ? [
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
                                    ' Execute'
                                ]),
                                React.createElement('button', {
                                    key: 'edit',
                                    className: 'btn btn-secondary',
                                    onClick: () => handleEditAgent(agent)
                                }, [
                                    React.createElement('i', { 
                                        key: 'icon',
                                        className: 'fas fa-edit' 
                                    }),
                                    ' Edit'
                                ]),
                                React.createElement('button', {
                                    key: 'delete',
                                    className: 'btn btn-danger',
                                    onClick: () => handleDeleteAgent(agent.name)
                                }, [
                                    React.createElement('i', { 
                                        key: 'icon',
                                        className: 'fas fa-trash' 
                                    }),
                                    ' Delete'
                                ])
                            ])
                        ])
                    ))
            ])
        ]),

        // Modal
        showModal && React.createElement(AgentModal, {
            key: 'modal',
            agent: editingAgent,
            tools: tools,
            models: models,
            onClose: () => setShowModal(false),
            onSave: loadData
        })
    ]);
};

// Make component globally available
window.AgentManagement = AgentManagement;