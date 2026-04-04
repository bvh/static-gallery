const slider = document.querySelector('.slider');
const list = slider.querySelector('ul');

const closeBtn = slider.querySelector('.close-button');
const infoBtn = slider.querySelector('.info-button');
const prevBtn = slider.querySelector('.prev-button');
const nextBtn = slider.querySelector('.next-button');
let openerThumbnail = null;

let infoPanelOpen = false;

function openInfoPanel() {
    infoPanelOpen = true;
    slider.classList.add('info-open');
    infoBtn.classList.add('active');
    infoBtn.setAttribute('aria-expanded', 'true');
    for (const panel of slider.querySelectorAll('.info')) {
        panel.setAttribute('aria-hidden', 'true');
    }
    const slide = currentSlide();
    const panel = slide?.querySelector('.info');
    if (panel) panel.setAttribute('aria-hidden', 'false');
}

function closeInfoPanel() {
    if (!infoPanelOpen) return;
    infoPanelOpen = false;
    slider.classList.remove('info-open');
    infoBtn.classList.remove('active');
    infoBtn.setAttribute('aria-expanded', 'false');
    for (const panel of slider.querySelectorAll('.info')) {
        panel.setAttribute('aria-hidden', 'true');
    }
}

function toggleInfoPanel() {
    if (infoPanelOpen) {
        closeInfoPanel();
    } else {
        openInfoPanel();
    }
}

infoBtn.addEventListener('click', toggleInfoPanel);

function currentSlide() {
    const scrollLeft = list.scrollLeft;
    const width = list.clientWidth;
    const index = Math.round(scrollLeft / width);
    return list.children[index] ?? null;
}

function syncHash() {
    const slide = currentSlide();
    if (slide && slide.id && location.hash !== '#' + slide.id) {
        history.replaceState(null, '', '#' + slide.id);
    }
}

let lastSettledSlide = null;
function onScrollSettle() {
    lastSettledSlide = currentSlide();
    syncHash();
    updateButtonStates();
}

if ('onscrollend' in window) {
    let scrolling = false;
    list.addEventListener('scroll', () => {
        if (!scrolling) {
            scrolling = true;
            closeInfoPanel();
            if (document.activeElement === infoBtn) infoBtn.blur();
        }
    });
    list.addEventListener('scrollend', () => {
        scrolling = false;
        onScrollSettle();
    });
} else {
    let scrollTimer;
    list.addEventListener('scroll', () => {
        const slide = currentSlide();
        if (slide !== lastSettledSlide) {
            closeInfoPanel();
            if (document.activeElement === infoBtn) infoBtn.blur();
        }
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(onScrollSettle, 50);
    });
}

function scrollToTarget() {
    const hash = location.hash.slice(1);
    if (!hash) return;
    const target = document.getElementById(hash);
    if (target && target.parentElement === list) {
        target.scrollIntoView({ behavior: 'instant', inline: 'start', block: 'nearest' });
    }
}

function isSliderOpen() {
    return !!slider.querySelector(':target');
}

function focusSlider() {
    if (isSliderOpen()) {
        list.focus();
    }
}

function returnFocusToThumbnail() {
    if (openerThumbnail) {
        openerThumbnail.focus();
        openerThumbnail = null;
    }
}

window.addEventListener('hashchange', () => {
    scrollToTarget();
    if (isSliderOpen()) {
        focusSlider();
    } else {
        closeInfoPanel();
        returnFocusToThumbnail();
    }
});

requestAnimationFrame(() => {
    scrollToTarget();
    focusSlider();
});

// Track which thumbnail opened the slider
document.querySelector('#gallery').addEventListener('click', (e) => {
    const link = e.target.closest('a[href^="#"]');
    if (link) openerThumbnail = link;
});

function getFocusableElements() {
    const elements = [infoBtn];                                // info (upper left)
    const slide = currentSlide();
    const titleLink = slide?.querySelector('.slide-caption a');
    if (infoPanelOpen) {
        const permalink = slide?.querySelector('.info-panel .permalink');
        if (permalink) elements.push(permalink);               // permalink (upper middle)
    }
    elements.push(closeBtn);                                   // close (upper right)
    if (prevBtn && !prevBtn.disabled) elements.push(prevBtn);  // prev (lower left)
    if (titleLink) elements.push(titleLink);                   // title (lower middle)
    if (nextBtn && !nextBtn.disabled) elements.push(nextBtn);  // next (lower right)
    return elements;
}

document.addEventListener('keydown', (e) => {
    if (!isSliderOpen()) return;

    if (e.key === 'Escape') {
        if (infoPanelOpen) {
            closeInfoPanel();
        } else {
            location.hash = '#gallery';
        }
    } else if (e.key === 'ArrowRight') {
        list.scrollBy({ left: list.clientWidth, behavior: 'smooth' });
    } else if (e.key === 'ArrowLeft') {
        list.scrollBy({ left: -list.clientWidth, behavior: 'smooth' });
    } else if (e.key === 'Tab') {
        const focusable = getFocusableElements();
        if (focusable.length === 0) return;

        const currentIndex = focusable.indexOf(document.activeElement);

        if (e.shiftKey) {
            e.preventDefault();
            const prevIndex = currentIndex <= 0 ? focusable.length - 1 : currentIndex - 1;
            focusable[prevIndex].focus();
        } else {
            e.preventDefault();
            const nextIndex = currentIndex >= focusable.length - 1 ? 0 : currentIndex + 1;
            focusable[nextIndex].focus();
        }
    } else if (e.key === 'i') {
        const tag = document.activeElement?.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || document.activeElement?.isContentEditable) {
            return;
        }
        if (infoPanelOpen) {
            closeInfoPanel();
        } else {
            openInfoPanel();
        }
    }
});

prevBtn.addEventListener('click', () => {
    list.scrollBy({ left: -list.clientWidth, behavior: 'smooth' });
});

nextBtn.addEventListener('click', () => {
    list.scrollBy({ left: list.clientWidth, behavior: 'smooth' });
});

function updateButtonStates() {
    prevBtn.disabled = list.scrollLeft <= 0;
    nextBtn.disabled = list.scrollLeft >= list.scrollWidth - list.clientWidth;
}

list.addEventListener('scroll', updateButtonStates);
new ResizeObserver(updateButtonStates).observe(list);
updateButtonStates();
