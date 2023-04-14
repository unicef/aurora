TODAY = new Date();
dateutil = {
    today: TODAY,
    years18: new Date(new Date().setDate(TODAY.getDate() - (365 * 18))),
    years2: new Date(new Date().setDate(TODAY.getDate() - (365 * 2))),
    isDate: function (d) {
        try {
            new Date(d)
            return true
        } catch (e) {
            return false;
        }
    },
    getAge: function (date2, date1) {
        // use today's date if ageAtDate is not provided
        if (typeof date1 == "undefined")
            date1 = new Date();
        let years = new Date(date1).getFullYear() - new Date(date2).getFullYear();
        let month = new Date(date1).getMonth() - new Date(date2).getMonth();
        let dateDiff = new Date(date1).getDay() - new Date(date2).getDay();
        if (dateDiff < 0) {
            month -= 1;
        }
        if (month < 0) {
            years -= 1;
        }
        return years;
    }
};
// _ = {
//     is_child: function (d) {
//         return d && dateutil.getAge(d) < 18
//     },
//     is_baby: function (d) {
//         return d && dateutil.getAge(d) <= 2
//     },
//     is_future: function (d) {
//         return d && Date.parse(d) > dateutil.today
//     },
// };
// _.is_adult = function (d) {
//     return !_.is_child(d)
// };

smart_fs = {
    getCollector: function (cd) {
        var collectors = cd.filter(e => e.role_i_c === "y");
        if (collectors.length === 1) {
            return collectors[0]
        }
        return null;
    }
}
smart = {
    sameAs: function (sender, target) {
        var $sender = $(sender);
        var $form = $sender.parents(".form-container");
        var $target = $form.find("[data-flex='" + target + "']");
        if ($sender.val() == $target.val()) {
            $sender.css("background-color", "#d7f6ca");
        } else {
            $sender.css("background-color", "#e1adad");
        }
    },
    preventSubmit: function (sender) {
        var $form = $(sender).parents("form");
        var $target = $form.find("input[type=submit]");
        var valid = false;

        if ($(sender).is("input[type=\"checkbox\"]")) {
            valid = $(sender).is(":checked");
        } else if ($(sender).is("input[type=\"radio\"]")) {
            valid = $(sender).val() === "y";
        } else {
            valid = !!$(sender).val();
        }
        if (valid) {
            $target.prop("disabled", false);
        } else {
            $target.prop("disabled", true);
        }
    },
    showHideInForm: function (sender, target, showHide) {
        try {
            var $form = $(sender).parents(".form-container");
            var $target = $form.find(target);
            if (showHide) {
                $target.show();
            } else {
                $target.hide();
            }
        } catch (error) {
            console.error(error);
        }
    },
    setRequired: function (targets, onOff) {
        $(targets).each(function (i, e) {
            if (onOff) {
                $(e).attr("required", true);
                $c.find('.required-label').show();
            } else {
                $(e).attr("required", false);
                $c.find('.required-label').hide();
            }
        });
    },
    setRequiredOnValue: function (sender, targets, value) {
        try {
            var cmp = value.toLowerCase();
            var $form = $(sender).parents(".form-container");
            $form.find(targets).each(function (i, e) {
                $c = $(e).parents(".field-container");
                if ($(sender).val() == cmp) {
                    $(e).attr("required", true);
                    $c.find('.required-label').show();
                } else {
                    $(e).attr("required", false);
                    $c.find('.required-label').hide();
                }
            })
        } catch (error) {
            console.error(error);
        }
    },
    getSiblingField: function (sender, target) {
        var $sender = $(sender);
        var $form = $sender.parents(".form-container");
        return $form.find("[data-flex='" + target + "']");
    },
    getSibling: function (sender, target) {
        var $form = $(sender).parents(".form-container");
        return $form.find(target).parents(".field-container");
    },
    showHideDependant: function (sender, target, value) {
        try {
            var cmp = null;
            if (Array.isArray(value)) {
                cmp = function (a, b) {
                    b.includes(a);
                }
            } else {
                cmp = function (a, b) {
                    return a == b
                };
            }
            var cleared = value.toLowerCase();
            var $form = $(sender).parents(".form-container");
            var $target = $form.find(target).parents(".field-container");
            if (cmp($(sender).val(), cleared)) {
                $target.show();
            } else {
                $target.hide();
            }
        } catch (error) {
            console.error(error);
        }
    },
    setDependant: function (sender, target, value) {
        try {
            var $form = $(sender).parents(".form-container");
            var $target = $form.find(target);
            $target.prop("disabled", !($(sender).val() == value));
        } catch (error) {
            console.error(error);
        }
    },
    is_adult: function (d) {
        return d && Date.parse(d) <= dateutil.years18 ? true : false;
    },
    handleQuestion: function (e) {
        var $container = $(e).parents("fieldset").find(".field-container");
        if ($(e).is(":checked")) {
            $container.show();
        } else {
            $container.hide();
        }
    },
    updateDeleteLabel: function (sender, label) {
        $(sender).parents(".form-container").find(".delete-button").text(label + $(sender).val());
    },
    getControlledField: function (questionCheckbox) {
        var $container = $(questionCheckbox).parents("fieldset").find(".field-container");
        return $container.find("input,select, textarea");
    },
    has_any_value: function ($sender) {
        var inputType = $sender.attr('type')
        if ((inputType === "radio") || (inputType === "checkbox")) {
            $sender.is(":checked");
        } else {
            return $sender.val().trim() !== '';
        }
    },
    getField: function ($sender) {
        var $fieldset = $($sender).parents("fieldset");
        var $form = $($sender).parents(".form-container");
        var $container = $fieldset.find(".field-container");
        var $question = $fieldset.find(".question");
        var $input = $container.find("input,select, textarea");
        var inputType = $sender.attr('type')
        var value = null;
        var hasValue = null;
        if ((inputType === "radio") || (inputType === "checkbox")) {
            value = $sender.val();
            hasValue = $sender.is(":checked");
        } else {
            value = $sender.val();
            hasValue = (value !== '');
        }
        return {
            'fieldset': $fieldset,
            'container': $container,
            'question': $question,
            'input': $input,
            'inputType': inputType,
            'form': $form,
            'value': value,
            'hasValue': hasValue,
            'checked': $sender.is(":checked"),
        }
    }
};
