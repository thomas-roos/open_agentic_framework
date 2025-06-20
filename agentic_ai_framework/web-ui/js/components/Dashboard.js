// js/components/Dashboard.js - Dashboard Component

const Dashboard = () => {
    const { useState, useEffect } = React;

    const [health, setHealth] = useState(null);
    const [providers, setProviders] = useState(null);
    const [memoryStats, setMemoryStats] = useState(null);
    const [agents, setAgents] = useState([]);
    const [workflows, setWorkflows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);
            
            // Load health data (required)
            const healthData = await api.getHealth();
            setHealth(healthData);
            
            // Load providers data (optional - might not exist)
            let providersData = null;
            try {
                providersData = await api.getProviders();
                setProviders(providersData);
            } catch (providerError) {
                console.log('Providers endpoint not available, skipping...');
                setProviders(null);
            }
            
            // Load other data
            const [memoryData, agentsData, workflowsData] = await Promise.allSettled([
                api.getMemoryStats(),
                api.getAgents(),
                api.getWorkflows()
            ]);

            setMemoryStats(memoryData.status === 'fulfilled' ? memoryData.value : {});
            setAgents(agentsData.status === 'fulfilled' ? agentsData.value : []);
            setWorkflows(workflowsData.status === 'fulfilled' ? workflowsData.value : []);
            
        } catch (err) {
            console.error('Failed to load dashboard data:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return React.createElement(Loading, { message: "Loading dashboard..." });

    if (error) {
        return React.createElement('div', { className: 'card' },
            React.createElement('div', { className: 'card-content' },
                React.createElement('div', {
                    style: { textAlign: 'center', padding: '40px', color: '#ef4444' }
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
                        onClick: loadDashboardData,
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

    const healthyProviders = providers ? 
        Object.values(providers.providers || {}).filter(p => p.is_healthy).length : 0;
    const totalProviders = providers ? 
        Object.keys(providers.providers || {}).length : 0;

    return React.createElement('div', {}, [
        // Stats Grid
        React.createElement('div', { 
            key: 'stats',
            className: 'stats-grid' 
        }, [
            React.createElement('div', { 
                key: 'agents-stat',
                className: 'stat-card' 
            }, [
                React.createElement('div', { 
                    key: 'value',
                    className: 'stat-value' 
                }, agents.length),
                React.createElement('div', { 
                    key: 'label',
                    className: 'stat-label' 
                }, 'Active Agents'),
                React.createElement('div', { 
                    key: 'change',
                    className: 'stat-change positive' 
                }, [
                    React.createElement('i', { 
                        key: 'icon',
                        className: 'fas fa-arrow-up' 
                    }),
                    ' Ready to work'
                ])
            ]),
            
            React.createElement('div', { 
                key: 'workflows-stat',
                className: 'stat-card' 
            }, [
                React.createElement('div', { 
                    key: 'value',
                    className: 'stat-value' 
                }, workflows.length),
                React.createElement('div', { 
                    key: 'label',
                    className: 'stat-label' 
                }, 'Workflows'),
                React.createElement('div', { 
                    key: 'change',
                    className: 'stat-change positive' 
                }, [
                    React.createElement('i', { 
                        key: 'icon',
                        className: 'fas fa-check' 
                    }),
                    ' Available'
                ])
            ]),
            
            React.createElement('div', { 
                key: 'providers-stat',
                className: 'stat-card' 
            }, [
                React.createElement('div', { 
                    key: 'value',
                    className: 'stat-value' 
                }, providers ? `${healthyProviders}/${totalProviders}` : 'N/A'),
                React.createElement('div', { 
                    key: 'label',
                    className: 'stat-label' 
                }, 'Healthy Providers'),
                React.createElement('div', { 
                    key: 'change',
                    className: 'stat-change' 
                }, providers ? (
                    totalProviders > 0 ? 
                        React.createElement('span', { className: 'positive' }, [
                            React.createElement('i', { 
                                key: 'icon',
                                className: 'fas fa-check' 
                            }),
                            ' All online'
                        ]) :
                        React.createElement('span', {}, 'No providers configured')
                ) : React.createElement('span', { 
                    style: { color: '#64748b' } 
                }, 'Providers endpoint not available'))
            ]),
            
            React.createElement('div', { 
                key: 'memory-stat',
                className: 'stat-card' 
            }, [
                React.createElement('div', { 
                    key: 'value',
                    className: 'stat-value' 
                }, memoryStats?.total_memory_entries || 0),
                React.createElement('div', { 
                    key: 'label',
                    className: 'stat-label' 
                }, 'Memory Entries'),
                React.createElement('div', { 
                    key: 'change',
                    className: 'stat-change' 
                }, `${memoryStats?.agents_with_memory || 0} agents with memory`)
            ])
        ]),

        // Content Grid
        React.createElement('div', { 
            key: 'content',
            className: 'grid grid-2' 
        }, [
            // System Health Card
            React.createElement('div', { 
                key: 'health-card',
                className: 'card' 
            }, [
                React.createElement('div', { 
                    key: 'header',
                    className: 'card-header' 
                }, [
                    React.createElement('h3', { 
                        key: 'title',
                        className: 'card-title' 
                    }, 'System Health'),
                    React.createElement('span', {
                        key: 'status',
                        className: `status ${health?.status === 'healthy' ? 'status-online' : 'status-offline'}`
                    }, health?.status || 'Unknown')
                ]),
                React.createElement('div', { 
                    key: 'content',
                    className: 'card-content' 
                }, [
                    // Warmup Stats
                    health?.warmup_stats && React.createElement('div', {
                        key: 'warmup',
                        style: { marginBottom: '16px' }
                    }, [
                        React.createElement('p', { key: 'title' }, React.createElement('strong', {}, 'Model Warmup:')),
                        React.createElement('p', { key: 'models' }, `Active Models: ${health.warmup_stats.active_models}/${health.warmup_stats.total_models}`),
                        React.createElement('p', { key: 'success' }, `Success Rate: ${health.warmup_stats.success_rate}%`)
                    ]),
                    
                    // Providers Info
                    providers && providers.providers ? React.createElement('div', {
                        key: 'providers',
                        style: { marginTop: '16px' }
                    }, [
                        React.createElement('p', { key: 'title' }, React.createElement('strong', {}, 'Providers:')),
                        ...Object.entries(providers.providers).map(([name, provider]) =>
                            React.createElement('div', {
                                key: name,
                                style: {
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    marginTop: '8px'
                                }
                            }, [
                                React.createElement('span', { key: 'name' }, name),
                                React.createElement('span', {
                                    key: 'status',
                                    className: `status ${provider.is_healthy ? 'status-online' : 'status-offline'}`
                                }, provider.is_healthy ? 'Healthy' : 'Offline')
                            ])
                        )
                    ]) : React.createElement('div', {
                        key: 'no-providers',
                        style: { marginTop: '16px', color: '#64748b' }
                    }, React.createElement('p', {}, 'Provider information not available'))
                ])
            ]),

            // Recent Activity Card
            React.createElement('div', { 
                key: 'activity-card',
                className: 'card' 
            }, [
                React.createElement('div', { 
                    key: 'header',
                    className: 'card-header' 
                }, 
                    React.createElement('h3', { 
                        key: 'title',
                        className: 'card-title' 
                    }, 'Recent Activity')
                ),
                React.createElement('div', { 
                    key: 'content',
                    className: 'card-content' 
                }, 
                    React.createElement('div', { 
                        style: { color: '#64748b' } 
                    }, [
                        React.createElement('p', { key: '1' }, '• System initialized successfully'),
                        React.createElement('p', { key: '2' }, `• ${agents.length} agents loaded and ready`),
                        React.createElement('p', { key: '3' }, `• ${workflows.length} workflows available`),
                        React.createElement('p', { key: '4' }, '• All systems operational'),
                        React.createElement('p', { key: '5' }, '• Memory management active')
                    ])
                )
            ])
        ])
    ]);
};

// Make component globally available
window.Dashboard = Dashboard;