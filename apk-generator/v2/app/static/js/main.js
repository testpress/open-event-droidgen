var $generateBtn = $("#generate-btn"),
    $emailInput = $("#email"),
    $jsonUploadInput = $("#json-upload"),
    $googleServicesJsonUploadInput = $("#google-services-json"),
    $apiEndpointInput = $("#api-endpoint"),
    $jsonUploadInputHolder = $("#json-upload-holder"),
    $apiEndpointInputHolder = $("#api-endpoint-holder"),
    $downloadBtn = $("#download-btn"),
    $form = $("#form"),
    $actionBtnGroup = $("#action-btn-group"),
    $dataSourceRadio = $("input:radio[name=data-source]"),
    dataSourceType = null,
    $buildTypeRadio = $("input:radio[name=build-type]"),
    buildType = null,
    $authOptionCheckbox = $("input:checkbox[name=is-auth-enabled]"),
    $colorPrimary = $("#cp-primary"),
    $colorPrimaryDark = $("#cp-primary-dark"),
    $colorAccent = $("#cp-accent"),
    $deploymentLink = $("#deploy-link");

var $fileProgressHolder = $("#file-progress"),
    $fileProgressBar = $("#file-progress-bar"),
    $fileProgressVal = $("#file-progress-val");

var $statusMessageHolder = $("#status-message-holder"),
    $statusMessage = $("#status-message");

var $errorMessageHolder = $("#error-message-holder"),
    $errorMessage = $("#error-message");

var identifier = null,
    taskId = null,
    pollingWorker = null,
    downloadUrl = null;

var menuDisplay = false;

$(".custom-menubutton").click(function() {
    var menuContent = $(".custom-menu-cont")[0];

    if (menuDisplay) {
        $(menuContent).removeClass("shown");
        $(menuContent).addClass("hidden");
    } else {
        $(menuContent).removeClass("hidden");
        $(menuContent).addClass("shown");
    }
    menuDisplay = !menuDisplay;
});

/**
 * Enable the generate button
 *
 * @param enabled
 */
function enableGenerateButton(enabled) {
    $errorMessageHolder.hide();
    $statusMessageHolder.hide();
    $generateBtn.prop("disabled", !enabled);
    $downloadBtn.disable();
}

$dataSourceRadio.change(
    function () {
        enableGenerateButton(false);
        $apiEndpointInput.val("");
        if (this.checked) {
            dataSourceType = $(this).val();
            if (dataSourceType === "json_upload") {
                $jsonUploadInputHolder.show();
                $apiEndpointInputHolder.hide();
            }
            if (dataSourceType === "api_endpoint") {
                $apiEndpointInputHolder.show();
                $jsonUploadInputHolder.hide();
            }
        }
    }
);

$buildTypeRadio.change(
    function () {
        if (this.checked) {
            enableGenerateButton(true);
            buildType = $(this).val();
        }
    }
);

$apiEndpointInput.valueChange(function (value) {
    if (dataSourceType === "api_endpoint") {
        if (buildType !== null && value.trim() !== "" && isLink(value.trim())) {
            enableGenerateButton(true);
        } else {
            enableGenerateButton(false);
        }
    }
});

$jsonUploadInput.change(function () {
    if (dataSourceType === "json_upload") {
        $fileProgressBar.css("width", 0);
        if (buildType !== null && this.value !== "") {
            enableGenerateButton(true);
        } else {
            enableGenerateButton(false);
        }
    }
});

/**
 * Set the form to the initial state
 */
function initialState() {
    $dataSourceRadio.prop("checked", false);
    $generateBtn.disable();
    $downloadBtn.disable();
    $actionBtnGroup.show();
    $colorPrimary.colorpicker();
    $colorPrimaryDark.colorpicker();
    $colorAccent.colorpicker();
}
initialState();

/**
 * Update the file upload progress bar
 * @param progress
 */
function updateProgress(progress) {
    $fileProgressHolder.show();
    var percentCompleted = Math.round((progress.loaded * 100) / progress.total);
    $fileProgressBar.css("width", percentCompleted + "%");
    $fileProgressVal.text(percentCompleted + "%");
}

/**
 * Hide the file upload progress bar
 */
function hideProgress() {
    updateProgress({loaded: 0, total: 100});
    $fileProgressHolder.hide();
}

/**
 * Enable the download button
 */
function enableDownloadButton() {
    hideProgress();
    $form.unlockFormInputs();
    $errorMessageHolder.hide();
    $statusMessageHolder.hide();
    $actionBtnGroup.show();
    $generateBtn.enable();
    $downloadBtn.enable();
}

/**
 * Update the status message
 *
 * @param status
 */
function updateStatus(status) {
    $actionBtnGroup.hide();
    $errorMessageHolder.hide();
    $statusMessageHolder.show();
    if (status) {
        $statusMessage.text(status);
    } else {
        $statusMessage.text($statusMessage.data("original"));
    }
}

function deployStatus() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            var version = JSON.parse(this.responseText).object.sha;
            var versionLink = "https://github.com/testpress/android/tree/" + version;
            $("#deploy-link").attr("href", versionLink);
            $("#deploy-link").html(version);
        }
    };
    xhttp.open("GET", "https://api.github.com/repos/testpress/android/git/refs/heads/master", true);
    xhttp.send();
}

deployStatus();

/**
 * Show an error message
 *
 * @param error
 */
function showError(error) {
    $form.unlockFormInputs();
    $statusMessageHolder.hide();
    $actionBtnGroup.show();
    $errorMessageHolder.show();
    hideProgress();
    if (error) {
        $errorMessage.text(error);
    } else {
        $errorMessage.text($errorMessage.data("original"));
    }
}

/**
 * Start the app download when the download button is clicked
 */
$downloadBtn.click(function () {
    if (window.location) {
        window.location = downloadUrl;
    } else {
        $(this).disable();
    }
});

/**
 * Start the continuous poll for getting status updates
 */
function startPoll() {
    pollingWorker = setInterval(function () {
        axios
            .get("/api/v2/app/" + taskId + "/status")
            .then(function (res) {
                res = res.data;
                switch (res.state) {
                    case "FAILURE":
                        showError();
                        clearInterval(pollingWorker);
                        break;
                    case "SUCCESS":
                        if (res.hasOwnProperty("result")) {
                            downloadUrl = res.result.hasOwnProperty("message") ? res.result.message : res.result;
                            enableDownloadButton();
                        } else {
                            showError();
                        }
                        clearInterval(pollingWorker);
                        break;
                    default:
                        updateStatus(res.state);
                }
            })
            .catch(function (err) {

            });
    }, 1000);
}

/**
 * Submit the data to the backend via AJAX when the form is submitted
 */
$form.submit(function (e) {
    e.preventDefault();
    downloadUrl = null;
    $form.lockFormInputs();
    var data = new FormData();
    data.append("email", $emailInput.val());
    data.append("data-source", dataSourceType);
    data.append("build-type", buildType);
    data.append("is-auth-enabled", $authOptionCheckbox.is(":checked"));
    data.append("colors", JSON.stringify({
        'primary': $colorPrimary.colorpicker('getValue'),
        'primary_dark': $colorPrimaryDark.colorpicker('getValue'),
        'accent': $colorAccent.colorpicker('getValue')
    }));

    var config = {};

    if (dataSourceType === "json_upload") {
        data.append("json-upload", $jsonUploadInput[0].files[0]);
        data.append("google-services-json", $googleServicesJsonUploadInput[0].files[0]);
        config.onUploadProgress = updateProgress;
    } else {
        data.append("api-endpoint", $apiEndpointInput.val());
    }

    updateStatus();
    axios
        .post("/", data, config)
        .then(function (res) {
            hideProgress();
            identifier = res.data.identifier;
            taskId = res.data.task_id;
            updateStatus("Waiting in line :)");
            if (taskId && taskId.trim() !== "") {
                startPoll();
            }
        })
        .catch(function () {
            showError();
        });
});