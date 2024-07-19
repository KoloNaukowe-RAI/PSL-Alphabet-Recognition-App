function changeVideo(srcVideo){
    goBackButton = document.getElementById("goBackButton");
    video = document.getElementById("video_player");
    video.pause();
    video.src = srcVideo;
    video.load();
    goBackButton.scrollIntoView({ block: 'end',  behavior: 'smooth' });
}

function scrollUp(){
    top_of_page = document.getElementById("heder");
    top_of_page.scrollIntoView({ block: 'start',  behavior: 'smooth' });
}

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

updateTheme();