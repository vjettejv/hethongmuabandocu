const UserProfile = require('../models/UserProfile');

const updateProfileHandler = async (authId, { fullName, phone, address, avatar }) => {
    const [profile, created] = await UserProfile.findOrCreate({
        where: { authId },
        defaults: { fullName, phone, address, avatar }
    });
    return profile;
};

module.exports = updateProfileHandler;