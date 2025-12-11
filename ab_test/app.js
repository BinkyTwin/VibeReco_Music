/**
 * VibeReco A/B Test - Main Application Logic
 * 
 * Handles:
 * - Seed selection UI
 * - Playlist display and comparison
 * - Voting and rating flow
 * - Audio preview playback
 * - API calls to save votes (Vercel KV)
 */

// ============================================
// State Management
// ============================================

const state = {
    currentStep: 1,
    selectedSeedId: null,
    selectedSeed: null,
    playlistData: null,
    playlistMapping: null, // { A: "youtube" | "vibe", B: "youtube" | "vibe" }
    userVote: null, // "A" or "B"
    ratings: {
        emotional: 3,
        narrative: 3,
        keepability: 3
    },
    testId: null,
    isPlaying: false,
    currentAudio: null,
    currentVideoId: null
};

// ============================================
// Pre-generated Playlists Data
// Will be loaded from data/ab_test_playlists.json
// ============================================

let PLAYLISTS_DATA = null;

// ============================================
// DOM Elements
// ============================================

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
    audioElement: document.getElementById('audio-element'),
    audioPlayPause: document.getElementById('audio-play-pause'),
    playIcon: document.getElementById('play-icon'),
    pauseIcon: document.getElementById('pause-icon'),
    nowPlayingTitle: document.getElementById('now-playing-title'),
    nowPlayingArtist: document.getElementById('now-playing-artist'),
    audioProgressFill: document.getElementById('audio-progress-fill'),
    audioPrev: document.getElementById('audio-prev'),
    audioNext: document.getElementById('audio-next')
};

// ============================================
// Initialization
// ============================================

async function init() {
    console.log('VibeReco A/B Test - Initializing...');

    // Load YouTube IFrame API
    loadYouTubeAPI();

    // Load pre-generated playlists
    await loadPlaylistsData();

    // Render seed grid
    renderSeedGrid();

    // Setup event listeners
    setupEventListeners();

    console.log('VibeReco A/B Test - Ready!');
}

async function loadPlaylistsData() {
    try {
        const response = await fetch('data/ab_test_playlists.json');
        if (response.ok) {
            PLAYLISTS_DATA = await response.json();
            console.log('Loaded playlist data:', PLAYLISTS_DATA);
        } else {
            console.warn('No pre-generated playlists found. Using demo mode.');
            PLAYLISTS_DATA = null;
        }
    } catch (error) {
        console.warn('Could not load playlists:', error);
        PLAYLISTS_DATA = null;
    }
}

// ============================================
// Seed Grid Rendering
// ============================================

function renderSeedGrid() {
    const seeds = window.SEED_SONGS || [];

    elements.seedGrid.innerHTML = seeds.map(seed => {
        // Find video ID from playlists data if available
        let videoId = null;
        if (PLAYLISTS_DATA && PLAYLISTS_DATA.playlists && PLAYLISTS_DATA.playlists[seed.id]) {
            const ytPlaylist = PLAYLISTS_DATA.playlists[seed.id].youtube;
            if (ytPlaylist && ytPlaylist.length > 0) {
                videoId = ytPlaylist[0].videoId;
            }
        }

        const imageUrl = videoId
            ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`
            : null;

        return `
        <div class="seed-card" data-seed-id="${seed.id}">
            ${imageUrl
                ? `<img src="${imageUrl}" class="seed-cover" alt="${seed.title}">`
                : `<div class="seed-vibe-emoji">${seed.vibeEmoji}</div>`
            }
            <div class="seed-title">${seed.title}</div>
            <div class="seed-artist">${seed.artist}</div>
            <span class="seed-vibe-tag">${window.VIBE_LABELS?.[seed.vibe] || seed.vibe}</span>
        </div>
    `}).join('');

    // Add click handlers
    document.querySelectorAll('.seed-card').forEach(card => {
        card.addEventListener('click', () => selectSeed(card));
    });
}

function selectSeed(cardElement) {
    // Remove previous selection
    document.querySelectorAll('.seed-card.selected').forEach(c => c.classList.remove('selected'));

    // Select new
    cardElement.classList.add('selected');

    const seedId = parseInt(cardElement.dataset.seedId);
    state.selectedSeedId = seedId;
    state.selectedSeed = window.SEED_SONGS.find(s => s.id === seedId);

    // Enable start button
    elements.startTestBtn.disabled = false;
}

// ============================================
// Step Navigation
// ============================================

function goToStep(stepNumber) {
    // Hide all steps
    Object.values(elements.steps).forEach(step => step.classList.remove('active'));

    // Show target step
    if (stepNumber === 'result') {
        elements.steps.result.classList.add('active');
        stopAndHidePlayer();
    } else {
        elements.steps[stepNumber].classList.add('active');
        if (stepNumber === 3) {
            stopAndHidePlayer();
        }
    }

    // Update step dots
    elements.stepDots.forEach((dot, index) => {
        const dotStep = index + 1;
        dot.classList.remove('active', 'completed');

        if (dotStep === stepNumber) {
            dot.classList.add('active');
        } else if (dotStep < stepNumber) {
            dot.classList.add('completed');
        }
    });

    // Update connectors
    elements.stepConnectors.forEach((conn, index) => {
        conn.classList.toggle('completed', index + 1 < stepNumber);
    });

    state.currentStep = stepNumber;
}

// ============================================
// Playlist Display
// ============================================

function startTest() {
    if (!state.selectedSeedId) return;

    // Generate test ID
    state.testId = generateTestId();

    // Get playlist data for this seed
    const seedData = getPlaylistsForSeed(state.selectedSeedId);

    if (!seedData) {
        alert('Playlists non disponibles pour ce seed. Génère-les d\'abord avec generate_playlists.py');
        return;
    }

    // Randomly assign A/B
    const flip = Math.random() > 0.5;
    state.playlistMapping = flip
        ? { A: 'youtube', B: 'vibe' }
        : { A: 'vibe', B: 'youtube' };

    // Balance playlist lengths
    const minLength = Math.min(seedData.youtube.length, seedData.vibereco.length);
    console.log(`Balancing playlists to length: ${minLength}`);

    const balancedYoutube = seedData.youtube.slice(0, minLength);
    const balancedVibereco = seedData.vibereco.slice(0, minLength);

    state.playlistData = {
        A: flip ? balancedYoutube : balancedVibereco,
        B: flip ? balancedVibereco : balancedYoutube
    };

    // Render playlists
    renderPlaylist('A', state.playlistData.A);
    renderPlaylist('B', state.playlistData.B);

    // Update title
    elements.comparisonTitle.textContent = `Test pour: ${state.selectedSeed.title}`;

    // Go to step 2
    goToStep(2);
}

function getPlaylistsForSeed(seedId) {
    // If we have pre-generated data
    if (PLAYLISTS_DATA && PLAYLISTS_DATA.playlists) {
        return PLAYLISTS_DATA.playlists[String(seedId)];
    }

    // Demo mode: generate fake playlists
    return generateDemoPlaylists();
}

function generateDemoPlaylists() {
    // Create demo playlists for testing UI
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

    // Shuffle for vibereco
    const vibereco = [...youtube].sort(() => Math.random() - 0.5)
        .map((t, i) => ({ ...t, position: i + 1 }));

    return { youtube, vibereco };
}

function renderPlaylist(label, tracks) {
    const container = label === 'A' ? elements.playlistATracks : elements.playlistBTracks;

    container.innerHTML = tracks.map(track => `
        <div class="track-item" data-video-id="${track.videoId || ''}">
            <div class="track-position">${track.position}</div>
            ${track.videoId
            ? `<img src="https://img.youtube.com/vi/${track.videoId}/default.jpg" class="track-cover" alt="Cover">`
            : ''}
            <div class="track-info">
                <div class="track-title">${track.title}</div>
                <div class="track-artist">${track.artist}</div>
            </div>
            <button class="track-play-btn" onclick="playTrack('${track.title.replace(/'/g, "\\'")}', '${track.artist.replace(/'/g, "\\'")}', '${track.videoId || ''}', '${label}')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
            </button>
        </div>
    `).join('');
}

// ============================================
// Voting Logic
// ============================================

function selectVote(vote) {
    state.userVote = vote;

    // Update UI
    elements.voteBtns.forEach(btn => {
        btn.classList.toggle('selected', btn.dataset.vote === vote);
    });

    elements.playlistAColumn.classList.toggle('selected', vote === 'A');
    elements.playlistBColumn.classList.toggle('selected', vote === 'B');

    // Enable continue button
    elements.goToRating.disabled = false;
}

function goToRatingStep() {
    if (!state.userVote) return;

    elements.chosenPlaylist.textContent = `Playlist ${state.userVote}`;
    goToStep(3);
}

// ============================================
// Rating Sliders
// ============================================

function setupRatingSliders() {
    const sliders = [
        { slider: elements.ratingEmotional, value: elements.ratingEmotionalValue, key: 'emotional' },
        { slider: elements.ratingNarrative, value: elements.ratingNarrativeValue, key: 'narrative' },
        { slider: elements.ratingKeepability, value: elements.ratingKeepabilityValue, key: 'keepability' }
    ];

    sliders.forEach(({ slider, value, key }) => {
        slider.addEventListener('input', () => {
            state.ratings[key] = parseInt(slider.value);
            value.textContent = slider.value;
        });
    });
}

// ============================================
// Submit Vote
// ============================================

async function submitVote() {
    const winnerSource = state.playlistMapping[state.userVote];
    const loserSource = state.playlistMapping[state.userVote === 'A' ? 'B' : 'A'];

    const voteData = {
        testId: state.testId,
        timestamp: new Date().toISOString(),
        seedId: state.selectedSeedId,
        seedTitle: state.selectedSeed.title,
        vote: state.userVote,
        winnerSource: winnerSource,
        scores: state.ratings,
        mapping: state.playlistMapping
    };

    console.log('Submitting vote:', voteData);

    // Try to save to API
    try {
        const response = await fetch('/api/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(voteData)
        });

        if (response.ok) {
            console.log('Vote saved successfully!');
        } else {
            console.warn('Failed to save vote to API');
        }
    } catch (error) {
        console.warn('API not available, vote stored locally only:', error);
        // Store locally as fallback
        storeVoteLocally(voteData);
    }

    // Show result
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
        ? 'Ta playlist préférée était générée par VibeReco. Le reranking sémantique a amélioré la cohérence perçue !'
        : 'Ta playlist préférée était l\'ordre original de YouTube. L\'algorithme de base reste performant sur ce type de vibe.';

    goToStep('result');
}

// ============================================
// New Test
// ============================================

function resetTest() {
    // Reset state
    state.selectedSeedId = null;
    state.selectedSeed = null;
    state.playlistData = null;
    state.playlistMapping = null;
    state.userVote = null;
    state.ratings = { emotional: 3, narrative: 3, keepability: 3 };
    state.testId = null;

    // Reset UI
    document.querySelectorAll('.seed-card.selected').forEach(c => c.classList.remove('selected'));
    elements.startTestBtn.disabled = true;
    elements.goToRating.disabled = true;
    elements.voteBtns.forEach(btn => btn.classList.remove('selected'));
    elements.playlistAColumn.classList.remove('selected');
    elements.playlistBColumn.classList.remove('selected');

    // Reset sliders
    [elements.ratingEmotional, elements.ratingNarrative, elements.ratingKeepability].forEach(s => s.value = 3);
    [elements.ratingEmotionalValue, elements.ratingNarrativeValue, elements.ratingKeepabilityValue].forEach(v => v.textContent = '3');

    // Go to step 1
    goToStep(1);
}

// ============================================
// Audio Playback (YouTube IFrame API)
// ============================================

let ytPlayer = null;
let ytPlayerReady = false;

// Load YouTube IFrame API
function loadYouTubeAPI() {
    if (window.YT && window.YT.Player) {
        ytPlayerReady = true;
        return;
    }

    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
}

// Called by YouTube API when ready
window.onYouTubeIframeAPIReady = function () {
    ytPlayerReady = true;
    console.log('YouTube IFrame API ready');
};

function playTrack(title, artist, videoId, playlistLabel) {
    // Save context
    if (playlistLabel) {
        state.currentPlaylistLabel = playlistLabel;
    }

    // Update now playing
    elements.nowPlayingTitle.textContent = title;
    elements.nowPlayingArtist.textContent = artist;
    elements.audioPlayer.classList.add('visible');

    if (!videoId || videoId === '' || videoId.startsWith('demo')) {
        console.warn('No valid videoId for this track');
        return;
    }

    // If same track, toggle play/pause
    if (state.currentVideoId === videoId && ytPlayer) {
        if (state.isPlaying) {
            ytPlayer.pauseVideo();
            state.isPlaying = false;
        } else {
            ytPlayer.playVideo();
            state.isPlaying = true;
        }
        updatePlayPauseIcon();
        return;
    }

    state.currentVideoId = videoId;

    // Create or update player
    if (!ytPlayer && ytPlayerReady) {
        // Create hidden player container
        let playerDiv = document.getElementById('yt-player');
        if (!playerDiv) {
            playerDiv = document.createElement('div');
            playerDiv.id = 'yt-player';
            playerDiv.style.cssText = 'position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none;';
            document.body.appendChild(playerDiv);
        }

        ytPlayer = new YT.Player('yt-player', {
            height: '1',
            width: '1',
            videoId: videoId,
            playerVars: {
                'autoplay': 1,
                'controls': 0,
                'disablekb': 1,
                'fs': 0,
                'modestbranding': 1,
                'playsinline': 1
            },
            events: {
                'onReady': onPlayerReady,
                'onStateChange': onPlayerStateChange
            }
        });
    } else if (ytPlayer) {
        ytPlayer.loadVideoById(videoId);
    } else {
        // API not loaded yet, wait
        console.log('Waiting for YouTube API...');
        setTimeout(() => playTrack(title, artist, videoId, playlistLabel), 500);
        return;
    }

    state.isPlaying = true;
    updatePlayPauseIcon();
}

function onPlayerReady(event) {
    event.target.playVideo();
    state.isPlaying = true;
    updatePlayPauseIcon();
}

function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.ENDED) {
        state.isPlaying = false;
        updatePlayPauseIcon();
    } else if (event.data === YT.PlayerState.PLAYING) {
        state.isPlaying = true;
        updatePlayPauseIcon();
        // Update progress bar
        updateProgress();
    } else if (event.data === YT.PlayerState.PAUSED) {
        state.isPlaying = false;
        updatePlayPauseIcon();
    }
}

function updatePlayPauseIcon() {
    elements.playIcon.style.display = state.isPlaying ? 'none' : 'block';
    elements.pauseIcon.style.display = state.isPlaying ? 'block' : 'none';
}

function updateProgress() {
    if (!ytPlayer || !state.isPlaying) return;

    const current = ytPlayer.getCurrentTime() || 0;
    const duration = ytPlayer.getDuration() || 1;
    const percent = (current / duration) * 100;

    elements.audioProgressFill.style.width = `${percent}%`;

    if (state.isPlaying) {
        requestAnimationFrame(updateProgress);
    }
}

function togglePlayPause() {
    if (ytPlayer) {
        if (state.isPlaying) {
            ytPlayer.pauseVideo();
        } else {
            ytPlayer.playVideo();
        }
        state.isPlaying = !state.isPlaying;
        updatePlayPauseIcon();
    }
}

function stopAndHidePlayer() {
    if (ytPlayer && state.isPlaying) {
        ytPlayer.pauseVideo();
    }
    state.isPlaying = false;
    state.currentVideoId = null;
    elements.audioPlayer.classList.remove('visible');
    updatePlayPauseIcon();
}

function playNext() {
    if (!state.currentPlaylistLabel || !state.playlistData) return;

    const currentList = state.playlistData[state.currentPlaylistLabel];
    if (!currentList) return;

    const currentIndex = currentList.findIndex(t => t.videoId === state.currentVideoId);
    if (currentIndex === -1) return;

    const nextIndex = (currentIndex + 1) % currentList.length;
    const nextTrack = currentList[nextIndex];

    playTrack(nextTrack.title, nextTrack.artist, nextTrack.videoId, state.currentPlaylistLabel);
}

function playPrev() {
    if (!state.currentPlaylistLabel || !state.playlistData) return;

    const currentList = state.playlistData[state.currentPlaylistLabel];
    if (!currentList) return;

    const currentIndex = currentList.findIndex(t => t.videoId === state.currentVideoId);
    if (currentIndex === -1) return;

    const prevIndex = (currentIndex - 1 + currentList.length) % currentList.length;
    const prevTrack = currentList[prevIndex];

    playTrack(prevTrack.title, prevTrack.artist, prevTrack.videoId, state.currentPlaylistLabel);
}

// ============================================
// Utilities
// ============================================

function generateTestId() {
    return 'test_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// ============================================
// Event Listeners Setup
// ============================================

function setupEventListeners() {
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

    // Audio - use togglePlayPause to actually control YouTube player
    elements.audioPlayPause.addEventListener('click', togglePlayPause);
    if (elements.audioPrev) elements.audioPrev.addEventListener('click', playPrev);
    if (elements.audioNext) elements.audioNext.addEventListener('click', playNext);
}

// ============================================
// Start App
// ============================================

document.addEventListener('DOMContentLoaded', init);

// Expose for HTML onclick handlers
window.playTrack = playTrack;
