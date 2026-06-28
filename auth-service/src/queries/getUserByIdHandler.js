const AuthUser = require('../models/AuthUser');

const getUserByIdHandler = async (id) => {
    const user = await AuthUser.findByPk(id);
    if (!user) throw new Error('User not found');
    return { id: user.id, username: user.username, email: user.email, roleId: user.roleId };
};

module.exports = getUserByIdHandler;
