let playerName = '';
if (localStorage.getItem("playerName") === null) {
    localStorage.setItem("playerName", '');
}
playerName = localStorage.getItem("playerName")
let language = localStorage.getItem("language") || 'EN';

let theme = 'dark';
if (localStorage.getItem("theme") === null) {
    localStorage.setItem("theme", theme);
}
let hand = 'right';
if (localStorage.getItem("hand") === null) {
    localStorage.setItem("hand", hand);
}
hand = localStorage.getItem("hand")
theme = localStorage.getItem("theme")
let difficulty = 'easy';
if (localStorage.getItem("difficulty") === null) {
    localStorage.setItem("difficulty", difficulty);
}
difficulty = localStorage.getItem("difficulty")
document.getElementById('player-name').value = playerName
document.getElementById('language-select').value = language
document.getElementById('difficulty-select').value = difficulty
document.getElementById('theme-select').value = theme
document.getElementById('hand-select').value = hand

document.getElementById('language-select').addEventListener('change', (event) => {
    language = event.target.value;
    setLanguagePreference(language);
});

document.getElementById('theme-select').addEventListener('change', (event) => {
    theme = event.target.value;
    localStorage.setItem('theme', theme);
    updateTheme();
});

let stream_set = false;
if (sessionStorage.getItem('stream_set') === null) {
    sessionStorage.setItem('stream_set', false);
}
let timer;

function updateTheme() {
    if (localStorage.getItem("theme") === 'light') {
        document.body.classList.add('light-mode');
    } else {
        document.body.classList.remove('light-mode');
    }
}

document.getElementById('save-settings-button').addEventListener('click', () => {
    playerName = document.getElementById('player-name').value;
    difficulty = document.getElementById('difficulty-select').value;
    theme = document.getElementById('theme-select').value;
    hand = document.getElementById('hand-select').value;
    if (playerName.length > 15) {
        alert('Player name must be 15 characters or less.');
        return;
    }
    if (playerName) {
        localStorage.setItem('playerName', playerName);
        localStorage.setItem('difficulty', difficulty);
        localStorage.setItem('theme', theme);
        localStorage.setItem('hand', hand);
        $('#settingsModal').modal('hide');
        showLoadingScreen();
        setTimeout(hideLoadingScreen, 2000);
        updateTheme();
        changeLanguage(language);
        updateHandedness(hand);
    } else {
        alert('Please enter your name.');
    }
});

function showLoadingScreen() {
    document.getElementById('loading-screen').style.display = 'flex';
}

function hideLoadingScreen() {
    document.getElementById('loading-screen').style.display = 'none';
}

function updatePlayer() {
    document.getElementById('player-name').value = playerName;
}

document.getElementById('start-game-button').addEventListener('click', () => {
    playerName = localStorage.getItem('playerName');
    difficulty = localStorage.getItem('difficulty');
    theme = localStorage.getItem('theme');
    if (!playerName) {
        alert('Please enter your name in the settings.');
        return;
    }
    document.getElementById('main-menu').classList.add('hidden');
    document.getElementById('game-section').classList.remove('hidden');
    startGame();
    showNotification("Game Started", "The game has started!");
});

document.getElementById('add-player-button').addEventListener('click', () => {
    let newPlayerName = prompt("Enter player's name:");
    if (newPlayerName) {
        if (newPlayerName.length > 15) {
            alert('Player name must be 15 characters or less.');
            return;
        }
        playerName = newPlayerName;
        localStorage.setItem('playerName', playerName);
        alert(`Player ${newPlayerName} added.`);
        updatePlayer();
    }
});

document.getElementById('back-button').addEventListener('click', () => {
    document.getElementById('menu-open-button').display = 'block'
    document.getElementById('game-section').classList.add('hidden');
    document.getElementById('main-menu').classList.remove('hidden');
});

document.getElementById('exit-button').addEventListener('click', () => {
    if (confirm("Are you sure you want to exit?")) {
        window.close();
    }
});

document.getElementById('tutorial-button').addEventListener('click', () => {
    $('#tutorialModal').modal('show');
});

function startGame() {
    const duration = document.getElementById('duration').value;
    document.getElementById('menu-open-button').display = 'none'
    fetch(`/start-game?player_name=${playerName}&language=${language}&difficulty=${difficulty}&hand=${hand}`)
        .then(response => response.json())
        .then(data => {
            const randomImage = document.getElementById('word-image');
            if (randomImage) {
                randomImage.src = data.image_url;
                randomImage.style.display = 'block';
            } else {
                console.error('Random image element not found.');
            }

            if (sessionStorage.getItem('stream_set') === 'false') {
                document.getElementById('live-camera-feed').style.display = 'block';
                document.getElementById('live-camera-feed').src = "/live-camera-feed/";
                sessionStorage.setItem('stream_set', true);
            }

            if (!stream_set) {
                updateRecognizedLetters();
                startTimer(duration * 60);
                stream_set = true;
            }
                                     
            document.getElementById('player_name_fill').textContent = playerName;
            document.getElementById('score_fill').textContent = data.score;
            timer = duration * 60;
        })
        .catch(error => {
            console.error('Error starting game:', error);
        });
}

function resetGame() {
    const duration = document.getElementById('duration').value;
    fetch(`/reset-game?language=${language}&difficulty=${difficulty}`)
        .then(response => response.json())
        .then(data => {
            const randomImage = document.getElementById('word-image');
            if (randomImage) {
                randomImage.src = data.image_url;
                randomImage.style.display = 'block';
            } else {
                console.error('Random image element not found.');
            }

            document.getElementById('score_fill').textContent = data.score;
        })
        .catch(error => {
            console.error('Error resetting game:', error);
        });
}

function startTimer(duration) {
    timer = duration;
    const timerDisplay = document.getElementById('timer');
    const interval = setInterval(() => {
        const minutes = String(Math.floor(timer / 60)).padStart(2, '0');
        const seconds = String(timer % 60).padStart(2, '0');

        timerDisplay.textContent = `${minutes}:${seconds}`;

        if (timer <= 0) {
            clearInterval(interval);
            alert("Time's up!");
            showNotification("Time's Up", "The game has ended!");
        } else {
            timer--;
        }
    }, 1000);
}

function updateRecognizedLetters() {
    const lettersDisplay = document.getElementById('letters_fill');
    const scoreDisplay = document.getElementById('score_fill');

    function fetchRecognizedLetters() {
        fetch('/live-feed-letters/?update_letters=true')
            .then(response => response.json())
            .then(data => {
                if (!(data.shown_letters.length == 0)) {
                    lettersDisplay.textContent = data.shown_letters.join('');
                } else {
                    lettersDisplay.textContent = '';
                }
                scoreDisplay.textContent = data.score;
            })
            .catch(error => console.error('Error fetching recognized letters:', error));
    }

    setInterval(fetchRecognizedLetters, 500);
}

function updateHandedness(hand) {
    fetch('/handedness-update?hand=' + hand)
        .then(response => response.json())
        .then(data => {
            console.log('Handedness updated:', data);
        })
        .catch(error => console.error('Error updating handedness:', error));
}

document.querySelectorAll('.star').forEach(star => {
    star.addEventListener('click', () => {
        const rating = star.getAttribute('data-value');
        document.querySelectorAll('.star').forEach(s => s.classList.remove('checked'));
        for (let i = 0; i < rating; i++) {
            document.querySelectorAll('.star')[i].classList.add('checked');
        }
        alert(`You rated this game ${rating} stars.`);
    });
});

function openNav() {
    document.getElementById("mySidebar").style.width = "250px";
}

function closeNav() {
    document.getElementById("mySidebar").style.width = "0";
}

function showNotification(title, body) {
    if (Notification.permission === "granted") {
        new Notification(title, { body });
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                new Notification(title, { body });
            }
        });
    }
}

function nextStep(step) {
    document.querySelectorAll('.tutorial-step').forEach((element) => {
        element.classList.add('hidden');
    });
    document.getElementById(`tutorial-step-${step}`).classList.remove('hidden');
}

function prevStep(step) {
    document.querySelectorAll('.tutorial-step').forEach((element) => {
        element.classList.add('hidden');
    });
    document.getElementById(`tutorial-step-${step}`).classList.remove('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
    updateTheme();
});

document.getElementById('reset-button').addEventListener('click', () => {
    resetGame();
});