document.addEventListener("DOMContentLoaded", function () {
    var path = window.location.pathname;
    document.querySelectorAll("#sidebar-nav .side-item").forEach(function (link) {
        var href = link.getAttribute("href");
        if (href && href !== "#" && (path === href || (path.startsWith(href) && href.length > 1))) {
            link.classList.add("active");
        }
    });
});
