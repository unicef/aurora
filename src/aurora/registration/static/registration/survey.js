(function ($) {
    var queryParams = window.location.search.substring(1).split('&').reduce(function (q, query) {
        var chunks = query.split('=');
        var key = chunks[0];
        var value = decodeURIComponent(chunks[1]);
        value = isNaN(Number(value)) ? value : Number(value);
        return (q[key] = value, q);
    }, {});
    var gst_session = function () {
        return queryParams['s'];
    }
    $(function () {
        // we need this HACK to manage the stupid cache system in front of the app
        const pk = $("meta[name=\"RegId\"]").attr("content");
        const sessionUrl = gst_session();
        $.get("/api/registration/" + pk + "/version/?" + Math.random(), function (data) {
            var parts = location.href.split("/");
            const version = parseInt(parts[parts.length - 2]);
            if (version !== data.version) {
                location.href = data.url;
            } else if (data.auth && (data.session_id !== sessionUrl)) {
                location.href = data.url;
            } else if (!data.auth && sessionUrl) {
                location.href = data.url;
            }
        });
    });
})($);
