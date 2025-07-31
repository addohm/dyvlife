// Back to top button
let backToTopButton = document.getElementById("backToTopBtn");

window.onscroll = function () { scrollFunction() };

function scrollFunction() {
  const btn = document.getElementById("backToTopBtn");
  const scrollThreshold = 20;

  if (document.body.scrollTop > scrollThreshold || document.documentElement.scrollTop > scrollThreshold) {
    btn.style.display = "block";
    setTimeout(() => btn.classList.add("show"), 10); // Small delay for display to take effect
  } else {
    btn.classList.remove("show");
    setTimeout(() => {
      if (!btn.classList.contains("show")) {
        btn.style.display = "none";
      }
    }, 300); // Match this with your CSS transition time
  }
}

function topFunction() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}