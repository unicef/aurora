;(function ($) {
    const NUMBERS = ['month', 'number', 'week'];
    const DATES = ['date', 'time'];
    const STRINGS = ['email', 'tel', 'text', 'url'];

    var highLight = function (onOff) {
        if (onOff) {
            this.__oldBorder = this.$.css("border");
            this.$.css("border", "1px solid red");
        } else {
            this.$.css("border", this.__oldBorder);
        }
        return this;
    };
    window.debug = function (arguments) {
        var log;
        if (window.parent.document.getElementById('debugLog')) {
            log = window.parent.document.getElementById('debugLog');
        } else {
            log = window.document.getElementById('debugLog');
        }
        if (log) {
            $(log).append(arguments);
            $(log).append("\n");
        }
    }
    window.aurora = {
        Module: function (config) {
            var self = this;
            var errorsStack = {};

            self.$ = $("#formContainer");
            var $form = $("#registrationForm");
            self.$submit = $form.find("input[type=submit]");
            self.config = config;
            self.name = config.name;
            self.setError = function (msg) {
                self.$.find('.alert-message').html(msg);
            };
            self.pushError = function (f) {
                errorsStack[f] = true;
            };
            self.popError = function (f) {
                errorsStack[f] = false;
                // var ret = false;
                var ret = _.filter(_.values(errorsStack), function (i) {
                    return i === true;
                });
            }
            self.getError = function (f) {
                return errorsStack[f];
            }
            self.getErrors = function () {
                return _.filter(_.keys(errorsStack), function (i, e) {
                    return errorsStack[i] === true;
                });
            }
            var _fields = null;
            self.fields = function () {
                if (_fields == null) {
                    _fields = {}
                    $form.find(`:input[data-flex-name]`).each(function (i, e) {
                        var f = new aurora.Field(e);
                        _fields[f.name] = f;
                    });
                }
                return _fields
            };

            self.isValid = function () {
                var ret = true
                for (let i = 0, keys = Object.keys(self.fields()), ii = keys.length; i < ii; i++) {
                    var f = self.fields()[keys[i]];
                    var ok = f.isValid();
                    if (ok === false) {
                        ret = false;
                        break;
                    }
                }
                return ret;
            }

            self.enableSubmit = function (onOff) {
                if (onOff) {
                    self.$submit.prop("disabled", "")
                } else {
                    self.$submit.prop("disabled", "disabled")
                }
                return self;
            }

            $form.on('submit', function (e) {
                if (self.isValid()) {
                    $form.find("input[type=submit]").prop("disabled", "disabled").val(gettext("Please wait..."));
                    return true;
                } else {
                    return false;
                }
            });
        },
        ChildForm: function (fs, index, origin) {
            var self = this;
            self.origin = origin;
            self.formset = fs;
            const $me = $(self.origin);
            self.$ = $me;
            const number = index;
            self.highLight = highLight;
            var _fields = null;
            self.fields = function () {
                if (_fields == null) {
                    _fields = {}
                    $me.find(`:input[data-flex-name]`).each(function (i, e) {
                        var f = new aurora.Field(e);
                        _fields[f.name] = f;
                    });
                }
                return _fields
            };
        },
        FlexForm: function (name) {
            var self = this;
            const $me = $(".form-container." + name);

            self.$ = $me;
            // var $container=$(".form-container");
            var _fields = null;
            self.fields = function () {
                if (_fields == null) {
                    _fields = {}
                    $me.find(`:input[data-flex-name]`).each(function (i, e) {
                        var f = new aurora.Field(e);
                        _fields[f.name] = f;
                    });
                }
                return _fields
            };
        },
        Formset: function (name) {
            var self = this;
            const $me = $(".formset.formset-" + name);
            self.name = name;
            self.$ = $me;
            self.entries = function () {
                var ret = [];
                $me.find('.form-container.' + self.name).each(function (i, e) {
                    ret.push(new aurora.ChildForm(self, i, e));
                })
                return ret;
            }
            self.highLight = highLight;
        },
        Field: function (origin) {
            var self = this;
            self.origin = origin;
            const $me = $(origin);
            const $fieldset = $me.parents('fieldset');
            const id = $fieldset.data("fid");
            const pk = $fieldset.data("fpk");
            const $form = $me.parents('form');
            const $fieldContainer = $me.parents('.field-container');
            const $formContainer = $me.parents('.form-container');
            // const $input = $fieldset.find(`#${id}`);
            const $input = $(origin);
            const inputType = $input.attr("type");
            const initial = {
                required: $input.attr("required"),
            }
            self.$ = $fieldset;
            self.$input = $input;
            self.$fieldset = $fieldset;
            self.flexName = $fieldset.data("fname");
            self.name = $input.attr("name");
            self.$description = $fieldset.find('.description');
            self.$hint = $fieldset.find('.hint');

            self.highLight = highLight;
            self.setRequired = function (onOff) {
                $input.attr("required", onOff);
                onOff ? $fieldset.find('.required-label').show() : $fieldset.find('.required-label').hide();
                return self;
            };
            self.hide = function () {
                $fieldContainer.hide();
                return self;
            };
            self.show = function () {
                $fieldContainer.show();
                return self;
            };
            self.toggle = function (value) {
                $fieldContainer.toggle();
                if (!$fieldContainer.is(":visible")) {
                    self.setRequired(false);
                } else {
                    self.setRequired(initial.required);
                }
                return self;
            };

            self.isTrue = function () {
                var value = $fieldset.find(`input:radio[data-flex='${name}']:checked`).val();
                return ["y", "yes", "1", "t", "true"].includes(value);
            };
            self.isChecked = function () {
                if ((inputType === "radio") || (inputType === "checkbox")) {
                    return $input.is(":checked");
                }
            };
            self.hasValue = function () {
                var inputType = $input.attr('type')
                if ((inputType === "radio") || (inputType === "checkbox")) {
                    return $input.is(":checked");
                } else {
                    return $input.val().trim() !== '';
                }
            };
            self.isValid = function () {
                if ($input.data('validation')) {
                    var code = $input.data('validation');
                    var ret = true;
                    try {
                        (function () {
                            return eval(code);
                        }.call(self.origin));
                        ret = !module.getError(self.name);
                        return ret;
                    } catch (e) {
                        return false;
                    }
                }
                if ($input.data('validator')) {
                    try {
                        var f = $input.data('validator');
                        return f(self.origin);
                        // (function () {
                        //     return eval(code);
                        // }.call(self.origin));
                        // ret = !module.getError(self.name);
                        // return ret;
                    } catch (e) {
                        return false;
                    }
                }
            };
            self.setError = function (text) {
                if (text) {
                    $fieldset.data("error", text);
                    $fieldset.find(".errors").html(`<ul class="errorlist"><li>${text}</li></ul>`);
                    module.pushError(self.name);
                } else {
                    $fieldset.data("error", "");
                    $fieldset.find(".errors").html("");
                    module.popError(self.name);
                }
                return self;
            }
            self.assertBetween = function (min, max) {

            };
            self.assertDateBetween = function (min, max) {
                var limit1 = Date.parse(min);
                var limit2 = Date.parse(max);
                var dt = Date.parse(self.getValue());
                if (!(dt < limit1 && dt > limit2)) {
                    self.setError('the date cannot be before 1 dec 1930 or after 1 dec 2007');
                } else {
                    self.setError('');
                }
            };

            self.sameAs = function (target) {
                const $target = self.sibling(target);
                if ($target.getValue() == self.getValue()) {
                    $input.css("background-color", "#d7f6ca");
                } else {
                    $input.css("background-color", "#e1adad");
                }
            }
            self.setValue = function (value) {
                $input.val(value);
                $input.trigger("change");
                return self;
            };
            self.getValue = function () {
                var raw = $input.val();
                if (NUMBERS.indexOf(inputType) >= 0) {
                    return parseInt(raw);
                }
                return raw;
            };
            self.setDescription = function (value) {
                $fieldset.find('.description').text(value);
                return self;
            };
            self.setHint = function (value) {
                $fieldset.find('.hint').text(value);
                return self;
            };
            self.sibling = function (name) {
                var $target = $formContainer.find(`:input[data-flex=${name}]`);
                if (!$target[0]) {
                    alert(`Cannot find "input[name=${name}]"`)
                }
                return new aurora.Field($target);
            };
            self.formsets = function (name) {
                var $target = $formContainer.find(`input[data-flex=${name}]`);
                if (!$target[0]) {
                    alert(`Cannot find "input[name=${name}]"`)
                }
                return new aurora.Field($target);
            };

            self.setRequiredOnValue = function (value, targets) {
                try {
                    const cmp = value.toString().toLowerCase();
                    const val = self.getValue();
                    $form.find(targets).each(function (i, e) {
                        var $c = $(e).parents(".field-container");
                        if (val == cmp) {
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
            };
            self.inspect = function () {
                console.log(`${id}: `, {
                    value: self.getValue(),
                    id: id,
                    me: $me,
                    form: $form,
                    fieldset: $fieldset,
                    input: $input,
                })
            };
        }
    };
    $(function () {
        if (!window.module) {
            window.module = new aurora.Module({});
        }
        $('[data-onload]').each(function () {
            eval($(this).data('onload'));
        });
    });
})(jQuery || django.jQuery);
