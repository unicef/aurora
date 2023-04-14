(function ($) {
    $(document).ready(function () {
        // var $me = $("#field_editor_script");
        var refreshUrl = $("#url").data("url");

        $(".toolbutton").on("click", function () {
            const action = $(this).data('action');
            const op = $(this).data('op');
            const fieldId = $(this).parents('div.cm-container').data('fieldid');
            const editor = $(`#${fieldId}`).data('CodeMirror');
            if (action) {
                window.cmToolBar.action(editor, action);
            } else if (op) {
                window.cmToolBar[op](editor);
            }
        });

        function update() {
            var formData = $("form").serialize();
            $(".field-error").remove();
            $.post(refreshUrl, formData)
                .done(function (data) {
                    $("iframe").each(function () {
                        $(this)[0].contentWindow.location = $(this).data("src")
                    })
                })
                .fail(function (xhr, err, txt) {
                    if (xhr.responseJSON) {
                        var errors = xhr.responseJSON;
                        var fieldErrors = errors.field;
                        var kwargsErrors = errors.kwargs;
                        var widget_kwargs = errors.widget_kwargs;
                        var smart = errors.smart;
                        for (const property in fieldErrors) {
                            $(`#id_field-${property}`).before(`<div class="field-error">${fieldErrors[property]}</div>`);
                        }
                    } else {
                        console.log(11111, xhr);
                        console.log(11111, err);
                        console.log(11111, txt);
                    }
                })
        }

        function checkForUpdate() {
            if ($("#autoRefresh").is(":checked")) {
                clearTimeout($.data(this, 'timer'));
                var wait = setTimeout(update, 500);
                $(this).data('timer', wait);
            } else {
                $("iframe.display").contents().find("*").css("background-color", "#bbbbbb");
            }
        }

        $('input[type=checkbox],input[type=radio]').on('click', function () {
            update();
        });
        $('select').on('change', function () {
            update();
        });
        $('input,textarea').on('keyup', function () {
            checkForUpdate();
        });
        $('textarea.js-editor').each(function (i, e) {
            var editor = $(e).data("CodeMirror");
            if (editor) {
                editor.refresh();
                editor.on('change', function () {
                    editor.save()
                })
            }
        });
        $("#refresh").on("click", function (e) {
            e.preventDefault();
            $("iframe").each(function () {
                $(this)[0].contentWindow.location = $(this).data("src")
            })
            return false;
        });

        $("#event_selector").on("change", function () {
            let sel = $(this).val();
            $('#events .code').removeClass('selected');
            $(`#event_${sel}`).addClass('selected').find('textarea.js-editor').each(function (i, e) {
                var editor = $(e).data("CodeMirror");
                if (editor) editor.refresh();
            });
        });
        $(".submit-row input[type=radio]").on("click", function (e) {
            var targetClass = $(this).data("target");
            $("iframe").hide();
            var $target = $("iframe." + targetClass);
            $(this).is(":checked") ? $target.show() : $target.hide();
        })
        $(".tabs th").on("click", function () {
            const targetName = $(this).data('target');
            $(`.tabs th`).removeClass('selected');
            $(`table.cfg-form`).addClass('collapsed');
            $(this).addClass('selected');
            $(`#${targetName}`).toggleClass('collapsed');
            $('textarea.js-editor').each(function (i, e) {
                var editor = $(e).data("CodeMirror");
                editor.refresh();
            });
        });
        $(".submit-row input[data-target=display]").trigger("click");
        $("#tabForms th:first").trigger("click");
    })
})(django.jQuery);
