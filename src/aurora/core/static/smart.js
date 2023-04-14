if ($ === undefined) {
    $ = django.jQuery;
}

(function ($) {
    $(function () {
        $(".field-container.required span.required").each(function (i, e) {
            $(e).removeClass("hidden");
        })
        $(".required_by_question").each(function (i, e) {
            var $question = $(e).parents('fieldset').find('.question-visibility');
            var $container = $(e).parents("fieldset").find(".field-container");
            var $input = $container.find("input,select");
            $question.on("change", function (e) {
                $input.attr("required", $(this).is(":checked"));
            });
        });
        //
        // $("#registrationForm").on("submit", function (e) {
        //     $(this).find("input[type=submit]").prop("disabled", "disabled").val(gettext("Please wait..."));
        // });
        //
        $("[data-visibility=hidden]").parents(".field-container").hide();

        $("[data-trigger=change]").each(function (i, e) {
            try{
                $(e).trigger("change");
            }catch (e){
            }
        });

        $(".errorlist").each(function (i, e) {
            var $container = $(e).parents("fieldset").find(".field-container");
            $container.show();
        });
        // display inputs with values
        $(".question-visibility").each(function (i, e) {
            var $container = $(e).parents("fieldset").find(".field-container");
            var $input = $container.find("input,select, textarea");
            if (smart.has_any_value($input)) {
                $(e).prop("checked", "checked");
                $container.show();
            }
        }).on("click", function () {
            smart.handleQuestion(this);
        });
        // trigger onload events
        // $('[data-onload]').each(function () {
        //     eval($(this).data('onload'));
        // });
    });
})($);
