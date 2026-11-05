document.addEventListener("DOMContentLoaded", () => {
    const examForm = document.querySelector("[data-exam-form]");
    const timer = document.querySelector("[data-timer]");
    const menuButton = document.querySelector("[data-menu-button]");
    const navigation = document.querySelector(".site-nav");

    if (menuButton && navigation) {
        menuButton.addEventListener("click", () => {
            navigation.classList.toggle("is-open");
            menuButton.setAttribute("aria-expanded", navigation.classList.contains("is-open"));
        });
    }

    if (!examForm || !timer) {
        return;
    }

    let remaining = Number(timer.dataset.seconds);
    let submitted = false;

    const submitExam = () => {
        if (!submitted) {
            submitted = true;
            examForm.submit();
        }
    };

    const updateTimer = () => {
        const minutes = Math.floor(remaining / 60).toString().padStart(2, "0");
        const seconds = (remaining % 60).toString().padStart(2, "0");
        timer.textContent = `${minutes}:${seconds}`;
        timer.classList.toggle("is-warning", remaining <= 60);
        if (remaining <= 0) {
            submitExam();
            return;
        }
        remaining -= 1;
        window.setTimeout(updateTimer, 1000);
    };

    examForm.addEventListener("submit", (event) => {
        if (submitted) {
            return;
        }
        if (!window.confirm("Submit your exam now?")) {
            event.preventDefault();
        } else {
            submitted = true;
        }
    });

    updateTimer();
});
