// Web3Forms: apunta a gracias.html en el mismo origen + auto-reply con email del usuario
(function initFormSubmitNext() {
  const nextInput = document.querySelector('#contactForm input[data-form-next]');
  if (!nextInput) return;
  nextInput.value = `${window.location.origin}/gracias`;

  const emailInput = document.querySelector('#contactForm input[name="email"]');
  const replytoInput = document.querySelector('#contactForm input[data-autoreply-email]');
  if (emailInput && replytoInput) {
    emailInput.addEventListener('input', () => { replytoInput.value = emailInput.value; });
  }
})();

// Navbar scroll
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 60);
});

// Mobile menu — toggle hamburger ↔ X
const toggle = document.getElementById('navToggle');
const navLinks = document.querySelector('.nav-links');
function closeMobileNav() {
  navLinks?.classList.remove('open');
  toggle?.classList.remove('open');
  toggle?.setAttribute('aria-label', 'Menú');
  document.body.classList.remove('nav-open');
}
toggle?.addEventListener('click', () => {
  const isOpen = navLinks?.classList.toggle('open');
  toggle.classList.toggle('open', isOpen);
  toggle.setAttribute('aria-label', isOpen ? 'Cerrar menú' : 'Menú');
  document.body.classList.toggle('nav-open', isOpen);
});
navLinks?.querySelectorAll('a').forEach((a) => {
  a.addEventListener('click', closeMobileNav);
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && navLinks?.classList.contains('open')) closeMobileNav();
});

// GTM helpers
function gtmPush(data) {
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push(data);
}

// Track WhatsApp clicks
document.querySelectorAll('a[href*="wa.me"]').forEach((el) => {
  const source = el.classList.contains('whatsapp-fab') ? 'fab' : 'contact_section';
  el.addEventListener('click', () => gtmPush({ event: 'whatsapp_click', source }));
});

// Track phone clicks
document.querySelectorAll('a[href^="tel:"]').forEach((el) => {
  el.addEventListener('click', () => gtmPush({ event: 'phone_click' }));
});

// Track email clicks
document.querySelectorAll('a[href^="mailto:"]').forEach((el) => {
  el.addEventListener('click', () => gtmPush({ event: 'email_click' }));
});

// Counter animation
function animateCounter(el) {
  const target = +el.dataset.target;
  const duration = 2000;
  const step = target / (duration / 16);
  let current = 0;
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = target >= 10000
      ? Math.floor(current).toLocaleString('es-CL')
      : Math.floor(current);
    if (current >= target) clearInterval(timer);
  }, 16);
}

const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.querySelectorAll('.stat-number').forEach(animateCounter);
      statsObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.4 });

const statsSection = document.querySelector('.stats');
if (statsSection) statsObserver.observe(statsSection);

// Scroll animations
const aosObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => {
        entry.target.classList.add('aos-visible');
      }, i * 80);
      aosObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('[data-aos]').forEach(el => aosObserver.observe(el));

// Project filter
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    document.querySelectorAll('.proyecto-card').forEach(item => {
      const show = filter === 'all' || item.dataset.category === filter;
      item.classList.toggle('hidden', !show);
    });
    gtmPush({ event: 'project_filter_click', filter_value: filter });
  });
});

// Form submit — GTM event + visual feedback
document.getElementById('contactForm')?.addEventListener('submit', (e) => {
  const btn = e.target.querySelector('button[type="submit"]');
  const servicio = e.target.querySelector('[name="servicio"]')?.value || '';
  btn.textContent = 'Enviando...';
  btn.disabled = true;
  gtmPush({ event: 'form_submitted', service: servicio });
});

// Cookie banner
(function initCookieBanner() {
  if (localStorage.getItem('cookies_accepted')) return;
  const banner = document.getElementById('cookieBanner');
  if (!banner) return;
  banner.style.display = 'flex';
  document.getElementById('cookieAccept')?.addEventListener('click', () => {
    localStorage.setItem('cookies_accepted', '1');
    banner.style.display = 'none';
    gtmPush({ event: 'cookie_consent_granted' });
  });
})();
