
document.addEventListener("DOMContentLoaded", function () {

    // GRAFIK PRODUKSI DASHBOARD
    const productionCanvas = document.getElementById("productionChart");

    if (productionCanvas && window.productionChartData) {
        new Chart(productionCanvas, {
            type: "bar",
            data: {
                labels: window.productionChartData.labels,
                datasets: [{
                    label: "Hasil Produksi",
                    data: window.productionChartData.values,
                    backgroundColor: "#2563eb",
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    // GRAFIK OEE
    const oeeCanvas = document.getElementById("oeeChart");

    if (oeeCanvas && window.oeeChartData) {
        new Chart(oeeCanvas, {
            type: "bar",
            data: {
                labels: window.oeeChartData.labels,
                datasets: [{
                    label: "Persentase (%)",
                    data: window.oeeChartData.values,
                    backgroundColor: ["#2563eb", "#0d9488", "#f59e0b"],
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    // GRAFIK FORECASTING
    const forecastCanvas = document.getElementById("forecastChart");

    if (forecastCanvas && window.forecastChartData) {
        new Chart(forecastCanvas, {
            type: "line",
            data: {
                labels: window.forecastChartData.labels,
                datasets: [
                    {
                        label: "Permintaan Aktual",
                        data: window.forecastChartData.actual,
                        borderColor: "#2563eb",
                        backgroundColor: "#2563eb",
                        tension: 0.3
                    },
                    {
                        label: "Hasil Forecasting",
                        data: window.forecastChartData.forecast,
                        borderColor: "#f59e0b",
                        backgroundColor: "#f59e0b",
                        borderDash: [6, 5],
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

});
