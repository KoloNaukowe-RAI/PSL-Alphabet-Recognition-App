function updateTheme() {
    if (localStorage.getItem("theme") === 'light') {
        document.body.classList.add('light-mode-qr');
    } else {
        document.body.classList.remove('light-mode-qr');
    }
}
function openNav() {
    document.getElementById("mySidebar").style.width = "250px";
}

function closeNav() {
    document.getElementById("mySidebar").style.width = "0";
}
document.addEventListener('DOMContentLoaded', () => {
    updateTheme();
});