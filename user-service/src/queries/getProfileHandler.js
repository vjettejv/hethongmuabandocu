const UserProfile = require('../models/UserProfile');

const getProfileHandler = async (authId) => {
    const profile = await UserProfile.findOne({ where: { authId } });
    if (!profile) throw new Error('Profile not found');
    return profile;
};

module.exports = getProfileHandler;