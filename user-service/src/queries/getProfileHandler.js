const UserProfile = require('../models/UserProfile');

const getProfileHandler = async (authId) => {
    const profile = await UserProfile.findOne({ where: { authId } });
    return profile;
};

module.exports = getProfileHandler;