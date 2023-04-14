// window.addEventListener("load", function(event) {
//     if (window.Sentry !== undefined) {
//         var script = document.getElementById("script-sentry");
//         const pk = $("meta[name=\"RegId\"]").attr("content");
//         const slug = $("meta[name=\"Survey\"]").attr("content");
//         Sentry.init({
//             dsn: script.dataset.dsn,
//             release: script.dataset.version,
//             tracesSampleRate: 1.0,
//             ignoreErrors: [
//                 "datepicker.inputField.after is not a function",
//                 "num.toString(...).padStart is not a function",
//                 "Unexpected token =>",
//                 "Unexpected identifier",
//             ]
//         });
//     }
// });
