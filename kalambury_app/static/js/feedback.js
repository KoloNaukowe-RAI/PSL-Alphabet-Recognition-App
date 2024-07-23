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

document.getElementById('feedback-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const email = document.getElementById('email').value;
    const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    if (!emailPattern.test(email)) {
        alert('Please enter a valid email address.');
        return;
    }
    const name = document.getElementById('name').value;
    if (/[^a-zA-Z0-9]/.test(name)) {
        alert('Name can only contain alphanumeric characters.');
        return;
    }
    this.submit();
});

function openNav() {
    document.getElementById("mySidebar").style.width = "250px";
}

function closeNav() {
    document.getElementById("mySidebar").style.width = "0";
}

function updateTheme() {
    if (localStorage.getItem("theme") === 'light') {
        document.body.classList.add('light-mode');
    } else {
        document.body.classList.remove('light-mode');
    }
}
if (sessionStorage.getItem('stream_set') === 'true') {
    sessionStorage.setItem('stream_set', false);
}
updateTheme();