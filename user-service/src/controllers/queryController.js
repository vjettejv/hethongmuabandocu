const getProfileHandler = require('../queries/getProfileHandler');

const getMyProfile = async (req, res) => {
    try {
        const profile = await getProfileHandler(req.user.id);
        res.json(profile);
    } catch (error) {
        res.json({}); // Original code returns {} if not found
    }
};

const getProfileByAuthId = async (req, res) => {
    try {
        const profile = await getProfileHandler(req.params.authId);
        res.json(profile);
    } catch (error) {
        res.status(404).json({ error: error.message });
    }
};

module.exports = { getMyProfile, getProfileByAuthId };