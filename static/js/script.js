document.addEventListener("DOMContentLoaded", () => {

    /* ---------------------------------------------------------
       Mobile nav toggle
    --------------------------------------------------------- */
    const navToggle = document.getElementById("navToggle");
    const navMenu = document.getElementById("navMenu");

    if (navToggle && navMenu) {
        navToggle.addEventListener("click", () => {
            const isOpen = navMenu.classList.toggle("open");
            navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });
    }

    /* ---------------------------------------------------------
       Loading modal
    --------------------------------------------------------- */
    const modal = document.getElementById("loadingModal");
    const modalTitle = document.getElementById("modalTitle");
    const modalStep = document.getElementById("modalStep");

    const SCAN_STEPS = [
        "Checking website connectivity…",
        "Verifying HTTPS & SSL certificate…",
        "Analyzing trust factors…",
        "Running AI phishing model…",
        "Compiling your report…"
    ];

    const VERIFY_STEPS = [
        "Searching trusted news sources…",
        "Fetching candidate articles…",
        "Extracting article content…",
        "Comparing against your claim…",
        "Asking the AI for a verdict…"
    ];

    let stepInterval = null;

    function showModal(title, steps) {
        if (!modal) return;
        modalTitle.textContent = title;
        let i = 0;
        modalStep.textContent = steps[0];
        modal.hidden = false;

        stepInterval = setInterval(() => {
            i = (i + 1) % steps.length;
            modalStep.textContent = steps[i];
        }, 1800);
    }

    // Safety net: if the browser somehow doesn't navigate away (e.g. the
    // request errors out client-side before a response is received), don't
    // leave the user staring at a spinner forever.
    window.addEventListener("pageshow", () => {
        if (modal) modal.hidden = true;
        if (stepInterval) clearInterval(stepInterval);
    });

    /* ---------------------------------------------------------
       URL scan form: validate + show modal
    --------------------------------------------------------- */
    const scanForm = document.querySelector('form[action="/scan"]');
    if (scanForm) {
        scanForm.addEventListener("submit", (event) => {
            const urlInput = scanForm.querySelector('input[name="url"]');
            const url = urlInput ? urlInput.value.trim() : "";
            // Accepts "example.com", "www.example.com", "sub.example.co.uk",
            // with or without a scheme/path - a plain domain is all that's
            // required, matching what the backend accepts.
            const urlPattern = /^(https?:\/\/)?([\w-]+\.)+[a-zA-Z]{2,}(:\d+)?(\/[^\s]*)?$/;

            if (!urlPattern.test(url)) {
                alert("Please enter a valid website, e.g. example.com");
                event.preventDefault();
                return;
            }

            const button = scanForm.querySelector("button[type='submit']");
            if (button) {
                button.disabled = true;
                button.innerText = "Scanning…";
            }

            showModal("Scanning your URL", SCAN_STEPS);
        });
    }

    /* ---------------------------------------------------------
       Claim verification form: show modal
    --------------------------------------------------------- */
    const verifyForm = document.querySelector('form[action="/verify"]');
    if (verifyForm) {
        verifyForm.addEventListener("submit", (event) => {
            const claimInput = verifyForm.querySelector('textarea[name="claim"]');
            const claim = claimInput ? claimInput.value.trim() : "";

            if (!claim) {
                event.preventDefault();
                return;
            }

            const button = verifyForm.querySelector("button[type='submit']");
            if (button) {
                button.disabled = true;
                button.innerText = "Verifying…";
            }

            showModal("Verifying your claim", VERIFY_STEPS);
        });
    }
});