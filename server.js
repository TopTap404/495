const express = require('express');
const bodyParser = require('body-parser');
const mysql = require('mysql2');

const app = express();
const port = 3000;

app.use(bodyParser.json());

// เชื่อมต่อ MySQL
const db = mysql.createConnection({
    host: 'cpe495.mysql.database.azure.com',
    user: 'cpe495',
    password: 'Padungkiat1598',  // แก้ให้ตรงกับของคุณ
    database: 'room_behavior'    // แก้ให้ตรงกับของคุณ
});

// ตรวจสอบการเชื่อมต่อ
db.connect((err) => {
    if (err) {
        console.error('❌ ไม่สามารถเชื่อมต่อกับฐานข้อมูล:', err);
    } else {
        console.log('✅ เชื่อมต่อฐานข้อมูลสำเร็จ');
    }
});

app.post('/postroomdata', (req, res) => {
    const { room_id, total_people, behavior_level, timestamp } = req.body;

    if (!room_id || total_people == null || behavior_level == null || !timestamp) {
        return res.status(400).json({ error: 'Missing required fields' });
    }

    // SQL สำหรับบันทึกข้อมูล
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

app.get('/getroomdata', (req, res) => {
    const sql = 'SELECT * FROM room_behavior ORDER BY timestamp DESC';

    db.query(sql, (err, results) => {
        if (err) {
            console.error('❌ เกิดข้อผิดพลาดขณะดึงข้อมูล:', err);
            return res.status(500).json({ error: 'Database error' });
        }

        res.status(200).json(results);
    });
});

app.listen(port, () => {
    console.log(`🚀 Server is running on http://localhost:${port}`);
});
