// js/main.js - Application Entry Point

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Agentic AI Framework UI starting...');
    
    // Check if React is loaded
    if (typeof React === 'undefined') {
        console.error('React is not loaded!');
        document.getElementById('root').innerHTML = `
            <div style="padding: 40px; text-align: center; color: #ef4444;">
                <h2>Error: React not loaded</h2>
                <p>Please ensure React is properly loaded before the application scripts.</p>
            </div>
        `;
        return;
    }

    // Check if ReactDOM is loaded
    if (typeof ReactDOM === 'undefined') {
        console.error('ReactDOM is not loaded!');
        document.getElementById('root').innerHTML = `
            <div style="padding: 40px; text-align: center; color: #ef4444;">
                <h2>Error: ReactDOM not loaded</h2>
                <p>Please ensure ReactDOM is properly loaded before the application scripts.</p>
            </div>
        `;
        return;
    }

    // Check if required components are loaded
    const requiredComponents = ['App', 'Dashboard', 'AgentManagement', 'AgentModal', 'Loading'];
    const missingComponents = requiredComponents.filter(comp => typeof window[comp] === 'undefined');
    
    if (missingComponents.length > 0) {
        console.error('Missing components:', missingComponents);
        document.getElementById('root').innerHTML = `
            <div style="padding: 40px; text-align: center; color: #ef4444;">
                <h2>Error: Missing Components</h2>
                <p>The following components failed to load: ${missingComponents.join(', ')}</p>
                <p>Please check the console for more details.</p>
            </div>
        `;
        return;
    }

    // Check if API client is loaded
    if (typeof window.api === 'undefined') {
        console.error('API client not loaded!');
        document.getElementById('root').innerHTML = `
            <div style="padding: 40px; text-align: center; color: #ef4444;">
                <h2>Error: API Client not loaded</h2>
                <p>Please ensure the API client is properly loaded.</p>
            </div>
        `;
        return;
    }

    try {
        // Test API connection
        console.log('Testing API connection...');
        window.api.getHealth()
            .then(() => {
                console.log('API connection successful');
            })
            .catch((error) => {
                console.warn('API connection failed:', error.message);
                // Don't block the UI, just warn
            });

        // Render the main App component
        console.log('Rendering App component...');
        ReactDOM.render(
            React.createElement(App),
            document.getElementById('root')
        );
        
        console.log('Agentic AI Framework UI loaded successfully!');
        
    } catch (error) {
        console.error('Failed to render application:', error);
        document.getElementById('root').innerHTML = `
            <div style="padding: 40px; text-align: center; color: #ef4444;">
                <h2>Application Error</h2>
                <p>Failed to start the application: ${error.message}</p>
                <p>Please check the console for more details.</p>
                <button onclick="location.reload()" style="margin-top: 16px; padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Reload Page
                </button>
            </div>
        `;
    }
});

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});