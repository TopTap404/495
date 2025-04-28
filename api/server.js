// server.js ของมึงที่แท้ทรู (เชื่อม MySQL + API Login/Register)
const express = require('express');
const bodyParser = require('body-parser');
const mysql = require('mysql2');
const cors = require('cors');
const app = express();
const port = 3000;

app.use(bodyParser.json());
app.use(cors());

// เชื่อมต่อ MySQL ด้วย SSL ใช้ CA certificate จาก DigiCert
const db = mysql.createConnection({
    host: 'cpe495.mysql.database.azure.com',
    user: 'cpe495',
    password: 'Padungkiat1598',
    database: 'room_behavior',
});

db.connect((err) => {
    if (err) {
        console.error('❌ ไม่สามารถเชื่อมต่อกับฐานข้อมูล:', err);
    } else {
        console.log('✅ เชื่อมต่อฐานข้อมูลสำเร็จ');
    }
});

// POST ข้อมูลห้องเรียนจาก YOLO
app.post('/postroomdata', (req, res) => {
    const { room_id, total_people, behavior_level, timestamp } = req.body;

    if (!room_id || total_people == null || behavior_level == null || !timestamp) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    const sql = `INSERT INTO room_behavior (room_id, total_people, behavior_level, timestamp)
                 VALUES (?, ?, ?, ?)`;

    db.query(sql, [room_id, total_people, behavior_level, timestamp], (err, result) => {
        if (err) {
            console.error('❌ เกิดข้อผิดพลาดขณะบันทึก:', err);
            return res.status(500).json({ error: 'Database error' });
        }

        console.log("📥 บันทึกลงฐานข้อมูลแล้ว:", {
            room_id,
            total_people,
            behavior_level,
            timestamp
        });

        res.status(200).json({ message: 'Data stored successfully' });
    });
});

// GET ข้อมูลสรุปสำหรับ dashboard
app.get('/getroomdata', (req, res) => {
    const { start, end } = req.query;

    let sql = 'SELECT * FROM room_behavior';
    let params = [];

    if (start && end) {
        sql += ' WHERE timestamp BETWEEN ? AND ?';
        params.push(`${start} 00:00:00`, `${end} 23:59:59`);
    }

    sql += ' ORDER BY timestamp DESC';

    db.query(sql, params, (err, results) => {
        if (err) {
            console.error('❌ เกิดข้อผิดพลาดขณะดึงข้อมูล:', err);
            return res.status(500).json({ error: 'Database error' });
        }

        let totalStudents = 0;
        let behaviorSum = 0;
        let behaviorCount = 0;
        const behaviorPercent = [0, 0, 0, 0, 0];
        const peoplePerHour = Array(8).fill(0); // 9AM–4PM
        const peoplePerDay = Array(7).fill(0);  // Sun–Sat

        results.forEach(row => {
            const ts = new Date(row.timestamp);
            const hour = ts.getHours();
            const dow = ts.getDay(); // 0 = Sunday
            const lvl = parseInt(row.behavior_level);

            if (hour >= 9 && hour <= 16) {
                peoplePerHour[hour - 9] += row.total_people;
            }
            peoplePerDay[dow] += row.total_people;

            totalStudents += row.total_people;
            behaviorSum += lvl;
            behaviorCount++;

            if (lvl >= 1 && lvl <= 5) behaviorPercent[lvl - 1]++;
        });

        const behaviorAvg = behaviorCount > 0 ? (behaviorSum / behaviorCount).toFixed(2) : 0;

        res.status(200).json({
            totalStudents,
            behaviorAvg,
            peoplePerHour,
            peoplePerDay,
            behaviorPercent
        });
    });
});

// POST สมัครสมาชิก
app.post('/register', (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) {
        return res.status(400).json({ error: 'Missing email or password' });
    }

    const sql = 'INSERT INTO users (email, password) VALUES (?, ?)';
    db.query(sql, [email, password], (err, result) => {
        if (err) {
            console.error('❌ เกิดข้อผิดพลาดตอนสมัคร:', err);
            return res.status(500).json({ error: 'Database error' });
        }
        res.status(200).json({ message: '✅ สมัครเรียบร้อยแล้ว' });
    });
});

// POST เข้าสู่ระบบ
app.post('/login', (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) {
        return res.status(400).json({ error: 'Missing email or password' });
    }

    const sql = 'SELECT * FROM users WHERE email = ? AND password = ?';
    db.query(sql, [email, password], (err, results) => {
        if (err) {
            console.error('❌ เกิดข้อผิดพลาดตอนล็อกอิน:', err);
            return res.status(500).json({ error: 'Database error' });
        }

        if (results.length > 0) {
            res.status(200).json({ message: '✅ เข้าสู่ระบบสำเร็จ', user: results[0] });
        } else {
            res.status(401).json({ error: 'อีเมลหรือรหัสผ่านไม่ถูกต้อง' });
        }
    });
});

app.listen(port, () => {
    console.log(`🚀 Server is running on http://localhost:${port}`);
});
