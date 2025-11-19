/**
 * Internationalization (i18n) Module
 * Handles language state and text updates
 */

class I18nHandler {
    constructor() {
        this.defaultLanguage = 'en';
        this.supportedLanguages = ['en', 'de'];
        this.currentLanguage = localStorage.getItem('user_language') || this.defaultLanguage;
        
        if (!this.supportedLanguages.includes(this.currentLanguage)) {
            this.currentLanguage = this.defaultLanguage;
        }
        
        // Bind methods
        this.setLanguage = this.setLanguage.bind(this);
        this.translate = this.translate.bind(this);
        this.updatePage = this.updatePage.bind(this);
    }

    init() {
        this.renderLanguageSelector();
        this.updatePage();
        
        // Expose global translate function
        window.t = this.translate;
    }

    setLanguage(lang) {
        if (this.supportedLanguages.includes(lang)) {
            this.currentLanguage = lang;
            localStorage.setItem('user_language', lang);
            this.updatePage();
            
            // Dispatch event for other components
            window.dispatchEvent(new CustomEvent('languageChanged', { 
                detail: { language: lang } 
            }));
        }
    }

    translate(key) {
        // translations.js uses flat keys (e.g., "nav.home"), so we look up directly
        const lang = this.currentLanguage;
        if (translations[lang] && translations[lang][key]) {
            return translations[lang][key];
        }
        
        // Fallback to English
        if (translations['en'] && translations['en'][key]) {
            return translations['en'][key];
        }
        
        return key;
    }

    updatePage() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.translate(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                if (element.getAttribute('placeholder')) {
                    element.setAttribute('placeholder', translation);
                }
            } else {
                element.textContent = translation;
            }
        });

        // Update custom language selector display
        const button = document.getElementById('customLanguageSelector');
        if (button) {
            const languages = [
                { code: 'en', name: 'English', flag: 'https://flagcdn.com/w40/us.png' },
                { code: 'de', name: 'Deutsch', flag: 'https://flagcdn.com/w40/de.png' }
            ];
            const selectedLang = languages.find(l => l.code === this.currentLanguage) || languages[0];
            const buttonImg = button.querySelector('img');
            const buttonText = button.querySelector('.language-selector-text');
            if (buttonImg && buttonText && selectedLang) {
                buttonImg.src = selectedLang.flag;
                buttonImg.alt = `${selectedLang.name} flag`;
                buttonText.textContent = selectedLang.name;
            }
        }

        // Update HTML lang attribute
        document.documentElement.lang = this.currentLanguage;
    }

    renderLanguageSelector() {
        const navContainer = document.querySelector('.nav-menu');
        if (navContainer && !document.getElementById('customLanguageSelector')) {
            const li = document.createElement('li');
            li.className = 'nav-item';
            
            // Flag image URLs from a reliable CDN (increased resolution to w40)
            const languages = [
                { code: 'en', name: 'English', flag: 'https://flagcdn.com/w40/us.png' },
                { code: 'de', name: 'Deutsch', flag: 'https://flagcdn.com/w40/de.png' }
            ];
            
            const currentLang = languages.find(l => l.code === this.currentLanguage) || languages[0];
            
            // Create a custom dropdown with flags visible in both selected and options
            li.innerHTML = `
                <div class="custom-language-selector" style="position: relative; display: inline-block; margin-left: 10px;">
                    <button id="customLanguageSelector" class="language-selector-button" style="padding: 4px 25px 4px 35px; border-radius: 4px; font-size: 0.9em; min-width: 110px; border: 1px solid #ddd; background: white; cursor: pointer; text-align: left; position: relative;">
                        <img src="${currentLang.flag}" alt="${currentLang.name} flag" style="position: absolute; left: 6px; top: 50%; transform: translateY(-50%); width: 24px; height: 18px; object-fit: cover; border-radius: 2px; pointer-events: none;" />
                        <span class="language-selector-text">${currentLang.name}</span>
                        <span style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); pointer-events: none;">▼</span>
                    </button>
                    <div id="languageDropdown" class="language-dropdown" style="display: none; position: absolute; top: 100%; left: 0; margin-top: 2px; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); z-index: 1000; min-width: 110px; overflow: hidden;">
                        ${languages.map(lang => `
                            <div class="language-option" data-lang="${lang.code}" style="padding: 8px 10px 8px 35px; cursor: pointer; display: flex; align-items: center; position: relative; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor='white'">
                                <img src="${lang.flag}" alt="${lang.name} flag" style="position: absolute; left: 8px; top: 50%; transform: translateY(-50%); width: 24px; height: 18px; object-fit: cover; border-radius: 2px; pointer-events: none;" />
                                <span>${lang.name}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            navContainer.appendChild(li);
            
            // Set up custom dropdown functionality
            const button = document.getElementById('customLanguageSelector');
            const dropdown = document.getElementById('languageDropdown');
            const options = dropdown.querySelectorAll('.language-option');
            
            if (button && dropdown) {
                // Toggle dropdown
                button.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isOpen = dropdown.style.display !== 'none';
                    dropdown.style.display = isOpen ? 'none' : 'block';
                });
                
                // Handle option selection
                options.forEach(option => {
                    option.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const langCode = option.getAttribute('data-lang');
                        const selectedLang = languages.find(l => l.code === langCode);
                        
                        if (selectedLang) {
                            // Update button display
                            const buttonImg = button.querySelector('img');
                            const buttonText = button.querySelector('.language-selector-text');
                            buttonImg.src = selectedLang.flag;
                            buttonImg.alt = `${selectedLang.name} flag`;
                            buttonText.textContent = selectedLang.name;
                            
                            // Close dropdown
                            dropdown.style.display = 'none';
                            
                            // Change language
                            this.setLanguage(langCode);
                        }
                    });
                });
                
                // Close dropdown when clicking outside
                document.addEventListener('click', (e) => {
                    if (!button.contains(e.target) && !dropdown.contains(e.target)) {
                        dropdown.style.display = 'none';
                    }
                });
                
                // Update display when language changes externally
                window.addEventListener('languageChanged', () => {
                    const selectedLang = languages.find(l => l.code === this.currentLanguage) || languages[0];
                    const buttonImg = button.querySelector('img');
                    const buttonText = button.querySelector('.language-selector-text');
                    if (buttonImg && buttonText) {
                        buttonImg.src = selectedLang.flag;
                        buttonImg.alt = `${selectedLang.name} flag`;
                        buttonText.textContent = selectedLang.name;
                    }
                });
            }
        }
    }

}

// Initialize
const I18n = new I18nHandler();

// Wait for DOM and translations
document.addEventListener('DOMContentLoaded', () => {
    if (typeof translations !== 'undefined') {
        I18n.init();
    } else {
        console.error('Translations not loaded!');
    }
});

