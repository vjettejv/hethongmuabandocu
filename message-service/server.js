const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
require('dotenv').config();

const sequelize = require('./src/config/db');
const routes = require('./src/routes');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*', methods: ["GET", "POST"] } });

app.set('io', io); // make io accessible to controllers
app.use(express.json());
app.use(cors());

sequelize.sync().then(() => console.log('Message DB synced'));

app.use('/', routes);

io.on('connection', (socket) => {
    socket.on('join_user_room', (userId) => {
        socket.join(`user_${userId}`);
    });
    socket.on('disconnect', () => {});
});

const PORT = process.env.PORT || 3005;
server.listen(PORT, () => console.log(`Message Service running on port ${PORT}`));