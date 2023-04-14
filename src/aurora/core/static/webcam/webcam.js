;(function ($) {
    $(function () {
        const cameraId = "camera";
        var Session = function (fieldName) {
            var self = this;
            self.fieldName = fieldName;
            self.$container = $("#div_" + fieldName);
            self.canvas = $("#div_" + fieldName + " canvas")[0];
            self.context = self.canvas.getContext("2d");
            self.$image = $("#div_" + fieldName + " canvas img");
            self.$field = $("#id_" + fieldName);
            var btnSnap = self.$container.find("button.show-camera")
            var btnCancel = self.$container.find("button.clear-camera")
            btnSnap.data("session", self);
            btnCancel.data("session", self);
        };
        $("<div class='flex justify-center items-center' id='" + cameraId + "'>" +
            "<div class='w-full md:w-1/3 bg-white rounded shadow border p-6 flex items-center flex-col'>" +
            "<video>" + gettext("Video stream not available.") + " </video>" +
            "<div class='w-full flex justify-between align-center'>" +
            "<button type='button' class='snap bg-white hover:bg-gray-100 text-gray-800 font-semibold my-2 mx-2 py-2 px-4 border border-gray-400 rounded shadow'>" +
            gettext("Take photo") + " </button>" +
            "<button type='button' class='cancel bg-white hover:bg-gray-100 text-gray-800 font-semibold my-2 mx-2 py-2 px-4 border border-gray-400 rounded shadow'>" +
            gettext("Cancel") + "</button>" +
            "</div></div></div>").appendTo("body");

        var activeSession = null;
        var streaming = false;
        var width = 460;    // We will scale the photo width to this
        var height = 0;     // This will be computed based on the input stream
        var video = $("#" + cameraId).find("video")[0];

        window.initWebCamField = function (f) {
            var fieldName = $(f).attr("name");

            var sess = $(f).data("session") || new Session(fieldName);
            var currentValue = sess.$field.val();

            if (currentValue) {
                let img = new Image();
                img.addEventListener("load", function () {
                    sess.context.clearRect(0, 0, sess.canvas.width, sess.canvas.height);
                    sess.canvas.width = img.width;
                    sess.canvas.height = img.height;
                    sess.context.drawImage(img, 0, 0, img.width, img.height);
                });
                img.setAttribute("src", currentValue);
            }
        };
        $(".WebcamWidget").each(function () {
            initWebCamField(this);
        });

        $("div.field-container").on("click", ".show-camera", function () {
            var win = $(window);
            // session = new Session($(this).parents('.field-container').find('input').attr("name"));
            activeSession = $(this).data("session");
            $("#camera").css("display", "flex");
            startup();
        });
        $("div.field-container").on("click", ".clear-camera", function () {
            activeSession = $(this).data("session");
            activeSession.context.fillStyle = "#AAA";
            activeSession.context.fillRect(0, 0, activeSession.canvas.width, activeSession.canvas.height);

            var data = activeSession.canvas.toDataURL("image/png");
            activeSession.$image.prop("src", data);
            activeSession.$field.val("");
        });

        function cancel() {
            video.pause();
            $("#camera").hide();
        };

        function takepicture() {
            if (width && height) {
                activeSession.canvas.width = width / 2;
                activeSession.canvas.height = height / 2;
                activeSession.context.drawImage(video, 0, 0, width / 2, height / 2);

                var data = activeSession.canvas.toDataURL("image/png");
                activeSession.$image.prop("src", data);
                activeSession.$field.val(data);
                activeSession = null;
                $("#camera").hide();
            } else {
                clearphoto();
                $("#camera").data("target", null).hide();
            }
        }

        $("#camera button.snap").on("click", function () {
            takepicture();
        });
        $("#camera button.cancel").on("click", function () {
            cancel();
        });

        function startup() {
            // snapshot = document.getElementById("snapshot");
            navigator.mediaDevices.enumerateDevices()
                     .then(function (devices) {
                         var totalCameras = 0;
                         devices.forEach(function(device) {
                             if (device.kind === "videoinput"){
                                 totalCameras++
                             }
                         });
                         navigator.mediaDevices.getUserMedia({
                             video: {
                                 width: 800,
                                 height: 600,
                                 facingMode: 'environment'
                             },
                             audio: false
                         })
                                  .then(function (stream) {
                                      video.srcObject = stream;
                                      video.play();
                                  })
                                  .catch(function (err) {
                                      console.log("An error occurred: " + err);
                                  });
                     });
        }

        video.addEventListener("canplay", function (ev) {
            if (!streaming) {
                height = video.videoHeight / (video.videoWidth / width);
                if (isNaN(height)) {
                    height = width / (4 / 3);
                }
                video.setAttribute("width", width);
                video.setAttribute("height", height);
                streaming = true;
            }
        }, false);
    });
})(jQuery || django.jQuery);
