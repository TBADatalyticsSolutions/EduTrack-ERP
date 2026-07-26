document.addEventListener("DOMContentLoaded", function () {

    const canvas = document.getElementById("studentChart");

    if (!canvas) return;

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun"
            ],
            datasets: [{
                label: "Student Admissions",
                data: [15, 20, 18, 25, 22, 30]
            }]
        }
    });

});