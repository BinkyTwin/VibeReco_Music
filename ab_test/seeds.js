/**
 * Official benchmark seedset for VibeReco A/B Testing
 *
 * Improvements:
 * - Vibe keys normalized to ASCII slugs (no accents) to avoid future bugs
 * - Labels remain French for UI
 */

const SEED_SONGS = [
    { id: 1, title: "Melodrama", artist: "Disiz, Theodora", vibe: "introspection", spotifyId: null, artwork: null },
    { id: 2, title: "DIPLOMATICO", artist: "ELGRANDETOTO", vibe: "ego", spotifyId: null, artwork: null },
    { id: 3, title: "LOVE YOU", artist: "Nono La Grinta", vibe: "amour", spotifyId: null, artwork: null },
    { id: 4, title: "Génération Impolie", artist: "Franglish, KeBlack", vibe: "fete", spotifyId: null, artwork: null },
    { id: 5, title: "PARISIENNE", artist: "GIMS, La Mano 1.9", vibe: "night_drive", spotifyId: null, artwork: null },
    { id: 6, title: "The Fate of Ophelia", artist: "Taylor Swift", vibe: "storytelling", spotifyId: null, artwork: null },
    { id: 7, title: "ZOU BISOU", artist: "Theodora, Jul", vibe: "amour", spotifyId: null, artwork: null },
    { id: 8, title: "BIRDS OF A FEATHER", artist: "Billie Eilish", vibe: "introspection", spotifyId: null, artwork: null },
    { id: 9, title: "Biff pas d'love", artist: "Bouss", vibe: "rupture", spotifyId: null, artwork: null },
    { id: 10, title: "RUINART", artist: "R2", vibe: "ego", spotifyId: null, artwork: null },
    { id: 11, title: "FASHION DESIGNA", artist: "Theodora", vibe: "ego", spotifyId: null, artwork: null },
    { id: 12, title: "CARTIER SANTOS", artist: "SDM", vibe: "ego", spotifyId: null, artwork: null },
    { id: 13, title: "Disfruto", artist: "Carla Morrison", vibe: "nostalgie", spotifyId: null, artwork: null },
    { id: 14, title: "Nostalgique", artist: "Jul", vibe: "nostalgie", spotifyId: null, artwork: null },
    { id: 15, title: "Iris", artist: "The Goo Goo Dolls", vibe: "emotionnel", spotifyId: null, artwork: null }
];

const VIBE_LABELS = {
    introspection: "Introspection",
    ego: "Ego / Flex",
    amour: "Amour",
    fete: "Fête",
    night_drive: "Night Drive",
    storytelling: "Storytelling",
    rupture: "Rupture",
    nostalgie: "Nostalgie",
    emotionnel: "Émotionnel"
};

if (typeof window !== 'undefined') {
    window.SEED_SONGS = SEED_SONGS;
    window.VIBE_LABELS = VIBE_LABELS;
}
