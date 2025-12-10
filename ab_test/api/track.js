/**
 * Vercel Serverless Function - Vote Tracking API
 * 
 * Endpoint: POST /api/track
 * Stores A/B test votes in Vercel KV (Redis)
 * 
 * Required env vars:
 * - KV_REST_API_URL
 * - KV_REST_API_TOKEN
 */

// Vercel KV client (Edge-compatible)
const KV_URL = process.env.KV_REST_API_URL;
const KV_TOKEN = process.env.KV_REST_API_TOKEN;

async function kvSet(key, value) {
    const response = await fetch(`${KV_URL}/set/${key}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${KV_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(value)
    });
    return response.ok;
}

async function kvGet(key) {
    const response = await fetch(`${KV_URL}/get/${key}`, {
        headers: {
            'Authorization': `Bearer ${KV_TOKEN}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data.result;
    }
    return null;
}

async function kvLpush(key, value) {
    const response = await fetch(`${KV_URL}/lpush/${key}`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${KV_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(value)
    });
    return response.ok;
}

async function kvLrange(key, start, end) {
    const response = await fetch(`${KV_URL}/lrange/${key}/${start}/${end}`, {
        headers: {
            'Authorization': `Bearer ${KV_TOKEN}`
        }
    });
    if (response.ok) {
        const data = await response.json();
        return data.result || [];
    }
    return [];
}

// Main handler
export default async function handler(req, res) {
    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    // POST - Save a vote
    if (req.method === 'POST') {
        try {
            const vote = req.body;

            if (!vote || !vote.testId) {
                return res.status(400).json({ error: 'Invalid vote data' });
            }

            // Check if KV is configured
            if (!KV_URL || !KV_TOKEN) {
                console.warn('Vercel KV not configured. Vote not persisted.');
                return res.status(200).json({
                    success: true,
                    warning: 'KV not configured, vote not persisted',
                    vote: vote
                });
            }

            // Save vote to list
            const saved = await kvLpush('vibereco:votes', JSON.stringify(vote));

            if (saved) {
                // Update stats
                await updateStats(vote);

                return res.status(200).json({ success: true, testId: vote.testId });
            } else {
                return res.status(500).json({ error: 'Failed to save vote' });
            }

        } catch (error) {
            console.error('Error saving vote:', error);
            return res.status(500).json({ error: error.message });
        }
    }

    // GET - Get stats
    if (req.method === 'GET') {
        try {
            if (!KV_URL || !KV_TOKEN) {
                return res.status(200).json({
                    total_votes: 0,
                    vibe_wins: 0,
                    youtube_wins: 0,
                    vibe_win_rate: 0,
                    message: 'KV not configured'
                });
            }

            const stats = await kvGet('vibereco:stats');

            if (stats) {
                return res.status(200).json(JSON.parse(stats));
            } else {
                return res.status(200).json({
                    total_votes: 0,
                    vibe_wins: 0,
                    youtube_wins: 0,
                    vibe_win_rate: 0
                });
            }

        } catch (error) {
            console.error('Error getting stats:', error);
            return res.status(500).json({ error: error.message });
        }
    }

    return res.status(405).json({ error: 'Method not allowed' });
}

async function updateStats(vote) {
    try {
        // Get current stats
        let stats = await kvGet('vibereco:stats');
        stats = stats ? JSON.parse(stats) : {
            total_votes: 0,
            vibe_wins: 0,
            youtube_wins: 0,
            vibe_win_rate: 0,
            by_seed: {}
        };

        // Update counts
        stats.total_votes++;

        if (vote.winnerSource === 'vibe') {
            stats.vibe_wins++;
        } else {
            stats.youtube_wins++;
        }

        // Calculate win rate
        stats.vibe_win_rate = stats.total_votes > 0
            ? (stats.vibe_wins / stats.total_votes) * 100
            : 0;

        // Track by seed
        const seedKey = String(vote.seedId);
        if (!stats.by_seed[seedKey]) {
            stats.by_seed[seedKey] = { vibe: 0, youtube: 0 };
        }
        stats.by_seed[seedKey][vote.winnerSource]++;

        // Save updated stats
        await kvSet('vibereco:stats', JSON.stringify(stats));

    } catch (error) {
        console.error('Error updating stats:', error);
    }
}
