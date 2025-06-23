// Dashboard JavaScript
let chart = null;

// Initialize dashboard when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    const dashboardData = getDashboardData();
    initProgressBars();
    initUsageChart(dashboardData);
    checkBudgetWarning(dashboardData.budgetPercentage);
    initServiceStatus();
});

// Get dashboard data from HTML element
function getDashboardData() {
    const dataElement = document.getElementById('dashboard-data');
    if (!dataElement) return { dailyUsage: {}, budgetPercentage: 0 };
    
    try {
        return {
            dailyUsage: JSON.parse(dataElement.dataset.dailyUsage || '{}'),
            budgetPercentage: parseFloat(dataElement.dataset.budgetPercentage || '0')
        };
    } catch (e) {
        console.warn('Error parsing dashboard data:', e);
        return { dailyUsage: {}, budgetPercentage: 0 };
    }
}

// Initialize progress bars
function initProgressBars() {
    const progressFills = document.querySelectorAll('.progress-fill[data-width]');
    progressFills.forEach(fill => {
        const width = fill.dataset.width;
        if (width) {
            fill.style.width = width + '%';
        }
    });
}

// Initialize usage chart
function initUsageChart(dashboardData) {
    const ctx = document.getElementById('usageChart');
    if (!ctx) return;
    
    const dailyUsage = dashboardData.dailyUsage || {};
    const labels = Object.keys(dailyUsage).sort();
    const costData = labels.map(date => dailyUsage[date] ? dailyUsage[date].cost : 0);
    const requestData = labels.map(date => dailyUsage[date] ? dailyUsage[date].requests : 0);

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Custo Diário ($)',
                data: costData,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1,
                yAxisID: 'y'
            }, {
                label: 'Requisições Diárias',
                data: requestData,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.1,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Data'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Custo ($)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Requisições'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

// Check budget warning
function checkBudgetWarning(budgetPercentage) {
    if (budgetPercentage > 80) {
        showBudgetWarning(budgetPercentage);
    }
}

// Show budget warning
function showBudgetWarning(percentage) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'budget-alert';
    alertDiv.innerHTML = `
        <div class="alert alert-warning">
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Aviso de Orçamento:</strong> Você usou ${percentage.toFixed(1)}% do seu orçamento mensal.
            <button onclick="this.parentElement.parentElement.remove()" class="close-btn">×</button>
        </div>
    `;
    
    const container = document.querySelector('.dashboard-container');
    if (container) {
        container.insertAdjacentElement('afterbegin', alertDiv);
    }
}

// Initialize service status checking
function initServiceStatus() {
    checkAllServicesStatus();
    // Check every 30 seconds
    setInterval(checkAllServicesStatus, 30000);
}

// Check all services status
async function checkAllServicesStatus() {
    try {
        const response = await fetch('/api/services/status');
        const data = await response.json();
        updateServicesStatus(data.services);
    } catch (error) {
        console.error('Error checking services:', error);
    }
}

// Update services status display
function updateServicesStatus(services) {
    Object.keys(services).forEach(service => {
        const statusDot = document.getElementById('status-' + service);
        const statusElement = document.getElementById(service + '-status');
        
        if (statusDot && statusElement) {
            const statusText = statusElement.querySelector('.status-text');
            
            if (services[service]) {
                statusDot.classList.add('online');
                statusText.textContent = 'Online';
            } else {
                statusDot.classList.remove('online');
                statusText.textContent = 'Offline';
            }
        }
    });
}

// Test Whisper API
async function testWhisperAPI() {
    try {
        const response = await fetch('/api/audio/transcribe', {
            method: 'POST',
            body: new FormData() // Empty form for test
        });
        
        if (response.status === 400) {
            alert('✅ Whisper API está funcionando!\n(Erro esperado - teste sem arquivo de áudio)');
        } else {
            alert('Whisper API respondeu com status: ' + response.status);
        }
    } catch (error) {
        alert('❌ Erro ao testar Whisper API: ' + error.message);
    }
}

// Check Ollama models
async function checkOllamaModels() {
    try {
        const response = await fetch('http://localhost:11434/api/tags');
        const data = await response.json();
        
        if (data.models && data.models.length > 0) {
            const modelNames = data.models.map(m => m.name).join('\n• ');
            alert('📋 Modelos Ollama disponíveis:\n\n• ' + modelNames);
        } else {
            alert('⚠️ Nenhum modelo Ollama encontrado.');
        }
    } catch (error) {
        alert('❌ Erro ao verificar modelos Ollama: ' + error.message);
    }
} 