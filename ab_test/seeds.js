/**
 * Official benchmark seedset for VibeReco A/B Testing
 * 
 * These 15 songs were selected from Top 50 France and Top 50 Monde
 * to represent diverse vibes: amour, rupture, ego, fête, nostalgie, introspection, etc.
 */

const SEED_SONGS = [
    {
        id: 1,
        title: "Melodrama",
        artist: "Disiz, Theodora",
        vibe: "introspection",
        vibeEmoji: "🌙",
        spotifyId: null, // To be filled with actual Spotify IDs
        artwork: null
    },
    {
        id: 2,
        title: "DIPLOMATICO",
        artist: "ELGRANDETOTO",
        vibe: "ego",
        vibeEmoji: "💎",
        spotifyId: null,
        artwork: null
    },
    {
        id: 3,
        title: "LOVE YOU",
        artist: "Nono La Grinta",
        vibe: "amour",
        vibeEmoji: "❤️",
        spotifyId: null,
        artwork: null
    },
    {
        id: 4,
        title: "Génération Impolie",
        artist: "Franglish, KeBlack",
        vibe: "fête",
        vibeEmoji: "🎉",
        spotifyId: null,
        artwork: null
    },
    {
        id: 5,
        title: "PARISIENNE",
        artist: "GIMS, La Mano 1.9",
        vibe: "night_drive",
        vibeEmoji: "🌃",
        spotifyId: null,
        artwork: null
    },
    {
        id: 6,
        title: "The Fate of Ophelia",
        artist: "Taylor Swift",
        vibe: "storytelling",
        vibeEmoji: "📖",
        spotifyId: null,
        artwork: null
    },
    {
        id: 7,
        title: "ZOU BISOU",
        artist: "Theodora, Jul",
        vibe: "amour",
        vibeEmoji: "💋",
        spotifyId: null,
        artwork: null
    },
    {
        id: 8,
        title: "BIRDS OF A FEATHER",
        artist: "Billie Eilish",
        vibe: "introspection",
        vibeEmoji: "🪶",
        spotifyId: null,
        artwork: null
    },
    {
        id: 9,
        title: "Biff pas d'love",
        artist: "Bouss",
        vibe: "rupture",
        vibeEmoji: "💔",
        spotifyId: null,
        artwork: null
    },
    {
        id: 10,
        title: "RUINART",
        artist: "R2",
        vibe: "ego",
        vibeEmoji: "🍾",
        spotifyId: null,
        artwork: null
    },
    {
        id: 11,
        title: "FASHION DESIGNA",
        artist: "Theodora",
        vibe: "ego",
        vibeEmoji: "👗",
        spotifyId: null,
        artwork: null
    },
    {
        id: 12,
        title: "CARTIER SANTOS",
        artist: "SDM",
        vibe: "ego",
        vibeEmoji: "⌚",
        spotifyId: null,
        artwork: null
    },
    {
        id: 13,
        title: "Disfruto",
        artist: "Carla Morrison",
        vibe: "nostalgie",
        vibeEmoji: "🌅",
        spotifyId: null,
        artwork: null
    },
    {
        id: 14,
        title: "Nostalgique",
        artist: "Jul",
        vibe: "nostalgie",
        vibeEmoji: "🥀",
        spotifyId: null,
        artwork: null
    },
    {
        id: 15,
        title: "Iris",
        artist: "The Goo Goo Dolls",
        vibe: "emotionnel",
        vibeEmoji: "🌸",
        spotifyId: null,
        artwork: null
    }
];

// Vibe category translations for display
const VIBE_LABELS = {
    introspection: "Introspection",
    ego: "Ego / Flex",
    amour: "Amour",
    fête: "Fête",
    night_drive: "Night Drive",
    storytelling: "Storytelling",
    rupture: "Rupture",
    nostalgie: "Nostalgie",
    emotionnel: "Émotionnel"
};

// Export for use in index.html
if (typeof window !== 'undefined') {
    window.SEED_SONGS = SEED_SONGS;
    window.VIBE_LABELS = VIBE_LABELS;
}
