// Graph
var ctx = document.getElementById("emotionChart");

var emotionChart = new Chart(ctx, {
  type: "line",
  data: {
    labels: [
      "Entusiasmo",
      "Felicidad",
      "Relajación",
      "Sorpresa",
      "Pasividad",
      "Ansiedad",
      "Aurrimiento",
    ],
    datasets: [
      {
        data: [10, 25, 30, 25, 75, 6, 15],
        lineTension: 0,
        backgroundColor: "transparent",
        borderColor: "#007bff",
        borderWidth: 4,
        pointBackgroundColor: "#007bff",
      },
    ],
  },
  options: {
    scales: {
      yAxes: [
        {
          ticks: {
            beginAtZero: false,
          },
        },
      ],
    },
    legend: {
      display: false,
    },
  },
});
