document.addEventListener("DOMContentLoaded", function () {

    // Student Chart

    const studentCanvas = document.getElementById("studentChart");

    if (studentCanvas) {

        new Chart(studentCanvas, {

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

                    label: "Students",

                    data: [5, 8, 12, 15, 18, 25]

                }]

            }

        });

    }

    // Revenue Chart

    const revenueCanvas = document.getElementById("revenueChart");

    if (revenueCanvas) {

        new Chart(revenueCanvas, {

            type: "line",

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

                    label: "Revenue",

                    data: [0, 200000, 500000, 750000, 900000, 1250000]

                }]

            }

        });

    }

});