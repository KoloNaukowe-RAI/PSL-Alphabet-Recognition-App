function updateTheme() {
    if (localStorage.getItem("theme") === 'light') {
        document.body.classList.add('light-mode-qr');
    } else {
        document.body.classList.remove('light-mode-qr');
    }
}

updateTheme();