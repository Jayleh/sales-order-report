function updateClick(object) {
    // Disable button
    object.classList.add('disabled');

    // Alert with a toast
    M.toast({ html: 'This may be a minute' })
}

let $bomUpdateBtn = document.querySelector('#bom-update-btn');

$bomUpdateBtn.addEventListener("click", function () {
    // Generate toasts
    updateClick($bomUpdateBtn);
});

document.addEventListener('DOMContentLoaded', function () {
    // Enable floating action button
    let $actionBtn = document.querySelectorAll('.fixed-action-btn');
    M.FloatingActionButton.init($actionBtn);

    // Enable tooltips
    let $toolTip = document.querySelectorAll('.tooltipped');
    M.Tooltip.init($toolTip);
});
