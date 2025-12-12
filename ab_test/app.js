/**
 * VibeReco A/B Test - Main Application Logic
 *
 * Improvements included:
 * - DOM-safe rendering (no untrusted innerHTML for text)
 * - No inline onclick handlers (event delegation + dataset)
 * - Fixed step logic for 'result'
 * - Better a11y state updates (aria-pressed, aria-current)
 * - RAF progress loop managed correctly (cancel on stop)
 * - Better YouTube thumbnails (mqdefault)
 */

const state = {
    currentStep: 1,
    selectedSeedId: null,
    selectedSeed: null,
    playlistData: null,
    playlistMapping: null, // { A: "youtube" | "vibe", B: "youtube" | "vibe" }
    userVote: null, // "A" or "B"
    ratings: { emotional: 3, narrative: 3, keepability: 3 },
    testId: null,

    // Audio / YouTube
    isPlaying: false,
    currentVideoId: null,
    currentPlaylistLabel: null
};

let PLAYLISTS_DATA = null;

const elements = {
    // Steps
    steps: {
        1: document.getElementById('step-1'),
        2: document.getElementById('step-2'),
        3: document.getElementById('step-3'),
        result: document.getElementById('result-screen')
    },
    stepDots: document.querySelectorAll('.step-dot'),
    stepConnectors: document.querySelectorAll('.step-connector'),

    // Step 1
    seedGrid: document.getElementById('seed-grid'),
    startTestBtn: document.getElementById('start-test-btn'),

    // Step 2
    comparisonTitle: document.getElementById('comparison-title'),
    playlistATracks: document.getElementById('playlist-a-tracks'),
    playlistBTracks: document.getElementById('playlist-b-tracks'),
    playlistAColumn: document.getElementById('playlist-a-column'),
    playlistBColumn: document.getElementById('playlist-b-column'),
    voteBtns: document.querySelectorAll('.playlist-vote-btn'),
    backToSeeds: document.getElementById('back-to-seeds'),
    goToRating: document.getElementById('go-to-rating'),

    // Step 3
    chosenPlaylist: document.getElementById('chosen-playlist'),
    ratingEmotional: document.getElementById('rating-emotional'),
    ratingNarrative: document.getElementById('rating-narrative'),
    ratingKeepability: document.getElementById('rating-keepability'),
    ratingEmotionalValue: document.getElementById('rating-emotional-value'),
    ratingNarrativeValue: document.getElementById('rating-narrative-value'),
    ratingKeepabilityValue: document.getElementById('rating-keepability-value'),
    backToComparison: document.getElementById('back-to-comparison'),
    submitVote: document.getElementById('submit-vote'),

    // Result
    resultWinner: document.getElementById('result-winner'),
    resultDescription: document.getElementById('result-description'),
    newTestBtn: document.getElementById('new-test-btn'),

    // Audio
    audioPlayer: document.getElementById('audio-player'),
    audioPlayPause: document.getElementById('audio-play-pause'),
    playIcon: document.getElementById('play-icon'),
    pauseIcon: document.getElementById('pause-icon'),
    nowPlayingTitle: document.getElementById('now-playing-title'),
    nowPlayingArtist: document.getElementById('now-playing-artist'),
    audioProgress: document.querySelector('.audio-progress'),
    audioProgressFill: document.getElementById('audio-progress-fill'),
    audioPrev: document.getElementById('audio-prev'),
    audioNext: document.getElementById('audio-next')
};

// ------------------------------
// Init
// ------------------------------

document.addEventListener('DOMContentLoaded', init);

async function init() {
    loadYouTubeAPI();
    await loadPlaylistsData();
    renderSeedGrid();
    setupEventListeners();
}

// ------------------------------
// Data
// ------------------------------

async function loadPlaylistsData() {
    try {
        const response = await fetch('data/ab_test_playlists.json');
        if (!response.ok) {
            PLAYLISTS_DATA = null;
            return;
        }
        PLAYLISTS_DATA = await response.json();
    } catch {
        PLAYLISTS_DATA = null;
    }
}

function getPlaylistsForSeed(seedId) {
    if (PLAYLISTS_DATA?.playlists?.[String(seedId)]) {
        return PLAYLISTS_DATA.playlists[String(seedId)];
    }
    return generateDemoPlaylists();
}

function generateDemoPlaylists() {
    const demoTracks = [
        { title: "Track 1", artist: "Artist A" },
        { title: "Track 2", artist: "Artist B" },
        { title: "Track 3", artist: "Artist C" },
        { title: "Track 4", artist: "Artist D" },
        { title: "Track 5", artist: "Artist E" },
    ];

    const youtube = demoTracks.map((t, i) => ({
        position: i + 1,
        title: t.title,
        artist: t.artist,
        videoId: `demo-${i}`
    }));

    const vibereco = [...youtube]
        .sort(() => Math.random() - 0.5)
        .map((t, i) => ({ ...t, position: i + 1 }));

    return { youtube, vibereco };
}

// ------------------------------
// Rendering (DOM safe)
// ------------------------------

function renderSeedGrid() {
    const seeds = window.SEED_SONGS || [];
    elements.seedGrid.innerHTML = '';

    const frag = document.createDocumentFragment();

    for (const seed of seeds) {
        const card = document.createElement('div');
        card.className = 'seed-card';
        card.dataset.seedId = String(seed.id);
        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', '0');
        card.setAttribute('aria-label', `Choisir ${seed.title} - ${seed.artist}`);

        // Try cover from playlists if available
        let videoId = null;
        if (PLAYLISTS_DATA?.playlists?.[String(seed.id)]?.youtube?.[0]?.videoId) {
            videoId = PLAYLISTS_DATA.playlists[String(seed.id)].youtube[0].videoId;
        }

        if (videoId) {
            const img = document.createElement('img');
            img.className = 'seed-cover';
            img.alt = `${seed.title} - ${seed.artist}`;
            img.loading = 'lazy';
            img.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
            card.appendChild(img);
        } else {
            const ph = document.createElement('div');
            ph.className = 'seed-placeholder';
            // Placeholder sobre : initiale du titre plutôt qu’un emoji flashy
            ph.textContent = (seed.title?.trim()?.[0] || '♪').toUpperCase();
            card.appendChild(ph);
        }

        const title = document.createElement('div');
        title.className = 'seed-title';
        title.textContent = seed.title;

        const artist = document.createElement('div');
        artist.className = 'seed-artist';
        artist.textContent = seed.artist;

        const vibe = document.createElement('span');
        vibe.className = 'seed-vibe-tag';
        vibe.textContent = window.VIBE_LABELS?.[seed.vibe] || seed.vibe;

        card.append(title, artist, vibe);
        frag.appendChild(card);
    }

    elements.seedGrid.appendChild(frag);
}

// Tracks rendering
function renderPlaylist(label, tracks) {
    const container = label === 'A' ? elements.playlistATracks : elements.playlistBTracks;
    container.innerHTML = '';

    const frag = document.createDocumentFragment();

    tracks.forEach((track) => {
        const item = document.createElement('div');
        item.className = 'track-item';

        const pos = document.createElement('div');
        pos.className = 'track-position';
        pos.textContent = String(track.position);

        const cover = document.createElement('img');
        cover.className = 'track-cover';
        cover.alt = 'Cover';
        cover.loading = 'lazy';

        if (track.videoId && !track.videoId.startsWith('demo')) {
            cover.src = `https://img.youtube.com/vi/${track.videoId}/mqdefault.jpg`;
        } else {
            // keep empty but valid
            cover.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==';
        }

        const info = document.createElement('div');
        info.className = 'track-info';

        const tTitle = document.createElement('div');
        tTitle.className = 'track-title';
        tTitle.textContent = track.title;

        const tArtist = document.createElement('div');
        tArtist.className = 'track-artist';
        tArtist.textContent = track.artist;

        info.append(tTitle, tArtist);

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'track-play-btn';
        btn.dataset.title = track.title;
        btn.dataset.artist = track.artist;
        btn.dataset.videoId = track.videoId || '';
        btn.dataset.playlistLabel = label;
        btn.setAttribute('aria-label', `Lire ${track.title} — ${track.artist}`);

        btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
    `;

        item.append(pos, cover, info, btn);
        frag.appendChild(item);
    });

    container.appendChild(frag);
}

// ------------------------------
// Selection / Steps
// ------------------------------

function selectSeedById(seedId) {
    const idNum = Number(seedId);
    const seed = (window.SEED_SONGS || []).find(s => s.id === idNum);
    if (!seed) return;

    state.selectedSeedId = idNum;
    state.selectedSeed = seed;

    document.querySelectorAll('.seed-card.selected').forEach(c => c.classList.remove('selected'));
    const card = elements.seedGrid.querySelector(`.seed-card[data-seed-id="${seedId}"]`);
    if (card) card.classList.add('selected');

    elements.startTestBtn.disabled = false;
}

function stepIndex(step) {
    if (step === 'result') return 4;
    return Number(step);
}

function goToStep(step) {
    // Hide all
    Object.values(elements.steps).forEach(s => s.classList.remove('active'));

    // Body flag for result screen
    const isResult = step === 'result';
    document.body.classList.toggle('is-result', isResult);

    // Show target
    if (isResult) {
        elements.steps.result.classList.add('active');
        stopAndHidePlayer();
    } else {
        elements.steps[step].classList.add('active');
        if (step === 3) stopAndHidePlayer();
    }

    const cur = stepIndex(step);

    // Update dots + aria-current
    elements.stepDots.forEach((dot, i) => {
        const dotStep = i + 1;
        dot.classList.remove('active', 'completed');
        dot.removeAttribute('aria-current');

        if (dotStep === cur) {
            dot.classList.add('active');
            dot.setAttribute('aria-current', 'step');
        } else if (dotStep < cur) {
            dot.classList.add('completed');
        }
    });

    // Update connectors
    elements.stepConnectors.forEach((conn, i) => {
        conn.classList.toggle('completed', (i + 2) <= cur);
    });

    state.currentStep = step;

    // Focus first heading of active step for accessibility
    const active = document.querySelector('.step-container.active');
    const heading = active?.querySelector('h2');
    if (heading) heading.setAttribute('tabindex', '-1'), heading.focus({ preventScroll: false });
}

// ------------------------------
// Test flow
// ------------------------------

function startTest() {
    if (!state.selectedSeedId || !state.selectedSeed) return;

    state.testId = generateTestId();

    const seedData = getPlaylistsForSeed(state.selectedSeedId);
    if (!seedData?.youtube?.length || !seedData?.vibereco?.length) {
        alert("Playlists non disponibles pour ce seed.");
        return;
    }

    // Random mapping
    const flip = Math.random() > 0.5;
    state.playlistMapping = flip
        ? { A: 'youtube', B: 'vibe' }
        : { A: 'vibe', B: 'youtube' };

    // Balance lengths
    const minLength = Math.min(seedData.youtube.length, seedData.vibereco.length);
    const balancedYoutube = seedData.youtube.slice(0, minLength);
    const balancedVibe = seedData.vibereco.slice(0, minLength);

    state.playlistData = {
        A: flip ? balancedYoutube : balancedVibe,
        B: flip ? balancedVibe : balancedYoutube
    };

    renderPlaylist('A', state.playlistData.A);
    renderPlaylist('B', state.playlistData.B);

    elements.comparisonTitle.textContent = `Test pour : ${state.selectedSeed.title}`;

    // Reset vote state
    selectVote(null);

    goToStep(2);
}

function selectVote(vote) {
    state.userVote = vote;

    elements.voteBtns.forEach(btn => {
        const isSelected = vote && btn.dataset.vote === vote;
        btn.classList.toggle('selected', isSelected);
        btn.setAttribute('aria-pressed', isSelected ? 'true' : 'false');
    });

    elements.playlistAColumn.classList.toggle('selected', vote === 'A');
    elements.playlistBColumn.classList.toggle('selected', vote === 'B');

    elements.goToRating.disabled = !vote;
}

function goToRatingStep() {
    if (!state.userVote) return;
    elements.chosenPlaylist.textContent = `Playlist ${state.userVote}`;
    goToStep(3);
}

// ------------------------------
// Ratings
// ------------------------------

function setupRatingSliders() {
    const sliders = [
        { slider: elements.ratingEmotional, value: elements.ratingEmotionalValue, key: 'emotional' },
        { slider: elements.ratingNarrative, value: elements.ratingNarrativeValue, key: 'narrative' },
        { slider: elements.ratingKeepability, value: elements.ratingKeepabilityValue, key: 'keepability' }
    ];

    sliders.forEach(({ slider, value, key }) => {
        slider.addEventListener('input', () => {
            state.ratings[key] = Number(slider.value);
            value.textContent = slider.value;
        });
    });
}

// ------------------------------
// Submit
// ------------------------------

async function submitVote() {
    if (!state.userVote || !state.playlistMapping) return;

    const winnerSource = state.playlistMapping[state.userVote]; // 'youtube' | 'vibe'
    const voteData = {
        testId: state.testId,
        timestamp: new Date().toISOString(),
        seedId: state.selectedSeedId,
        seedTitle: state.selectedSeed?.title || '',
        vote: state.userVote,
        winnerSource,
        scores: state.ratings,
        mapping: state.playlistMapping
    };

    try {
        const response = await fetch('/api/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(voteData)
        });

        if (!response.ok) {
            storeVoteLocally(voteData);
        }
    } catch {
        storeVoteLocally(voteData);
    }

    showResult(winnerSource);
}

function storeVoteLocally(voteData) {
    const stored = JSON.parse(localStorage.getItem('vibereco_votes') || '[]');
    stored.push(voteData);
    localStorage.setItem('vibereco_votes', JSON.stringify(stored));
}

function showResult(winnerSource) {
    const isVibeReco = winnerSource === 'vibe';

    elements.resultWinner.textContent = isVibeReco ? 'VibeReco' : 'YouTube';
    elements.resultDescription.textContent = isVibeReco
        ? "Ta playlist préférée était générée par VibeReco. Le reranking sémantique a amélioré la cohérence perçue."
        : "Ta playlist préférée était l'ordre original de YouTube. L'algorithme de base reste performant sur ce type de vibe.";

    goToStep('result');
}

// ------------------------------
// Reset
// ------------------------------

function resetTest() {
    stopAndHidePlayer();

    state.selectedSeedId = null;
    state.selectedSeed = null;
    state.playlistData = null;
    state.playlistMapping = null;
    state.userVote = null;
    state.ratings = { emotional: 3, narrative: 3, keepability: 3 };
    state.testId = null;

    document.querySelectorAll('.seed-card.selected').forEach(c => c.classList.remove('selected'));
    elements.startTestBtn.disabled = true;

    selectVote(null);

    // Reset sliders UI
    [elements.ratingEmotional, elements.ratingNarrative, elements.ratingKeepability].forEach(s => s.value = '3');
    [elements.ratingEmotionalValue, elements.ratingNarrativeValue, elements.ratingKeepabilityValue].forEach(v => v.textContent = '3');

    goToStep(1);
}

// ------------------------------
// Audio / YouTube IFrame API
// ------------------------------

let ytPlayer = null;
let ytPlayerReady = false;
let rafId = null;

function loadYouTubeAPI() {
    if (window.YT && window.YT.Player) {
        ytPlayerReady = true;
        return;
    }
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(tag);
}

// Called by YouTube API when ready
window.onYouTubeIframeAPIReady = function () {
    ytPlayerReady = true;
};

function playTrack(title, artist, videoId, playlistLabel) {
    state.currentPlaylistLabel = playlistLabel || state.currentPlaylistLabel;

    elements.nowPlayingTitle.textContent = title || '-';
    elements.nowPlayingArtist.textContent = artist || '-';
    elements.audioPlayer.classList.add('visible');

    if (!videoId || videoId.startsWith('demo')) {
        // Pas de preview en demo
        state.isPlaying = false;
        updatePlayPauseIcon();
        return;
    }

    // Toggle if same
    if (state.currentVideoId === videoId && ytPlayer) {
        togglePlayPause();
        return;
    }

    state.currentVideoId = videoId;

    if (!ytPlayer && ytPlayerReady) {
        ensureHiddenPlayerDiv();
        ytPlayer = new YT.Player('yt-player', {
            height: '1',
            width: '1',
            videoId,
            playerVars: {
                autoplay: 1,
                controls: 0,
                disablekb: 1,
                fs: 0,
                modestbranding: 1,
                playsinline: 1
            },
            events: {
                onReady: (event) => {
                    event.target.playVideo();
                    state.isPlaying = true;
                    updatePlayPauseIcon();
                    startProgressLoop();
                },
                onStateChange: onPlayerStateChange
            }
        });
    } else if (ytPlayer) {
        ytPlayer.loadVideoById(videoId);
        state.isPlaying = true;
        updatePlayPauseIcon();
        startProgressLoop();
    } else {
        // API pas encore prête → retry léger
        setTimeout(() => playTrack(title, artist, videoId, playlistLabel), 350);
    }
}

function ensureHiddenPlayerDiv() {
    let playerDiv = document.getElementById('yt-player');
    if (!playerDiv) {
        playerDiv = document.createElement('div');
        playerDiv.id = 'yt-player';
        playerDiv.style.cssText = 'position:absolute;width:1px;height:1px;opacity:0;pointer-events:none;';
        document.body.appendChild(playerDiv);
    }
}

function onPlayerStateChange(event) {
    const YTPS = window.YT?.PlayerState;
    if (!YTPS) return;

    if (event.data === YTPS.ENDED) {
        state.isPlaying = false;
        updatePlayPauseIcon();
        stopProgressLoop();
    } else if (event.data === YTPS.PLAYING) {
        state.isPlaying = true;
        updatePlayPauseIcon();
        startProgressLoop();
    } else if (event.data === YTPS.PAUSED) {
        state.isPlaying = false;
        updatePlayPauseIcon();
        stopProgressLoop();
    }
}

function updatePlayPauseIcon() {
    elements.playIcon.style.display = state.isPlaying ? 'none' : 'block';
    elements.pauseIcon.style.display = state.isPlaying ? 'block' : 'none';
}

function startProgressLoop() {
    stopProgressLoop();
    rafId = requestAnimationFrame(updateProgress);
}

function stopProgressLoop() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
}

function updateProgress() {
    if (!ytPlayer || !state.isPlaying) return;

    const current = ytPlayer.getCurrentTime?.() || 0;
    const duration = ytPlayer.getDuration?.() || 1;
    const percent = Math.max(0, Math.min(100, (current / duration) * 100));

    elements.audioProgressFill.style.width = `${percent}%`;
    rafId = requestAnimationFrame(updateProgress);
}

function seekTo(clientX) {
    if (!ytPlayer || !state.currentVideoId) return;

    const rect = elements.audioProgress.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));

    const duration = ytPlayer.getDuration?.() || 0;
    const newTime = duration * percentage;

    if (duration > 0) {
        ytPlayer.seekTo(newTime, true);
        elements.audioProgressFill.style.width = `${percentage * 100}%`;
    }
}

function togglePlayPause() {
    if (!ytPlayer) return;

    if (state.isPlaying) {
        ytPlayer.pauseVideo();
        state.isPlaying = false;
        stopProgressLoop();
    } else {
        ytPlayer.playVideo();
        state.isPlaying = true;
        startProgressLoop();
    }
    updatePlayPauseIcon();
}

function stopAndHidePlayer() {
    stopProgressLoop();

    if (ytPlayer) {
        try { ytPlayer.pauseVideo(); } catch { }
    }

    state.isPlaying = false;
    state.currentVideoId = null;
    state.currentPlaylistLabel = null;

    elements.audioPlayer.classList.remove('visible');
    elements.audioProgressFill.style.width = '0%';
    updatePlayPauseIcon();
}

function playNext() {
    if (!state.currentPlaylistLabel || !state.playlistData || !state.currentVideoId) return;

    const currentList = state.playlistData[state.currentPlaylistLabel];
    if (!Array.isArray(currentList) || currentList.length === 0) return;

    const idx = currentList.findIndex(t => t.videoId === state.currentVideoId);
    if (idx === -1) return;

    const next = currentList[(idx + 1) % currentList.length];
    playTrack(next.title, next.artist, next.videoId, state.currentPlaylistLabel);
}

function playPrev() {
    if (!state.currentPlaylistLabel || !state.playlistData || !state.currentVideoId) return;

    const currentList = state.playlistData[state.currentPlaylistLabel];
    if (!Array.isArray(currentList) || currentList.length === 0) return;

    const idx = currentList.findIndex(t => t.videoId === state.currentVideoId);
    if (idx === -1) return;

    const prev = currentList[(idx - 1 + currentList.length) % currentList.length];
    playTrack(prev.title, prev.artist, prev.videoId, state.currentPlaylistLabel);
}

// ------------------------------
// Utilities
// ------------------------------

function generateTestId() {
    // Better uniqueness when available
    if (window.crypto?.randomUUID) return `test_${crypto.randomUUID()}`;
    return 'test_' + Date.now() + '_' + Math.random().toString(36).slice(2, 11);
}

// ------------------------------
// Events
// ------------------------------

function setupEventListeners() {
    // Seed selection (click + keyboard)
    elements.seedGrid.addEventListener('click', (e) => {
        const card = e.target.closest('.seed-card');
        if (!card) return;
        selectSeedById(card.dataset.seedId);
    });

    elements.seedGrid.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        const card = e.target.closest('.seed-card');
        if (!card) return;
        e.preventDefault();
        selectSeedById(card.dataset.seedId);
    });

    // Step 1
    elements.startTestBtn.addEventListener('click', startTest);

    // Step 2
    elements.voteBtns.forEach(btn => {
        btn.addEventListener('click', () => selectVote(btn.dataset.vote));
    });

    elements.backToSeeds.addEventListener('click', () => goToStep(1));
    elements.goToRating.addEventListener('click', goToRatingStep);

    // Step 3
    setupRatingSliders();
    elements.backToComparison.addEventListener('click', () => goToStep(2));
    elements.submitVote.addEventListener('click', submitVote);

    // Result
    elements.newTestBtn.addEventListener('click', resetTest);

    // Track play buttons (event delegation, no inline onclick)
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.track-play-btn');
        if (!btn || btn.id === 'audio-play-pause') return; // exclude main play/pause
        playTrack(btn.dataset.title, btn.dataset.artist, btn.dataset.videoId, btn.dataset.playlistLabel);
    });

    // Audio controls
    elements.audioPlayPause.addEventListener('click', togglePlayPause);

    // Seek (pointer-friendly)
    elements.audioProgress.addEventListener('pointerdown', (e) => {
        seekTo(e.clientX);
    });

    if (elements.audioPrev) elements.audioPrev.addEventListener('click', playPrev);
    if (elements.audioNext) elements.audioNext.addEventListener('click', playNext);
}
