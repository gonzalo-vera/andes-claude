// FormSubmit: URL de agradecimiento en el origen actual (siempre home con ?enviado=1)
(function initFormSubmitNext() {
  const nextInput = document.querySelector('#contactForm input[data-form-next]');
  if (!nextInput) return;
  try {
    const u = new URL(window.location.origin);
    u.searchParams.set('enviado', '1');
    nextInput.value = u.toString();
  } catch {
    nextInput.value = `${window.location.origin}/?enviado=1`;
  }
})();

// Navbar scroll
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 60);
});

// Mobile menu
const toggle = document.getElementById('navToggle');
const navLinks = document.querySelector('.nav-links');
toggle?.addEventListener('click', () => {
  navLinks?.classList.toggle('open');
});
navLinks?.querySelectorAll('a').forEach((a) => {
  a.addEventListener('click', () => navLinks.classList.remove('open'));
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
    document.querySelectorAll('.project-item').forEach(item => {
      const show = filter === 'all' || item.dataset.category === filter;
      item.classList.toggle('hidden', !show);
    });
  });
});

// Form submit — feedback visual antes de enviar a FormSubmit
document.getElementById('contactForm')?.addEventListener('submit', (e) => {
  const btn = e.target.querySelector('button[type="submit"]');
  btn.textContent = 'Enviando...';
  btn.disabled = true;
});

// Mostrar mensaje de éxito si volvió desde FormSubmit
if (new URLSearchParams(window.location.search).get('enviado') === '1') {
  const form = document.getElementById('contactForm');
  if (form) {
    form.innerHTML = `
      <div style="text-align:center; padding: 48px 24px;">
        <div style="font-size:3rem; margin-bottom:16px;">✓</div>
        <h3 style="font-family:'Montserrat',sans-serif; color:#1A2B4A; margin-bottom:12px;">¡Mensaje enviado!</h3>
        <p style="color:#888;">Te responderemos a la brevedad en menos de 24 horas.</p>
      </div>`;
  }
}
