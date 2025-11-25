// Global chart instances
let donutChart = null;
let densityChart = null;
let sunburstChartInstance = null;
let radarChartInstance = null;

async function loadVisualizations(sessionId, skillSystem = 'CUSTOM') {
    console.log("Loading visualizations for session:", sessionId, "skill system:", skillSystem);
    
    // Check if global api object is available
    if (typeof api === 'undefined') {
        console.error("API client not initialized. Make sure api.js is loaded.");
        return;
    }

    try {
        if (skillSystem === 'CUSTOM') {
            // Fetch Custom Data only
            try {
                const customData = await api.request(`/api/visualizations/session/${sessionId}/custom`);
                renderCustomCharts(customData);
                // Clear ESCO charts
                clearEscoCharts();
            } catch (e) {
                console.warn("Failed to load custom viz data:", e);
                clearCustomCharts();
            }
        } else if (skillSystem === 'ESCO') {
            // Fetch ESCO Data only
            try {
                const escoData = await api.request(`/api/visualizations/session/${sessionId}/esco`);
                renderEscoCharts(escoData);
                // Clear Custom charts
                clearCustomCharts();
            } catch (e) {
                console.warn("Failed to load ESCO viz data:", e);
                clearEscoCharts();
            }
        }

    } catch (error) {
        console.error("Error loading visualizations:", error);
    }
}

function clearCustomCharts() {
    // Clear Donut Chart
    const donutCanvas = document.getElementById('donutChart');
    if (donutChart) {
        donutChart.destroy();
        donutChart = null;
        if (donutCanvas) {
            const ctx = donutCanvas.getContext('2d');
            ctx.clearRect(0, 0, donutCanvas.width, donutCanvas.height);
        }
    }
    
    // Clear Density Chart
    const densityCanvas = document.getElementById('densityChart');
    if (densityChart) {
        densityChart.destroy();
        densityChart = null;
        if (densityCanvas) {
            const ctx = densityCanvas.getContext('2d');
            ctx.clearRect(0, 0, densityCanvas.width, densityCanvas.height);
        }
    }
}

function clearEscoCharts() {
    // Clear Sunburst Chart
    const sunburstCanvas = document.getElementById('sunburstChart');
    if (sunburstChartInstance) {
        sunburstChartInstance.destroy();
        sunburstChartInstance = null;
        if (sunburstCanvas) {
            const ctx = sunburstCanvas.getContext('2d');
            ctx.clearRect(0, 0, sunburstCanvas.width, sunburstCanvas.height);
        }
    }
    
    // Clear Radar Chart
    const radarCanvas = document.getElementById('radarChart');
    if (radarChartInstance) {
        radarChartInstance.destroy();
        radarChartInstance = null;
        if (radarCanvas) {
            const ctx = radarCanvas.getContext('2d');
            ctx.clearRect(0, 0, radarCanvas.width, radarCanvas.height);
        }
    }
    
    // Clear Occupation List
    const occupationList = document.getElementById('occupationList');
    if (occupationList) {
        occupationList.innerHTML = '';
    }
}

function renderCustomCharts(data) {
    if (!data) return;

    // Show Custom chart containers, hide ESCO ones
    const donutContainer = document.getElementById('donutChart')?.parentElement;
    const densityContainer = document.getElementById('densityChart')?.parentElement;
    const sunburstContainer = document.getElementById('sunburstChart')?.parentElement;
    const radarContainer = document.getElementById('radarChart')?.parentElement;
    const occupationContainer = document.getElementById('occupationList')?.parentElement;
    
    if (donutContainer) donutContainer.style.display = 'block';
    if (densityContainer) densityContainer.style.display = 'block';
    if (sunburstContainer) sunburstContainer.style.display = 'none';
    if (radarContainer) radarContainer.style.display = 'none';
    if (occupationContainer) occupationContainer.style.display = 'none';

    // Donut Chart (Type Distribution)
    const donutCanvas = document.getElementById('donutChart');
    if (donutCanvas && data.donut) {
        const donutCtx = donutCanvas.getContext('2d');
        if (donutChart) donutChart.destroy();
        
        donutChart = new Chart(donutCtx, {
            type: 'doughnut',
            data: data.donut,
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right' },
                    title: { display: true, text: 'Skill Types' }
                }
            }
        });
    }

    // Density/Histogram Chart (Confidence) - Visualized as Area Chart
    const densityCanvas = document.getElementById('densityChart');
    if (densityCanvas && data.density) {
        const densityCtx = densityCanvas.getContext('2d');
        if (densityChart) densityChart.destroy();

        densityChart = new Chart(densityCtx, {
            type: 'line', 
            data: data.density,
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Count' } },
                    x: { title: { display: true, text: 'Confidence Level' } }
                },
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Confidence Distribution' }
                },
                elements: {
                    line: {
                        tension: 0.4, // Smooth curves
                        fill: true
                    }
                }
            }
        });
    }
}

function renderEscoCharts(data) {
    if (!data) return;

    // Show ESCO chart containers, hide Custom ones
    const donutContainer = document.getElementById('donutChart')?.parentElement;
    const densityContainer = document.getElementById('densityChart')?.parentElement;
    const sunburstContainer = document.getElementById('sunburstChart')?.parentElement;
    const radarContainer = document.getElementById('radarChart')?.parentElement;
    const occupationContainer = document.getElementById('occupationList')?.parentElement;
    
    if (donutContainer) donutContainer.style.display = 'none';
    if (densityContainer) densityContainer.style.display = 'none';
    if (sunburstContainer) sunburstContainer.style.display = 'block';
    if (radarContainer) radarContainer.style.display = 'block';
    if (occupationContainer) occupationContainer.style.display = 'block';

    // Sunburst Proxy (Doughnut of Top Level Categories)
    const hierarchyData = {
        labels: [],
        datasets: [{
            data: [],
            backgroundColor: []
        }]
    };
    
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40',
        '#C9CBCF', '#FF9F40', '#4BC0C0', '#FF6384', '#36A2EB'
    ];

    if (data.sunburst && data.sunburst.children) {
        data.sunburst.children.forEach((child, index) => {
            hierarchyData.labels.push(child.name);
            // Aggregate count of children
            const count = child.children ? child.children.length : 0;
            hierarchyData.datasets[0].data.push(count);
            hierarchyData.datasets[0].backgroundColor.push(colors[index % colors.length]);
        });
    }

    // Render Hierarchy Chart
    const sunburstCanvas = document.getElementById('sunburstChart');
    if (sunburstCanvas) {
        const sunburstCtx = sunburstCanvas.getContext('2d');
        if (sunburstChartInstance) sunburstChartInstance.destroy();
        
        sunburstChartInstance = new Chart(sunburstCtx, {
            type: 'doughnut',
            data: hierarchyData,
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right' },
                    title: { display: true, text: 'Skill Hierarchy (Top Level)' }
                }
            }
        });
    }

    // Radar Chart (Pillars)
    const radarCanvas = document.getElementById('radarChart');
    if (radarCanvas && data.radar) {
        const radarCtx = radarCanvas.getContext('2d');
        if (radarChartInstance) radarChartInstance.destroy();
        
        radarChartInstance = new Chart(radarCtx, {
            type: 'radar',
            data: data.radar,
            options: {
                responsive: true,
                scales: {
                    r: {
                        angleLines: { display: false },
                        suggestedMin: 0
                    }
                },
                plugins: {
                    title: { display: true, text: 'Skill Pillars' }
                }
            }
        });
    }

    // Occupation List
    const occupationList = document.getElementById('occupationList');
    if (occupationList) {
        occupationList.innerHTML = '';
        if (data.occupations && data.occupations.length > 0) {
            const ul = document.createElement('ul');
            ul.className = 'list-group'; // Bootstrap class style
            ul.style.listStyle = 'none';
            ul.style.padding = '0';
            
            data.occupations.forEach(occ => {
                const li = document.createElement('li');
                li.style.padding = '10px';
                li.style.borderBottom = '1px solid #eee';
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.style.alignItems = 'center';
                
                li.innerHTML = `
                    <span style="font-weight: 500;">${occ.title}</span>
                    <span style="background: #3498db; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">${occ.count} matches</span>
                `;
                ul.appendChild(li);
            });
            occupationList.appendChild(ul);
        } else {
            occupationList.innerHTML = '<p style="color: #95a5a6; font-style: italic;">No matching occupations found based on current skills.</p>';
        }
    }
}

window.loadVisualizations = loadVisualizations;
