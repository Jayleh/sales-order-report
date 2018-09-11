function dimPage() {
    // Dim page contents and display preloader
    let $main = document.querySelectorAll('.container'),
        $preloader = document.querySelector('#preloader-container');

    $main.forEach(function (element) {
        element.setAttribute("style", "opacity: 0.2;")
    });

    $preloader.setAttribute("style", "display: unset;")
}

function disableButtons(buttonList) {
    // Disable all buttons
    buttonList.forEach(function (element) {
        element.classList.add('disabled');
    });
}

document.addEventListener('DOMContentLoaded', function () {
    // Enable floating action button
    let $actionBtn = document.querySelectorAll('.fixed-action-btn');
    M.FloatingActionButton.init($actionBtn);

    // Enable tooltips
    let $toolTip = document.querySelectorAll('.tooltipped');
    M.Tooltip.init($toolTip);

    // Enable modal
    let $modal = document.querySelectorAll('.modal');
    M.Modal.init($modal);

    // Click event on flash message
    let $flashBtn = document.querySelector('#flash-close');

    if ($flashBtn) {
        $flashBtn.addEventListener("click", function () {
            let $flashToast = document.querySelector('#flash-toast');
            $flashToast.parentNode.removeChild($flashToast);
        });
    }

    // List all buttons
    let $browseBtn = document.querySelector('#browse-btn'),
        $submitBtn = document.querySelector('#submit-btn'),
        $bomUpdateBtn = document.querySelector('#bom-update-btn'),
        $sohUpdateBtn = document.querySelector('#soh-update-btn'),
        $deleteBtn = document.querySelector('#delete-reports-btn'),
        buttonList = [$browseBtn, $submitBtn, $bomUpdateBtn, $sohUpdateBtn, $deleteBtn];

    // Disable button if there are no reports
    let $reports = document.querySelectorAll('.report');

    if ($reports.length === 0) {
        $deleteBtn.classList.add('disabled');
    }

    // Disable submit button if no file selected
    let $filePath = document.querySelector('.file-path');

    $filePath.addEventListener('change', function () {
        if ($filePath.value !== "") {
            $submitBtn.classList.remove('disabled');
        }
        else {
            $submitBtn.classList.add('disabled');
        }
    });

    // Click event on Submit button
    $submitBtn.addEventListener("click", function () {
        // Dimmer
        dimPage();

        // Disable all buttons
        disableButtons(buttonList);
    });

    // Click event on bom update button
    $bomUpdateBtn.addEventListener("click", function () {
        // Alert with a toast
        M.toast({ html: 'This may be a minute' })

        // Dimmer
        dimPage();

        // Disable all buttons
        disableButtons(buttonList);
    });

    // Click event on soh update button
    $sohUpdateBtn.addEventListener("click", function () {
        // Alert with a toast
        M.toast({ html: 'This may be a minute' })

        // Dimmer
        dimPage();

        // Disable all buttons
        disableButtons(buttonList);
    });
});
