// js/components/Loading.js - Loading component

const Loading = ({ message = "Loading..." }) => {
    return React.createElement('div', { className: 'loading' }, [
        React.createElement('div', { 
            key: 'spinner',
            className: 'spinner' 
        }),
        React.createElement('span', { 
            key: 'message' 
        }, message)
    ]);
};

// Make component globally available
window.Loading = Loading;