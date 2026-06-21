document.addEventListener("DOMContentLoaded", () => {

    const form = document.querySelector("form");

    if(!form) return;

    form.addEventListener("submit", function(event){

        const urlInput =
            document.querySelector('input[name="url"]');

        const url = urlInput.value.trim();

        const regex =
        /^(https?:\/\/)?([\w\-])+\.{1}[a-zA-Z]{2,}(\/.*)?$/;

        if(!regex.test(url)){

            alert(
                "Please enter a valid URL."
            );

            event.preventDefault();
        }
    });

});