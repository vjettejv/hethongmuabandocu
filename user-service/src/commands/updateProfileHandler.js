const UserProfile = require('../models/UserProfile');

const updateProfileHandler = async (authId, { fullName, phone, address, avatar }) => {
    const profile = await UserProfile.create({ authId, fullName, phone, address, avatar });
    return profile;
};

module.exports = updateProfileHandler;