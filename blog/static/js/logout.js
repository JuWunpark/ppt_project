window.addEventListener("beforeunload", function () {
    navigator.sendBeacon('logout/');
});