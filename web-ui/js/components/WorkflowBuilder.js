// js/components/WorkflowBuilder.js - Enhanced Workflow Builder Component

const WorkflowBuilder = () => {
    const { useState, useEffect } = React;

    const [workflows, setWorkflows] = useState([]);
    const [agents, setAgents] = useState([]);
    const [tools, setTools] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [showExecuteModal, setShowExecuteModal] = useState(false);
    const [editingWorkflow, setEditingWorkflow] = useState(null);
    const [selectedWorkflow, setSelectedWorkflow] = useState(null);
    const [executing, setExecuting] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const [workflowsData, agentsData, toolsData] = await Promise.allSettled([
                api.getWorkflows(),
                api.getAgents(),
                api.getTools()
            ]);
            
            setWorkflows(workflowsData.status === 'fulfilled' ? workflowsData.value : []);
            setAgents(agentsData.status === 'fulfilled' ? agentsData.value : []);
            setTools(toolsData.status === 'fulfilled' ? toolsData.value : []);
        } catch (error) {
            console.error('Failed to load data:', error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateWorkflow = () => {
        setEditingWorkflow(null);
        setShowModal(true);
    };

    const handleEditWorkflow = (workflow) => {
        setEditingWorkflow(workflow);
        setShowModal(true);
    };

    const handleDeleteWorkflow = async (workflowName) => {
        if (confirm(`Are you sure you want to delete workflow "${workflowName}"?`)) {
            try {
                await api.deleteWorkflow(workflowName);
                await loadData();
            } catch (error) {
                alert('Failed to delete workflow: ' + error.message);
            }
        }
    };

    const handleExecuteWorkflow = (workflow) => {
        setSelectedWorkflow(workflow);
        setShowExecuteModal(true);
    };

    const executeWorkflowWithInput = async (inputData) => {
        if (!selectedWorkflow) return;

        try {
            setExecuting(selectedWorkflow.name);
            const result = await api.executeWorkflow(selectedWorkflow.name, inputData);
            
            // Show result in a nice format
            const resultMessage = `Workflow "${selectedWorkflow.name}" executed successfully!\n\n` +
                                `Input: ${JSON.stringify(inputData, null, 2)}\n\n` +
                                `Result: ${typeof result === 'string' ? result : JSON.stringify(result, null, 2)}`;
            
            alert(resultMessage);
        } catch (error) {
            alert('Failed to execute workflow: ' + error.message);
        } finally {
            setExecuting(null);
            setSelectedWorkflow(null);
            setShowExecuteModal(false);
        }
    };

    const getWorkflowInputSummary = (workflow) => {
        if (!workflow.input_schema || !workflow.input_schema.properties) {
            return 'No input required';
        }
        
        const fields = Object.keys(workflow.input_schema.properties);
        const requiredFields = workflow.input_schema.required || [];
        
        if (fields.length === 0) {
            return 'No input required';
        }
        
        return `${fields.length} input field${fields.length > 1 ? 's' : ''} ` +
               `(${requiredFields.length} required)`;
    };

    const hasInputFields = (workflow) => {
        return workflow.input_schema && 
               workflow.input_schema.properties && 
               Object.keys(workflow.input_schema.properties).length > 0;
    };

    if (loading) return React.createElement(Loading, { message: "Loading workflows..." });

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
                }, 'Workflows'),
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
                        onClick: handleCreateWorkflow
                    }, [
                        React.createElement('i', { 
                            key: 'icon',
                            className: 'fas fa-plus' 
                        }),
                        ' Create Workflow'
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
                }, `Debug: Loaded ${workflows.length} workflows, ${agents.length} agents, ${tools.length} tools`),

                workflows.length === 0 ? 
                    React.createElement('div', {
                        key: 'empty',
                        className: 'empty-state'
                    }, [
                        React.createElement('i', {
                            key: 'icon',
                            className: 'fas fa-project-diagram'
                        }),
                        React.createElement('h3', { key: 'title' }, 'No workflows created yet'),
                        React.createElement('p', { key: 'description' }, 'Create your first workflow to automate tasks!'),
                        React.createElement('button', {
                            key: 'cta',
                            className: 'btn btn-primary',
                            onClick: handleCreateWorkflow
                        }, [
                            React.createElement('i', { 
                                key: 'icon',
                                className: 'fas fa-plus' 
                            }),
                            ' Create Your First Workflow'
                        ])
                    ]) :
                    React.createElement('div', {
                        key: 'list',
                        className: 'item-list'
                    }, workflows.map(workflow => 
                        React.createElement('div', {
                            key: workflow.id || workflow.name,
                            className: 'item-card'
                        }, [
                            React.createElement('div', { 
                                key: 'info',
                                className: 'item-info' 
                            }, [
                                React.createElement('div', {
                                    key: 'header',
                                    style: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }
                                }, [
                                    React.createElement('h4', { 
                                        key: 'name',
                                        style: { margin: 0 }
                                    }, workflow.name),
                                    React.createElement('span', {
                                        key: 'status',
                                        className: `status ${workflow.enabled ? 'status-online' : 'status-offline'}`
                                    }, workflow.enabled ? 'Enabled' : 'Disabled'),
                                    hasInputFields(workflow) && React.createElement('span', {
                                        key: 'input-indicator',
                                        style: {
                                            fontSize: '11px',
                                            background: '#dbeafe',
                                            color: '#1e40af',
                                            padding: '2px 6px',
                                            borderRadius: '4px'
                                        }
                                    }, '📝 Has Input')
                                ]),
                                React.createElement('p', { 
                                    key: 'description',
                                    style: { margin: '0 0 8px 0' }
                                }, workflow.description),
                                React.createElement('div', {
                                    key: 'details',
                                    style: { fontSize: '12px', color: '#64748b' }
                                }, [
                                    React.createElement('div', { 
                                        key: 'steps' 
                                    }, `Steps: ${workflow.steps?.length || 0}`),
                                    React.createElement('div', { 
                                        key: 'input' 
                                    }, `Input: ${getWorkflowInputSummary(workflow)}`),
                                    hasInputFields(workflow) && React.createElement('div', {
                                        key: 'input-fields',
                                        style: { 
                                            marginTop: '4px',
                                            fontSize: '11px',
                                            color: '#6b7280'
                                        }
                                    }, `Fields: ${Object.keys(workflow.input_schema.properties).join(', ')}`)
                                ])
                            ]),
                            React.createElement('div', { 
                                key: 'actions',
                                className: 'item-actions' 
                            }, [
                                React.createElement('button', {
                                    key: 'execute',
                                    className: 'btn btn-success',
                                    onClick: () => handleExecuteWorkflow(workflow),
                                    disabled: executing === workflow.name || !workflow.enabled
                                }, executing === workflow.name ? [
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
                                    hasInputFields(workflow) ? ' Execute...' : ' Execute'
                                ]),
                                React.createElement('button', {
                                    key: 'edit',
                                    className: 'btn btn-secondary',
                                    onClick: () => handleEditWorkflow(workflow)
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
                                    onClick: () => handleDeleteWorkflow(workflow.name)
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

        // Create/Edit Modal
        showModal && React.createElement(WorkflowModal, {
            key: 'modal',
            workflow: editingWorkflow,
            agents: agents,
            tools: tools,
            onClose: () => setShowModal(false),
            onSave: loadData
        }),

        // Execute Modal
        showExecuteModal && selectedWorkflow && React.createElement(WorkflowExecutionModal, {
            key: 'execute-modal',
            workflow: selectedWorkflow,
            onClose: () => {
                setShowExecuteModal(false);
                setSelectedWorkflow(null);
            },
            onExecute: executeWorkflowWithInput
        })
    ]);
};

// Make component globally available
window.WorkflowBuilder = WorkflowBuilder;