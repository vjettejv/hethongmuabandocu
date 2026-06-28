const bcrypt = require('bcryptjs');
const { Sequelize } = require('sequelize');
const AuthUser = require('../models/AuthUser');

const registerHandler = async ({ username, email, password }) => {
    if (!username || !email || !password) {
        throw new Error('Vui lòng điền đầy đủ thông tin');
    }

    const existingUser = await AuthUser.findOne({ 
        where: {
            [Sequelize.Op.or]: [{ email }, { username }]
        }
    });

    let userToUse = null;

    if (existingUser) {
        if (existingUser.isVerified) {
            if (existingUser.email === email) {
                throw new Error('Email đã được sử dụng');
            } else {
                throw new Error('Tên đăng nhập đã tồn tại');
            }
        } else {
            userToUse = existingUser;
        }
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    const generatedOtp = Math.floor(100000 + Math.random() * 900000).toString();

    if (userToUse) {
        userToUse.username = username;
        userToUse.email = email;
        userToUse.password = hashedPassword;
        userToUse.otp = generatedOtp;
        await userToUse.save();
    } else {
        userToUse = await AuthUser.create({
            username, email, password: hashedPassword, otp: generatedOtp
        });
    }

    // Call notification-service for welcome email
    try {
        console.log(`Sending OTP email to ${email} via notification-service...`);
        const notifRes = await fetch((process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:3006') + '/email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to: email,
                subject: 'Mã xác thực OTP - Đồ Cũ Marketplace',
                text: `Xin chào ${username},\n\nMã xác thực OTP của bạn là: ${generatedOtp}\n\nVui lòng nhập mã này trên trang web để kích hoạt tài khoản.\n\nTrân trọng,\nĐội ngũ Đồ Cũ Marketplace`,
                html: `<h3>Xin chào ${username},</h3><p>Mã xác thực OTP của bạn là: <strong style="font-size:24px;color:blue;">${generatedOtp}</strong></p><p>Vui lòng nhập mã này trên trang web để kích hoạt tài khoản.</p><p>Trân trọng,<br>Đội ngũ Đồ Cũ Marketplace</p>`
            })
        });
        const notifData = await notifRes.json();
        console.log('Notification service response:', notifData);
    } catch (e) {
        console.error('Failed to call notification service:', e.message);
    }

    return { message: 'User created successfully', userId: userToUse.id };
};

module.exports = registerHandler;
