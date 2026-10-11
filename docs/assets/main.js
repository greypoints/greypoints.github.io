/* 灰点作品集 · 交互脚本
   只做三件事：阅读进度条、目录当前章节高亮、移动端目录折叠。
   动效一律线性/短时，不做花哨过渡。 */
(function () {
  "use strict";

  /* 1) 阅读进度条 */
  var bar = document.getElementById("progressBar");
  if (bar) {
    var tick = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
    };
    document.addEventListener("scroll", tick, { passive: true });
    window.addEventListener("resize", tick);
    tick();
  }

  /* 2) 目录：滚动时高亮当前章节 + 移动端折叠 */
  var toc = document.getElementById("toc");
  if (!toc) return;

  var toggle = document.getElementById("tocToggle");
  if (toggle) {
    toggle.addEventListener("click", function () { toc.classList.toggle("open"); });
  }

  var links = Array.prototype.slice.call(toc.querySelectorAll("nav a"));
  var heads = links
    .map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); })
    .filter(Boolean);

  if (!heads.length || !("IntersectionObserver" in window)) return;

  var spy = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var i = heads.indexOf(entry.target);
        if (i < 0) return;
        links.forEach(function (a) { a.classList.remove("active"); });
        links[i].classList.add("active");
      });
    },
    { rootMargin: "-92px 0px -68% 0px", threshold: 0 }
  );

  heads.forEach(function (h) { spy.observe(h); });
})();
