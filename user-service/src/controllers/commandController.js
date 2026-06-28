const updateProfileHandler = require('../commands/updateProfileHandler');

const updateMyProfile = async (req, res) => {
    try {
        const profile = await updateProfileHandler(req.user.id, req.body);
        res.json(profile);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const updateProfileByAuthId = async (req, res) => {
    try {
        const profile = await updateProfileHandler(req.params.authId, req.body);
        res.json(profile);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { updateMyProfile, updateProfileByAuthId };