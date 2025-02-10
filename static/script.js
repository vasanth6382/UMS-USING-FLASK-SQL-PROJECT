document.addEventListener("DOMContentLoaded", function() {
    const inputs = document.querySelectorAll("input");

    inputs.forEach(function(input) {
        // On focus, hide placeholder
        input.addEventListener("focus", function() {
            input.placeholder = "";
            input.style.outline = "none"; 
        });

        // On blur, show placeholder if the input is empty
        input.addEventListener("blur", function() {
            if (input.value === "") {
                input.placeholder = input.getAttribute("data-placeholder");
            }
        });

        // Set the initial placeholder text using a custom attribute
        input.setAttribute("data-placeholder", input.placeholder);
    });
});
