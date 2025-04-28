const API_URL = "http://localhost:3000/getRoomData";

let peoplePerHourChart;
let peoplePerDayChart;
let behaviorPercentChart;

async function loadWithDateRange() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    let url = API_URL;
    if (startDate && endDate) {
        url += `?start=${startDate}&end=${endDate}`;
    }

    const totalStudentsElement = document.getElementById('totalStudents');
    const behaviorAvgElement = document.getElementById('behaviorAvg');

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Received data (date range):", data);

        // รีเซ็ตค่า
        totalStudentsElement.textContent = data.totalStudents ?? "--";
        behaviorAvgElement.textContent = data.behaviorAvg ?? "--";

        // อัปเดตกราฟ
        updateCharts(data);
    } catch (error) {
        console.error('Error fetching room data:', error);
        totalStudentsElement.textContent = "--";
        behaviorAvgElement.textContent = "--";
    }
}

async function fetchRoomData() {
    const totalStudentsElement = document.getElementById('totalStudents');
    const behaviorAvgElement = document.getElementById('behaviorAvg');

    try {
        const response = await fetch(API_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Received data:", data);

        // อัปเดตจำนวนคนในห้องและค่าเฉลี่ยพฤติกรรม
        totalStudentsElement.textContent = data.totalStudents ?? "--";
        behaviorAvgElement.textContent = data.behaviorAvg ?? "--";

        // อัปเดตกราฟ
        updateCharts(data);
    } catch (error) {
        console.error('Error fetching room data:', error);
        totalStudentsElement.textContent = "--";
        behaviorAvgElement.textContent = "--";
    }
}

// ฟังก์ชันอัปเดตกราฟ
function updateCharts(data) {
    if (peoplePerHourChart) {
        peoplePerHourChart.data.datasets[0].data = data.peoplePerHour ?? [];
        peoplePerHourChart.update();
    }

    if (peoplePerDayChart) {
        peoplePerDayChart.data.datasets[0].data = data.peoplePerDay ?? [];
        peoplePerDayChart.update();
    }

    if (behaviorPercentChart) {
        behaviorPercentChart.data.datasets[0].data = data.behaviorPercent ?? [];
        behaviorPercentChart.update();
    }
}

// ฟังก์ชันสร้างกราฟ
function createCharts() {
    const ctx1 = document.getElementById('peoplePerHour').getContext('2d');
    peoplePerHourChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: ['9 AM', '10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM', '4 PM'],
            datasets: [{
                label: 'Number of people',
                data: [], // ค่าเริ่มต้น ว่างไว้แล้วค่อยอัปเดต
                borderColor: '#6ca6fd',
                fill: false
            }]
        }
    });

    const ctx2 = document.getElementById('peoplePerDay').getContext('2d');
    peoplePerDayChart = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Number of people',
                data: [],
                backgroundColor: ['#4a90e2', '#6ca6fd', '#add8e6', '#4a90e2', '#6ca6fd', '#add8e6', '#4a90e2']
            }]
        }
    });

    const ctx3 = document.getElementById('behaviorPercent').getContext('2d');
    behaviorPercentChart = new Chart(ctx3, {
        type: 'pie',
        data: {
            labels: ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
            datasets: [{
                data: [],
                backgroundColor: ['#6ca6fd', '#68d391', '#f6e05e', '#fc8181', '#e53e3e']
            }]
        }
    });
}

// โหลดค่าครั้งแรก
document.addEventListener("DOMContentLoaded", () => {
    createCharts();
    fetchRoomData();
});

// อัปเดตข้อมูลทุก 5 วินาที
setInterval(fetchRoomData, 5000);
