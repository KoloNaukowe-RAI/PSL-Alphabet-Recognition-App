function updateContent(langData) {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        element.textContent = langData[key];
    });
}

function setLanguagePreference(lang) {
    localStorage.setItem('language', lang);
}

async function fetchLanguageData(lang) {
    switch(lang){
        case 'EN':
            var src = json_translation_EN;
        break;
        case 'PL':
            var src = json_translation_PL;
        break;
        default:
            var src = json_translation_EN;
    }
    console.log(src);
    const response = await fetch(src);
    return response.json();
}

async function changeLanguage(lang) {
    const langData = await fetchLanguageData(lang);
    updateContent(langData);
}

// Call updateContent() on page load
window.addEventListener('DOMContentLoaded', async () => {
    const userPreferredLanguage = localStorage.getItem('language') || 'EN';
    const langData = await fetchLanguageData(userPreferredLanguage);
    updateContent(langData);
});