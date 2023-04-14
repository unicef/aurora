(function ($) {
    window.cmToolBar = {
        save: function (cm) {
            $('form').submit();
        },
        action: function (cm, action) {
            const expression = "'use strict';const doc=cm.getDoc(); doc." + action + "()";
            eval(expression);
        },
        expand: function (cm) {
            cm.focus();
            const $c = $(cm.getTextArea()).parents('.cm-container');
            $c.addClass('fieldEditor-fullscreen');
            cm.setOption("fullScreen", !cm.getOption("fullScreen"));
            cm.focus();
            if (cm.getOption("fullScreen")) {
                $("#fieldEditor .submit-row").hide();
                $("#toggle-nav-sidebar").hide();
            } else {
                $("#fieldEditor .submit-row").show();
                $("#toggle-nav-sidebar").show();
            }
        },
        run: function (cm) {

        }
    };
})(django.jQuery);
