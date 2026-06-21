document.addEventListener("DOMContentLoaded", () => {

    const numbers =
        document.querySelectorAll(".card h2");

    numbers.forEach(counter => {

        const target =
            Number(counter.innerText);

        let count = 0;

        const speed = target / 50;

        const updateCounter = () => {

            count += speed;

            if(count < target){

                counter.innerText =
                    Math.floor(count);

                requestAnimationFrame(
                    updateCounter
                );

            }else{

                counter.innerText = target;
            }
        };

        updateCounter();
    });

});