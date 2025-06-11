// js/components/WorkflowBuilder.js - Workflow Builder Component

const WorkflowBuilder = () => {
    const { useState, useEffect } = React;

    const [workflows, setWorkflows] = useState([]);
    const [agents, setAgents] = useState([]);
    const [tools, setTools] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingWorkflow, setEditingWorkflow] = useState(null);
    const [executing, setExecuting] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
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
        } finally {
            setLoading(false);
        }
    };

    const handleCreateWorkflow = () => {
        setEditingWorkflow(null);
        setShowModal(true);
    };

    const handleExecuteWorkflow = async (workflowName) => {
        try {
            setExecuting(workflowName);
            const result = await api.executeWorkflow(workflowName);
            alert(`Workflow executed successfully!\n\nResult: ${JSON.stringify(result, null, 2)}`);
        } catch (error) {
            alert('Failed to execute workflow: ' + error.message);
        } finally {
            setExecuting(null);
        }
    };

    if (loading) return React.createElement(Loading, { message: "Loading workflows..." });

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
            ]),
            React.createElement('div', { 
                key: 'content',
                className: 'card-content' 
            }, 
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
                                React.createElement('h4', { key: 'name' }, workflow.name),
                                React.createElement('p', { key: 'description' }, workflow.description),
                                React.createElement('p', {
                                    key: 'details',
                                    style: { fontSize: '12px', color: '#64748b' }
                                }, `${workflow.steps?.length || 0} steps | ${workflow.enabled ? 'Enabled' : 'Disabled'}`)
                            ]),
                            React.createElement('div', { 
                                key: 'actions',
                                className: 'item-actions' 
                            }, [
                                React.createElement('button', {
                                    key: 'execute',
                                    className: 'btn btn-success',
                                    onClick: () => handleExecuteWorkflow(workflow.name),
                                    disabled: executing === workflow.name
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
                                    ' Execute'
                                ]),
                                React.createElement('button', {
                                    key: 'edit',
                                    className: 'btn btn-secondary',
                                    onClick: () => {
                                        setEditingWorkflow(workflow);
                                        setShowModal(true);
                                    }
                                }, [
                                    React.createElement('i', { 
                                        key: 'icon',
                                        className: 'fas fa-edit' 
                                    }),
                                    ' Edit'
                                ])
                            ])
                        ])
                    ))
            )
        ]),

        // Modal (if WorkflowModal is available)
        showModal && window.WorkflowModal && React.createElement(WorkflowModal, {
            key: 'modal',
            workflow: editingWorkflow,
            agents: agents,
            tools: tools,
            onClose: () => setShowModal(false),
            onSave: loadData
        })
    ]);
};

// Make component globally available
window.WorkflowBuilder = WorkflowBuilder;