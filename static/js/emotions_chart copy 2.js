/*const labels = Utils.months({count: 7});*/
const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December'
];
const labels = MONTHS

// Graph
var ctx = document.getElementById("emotionChart");

var emotionChart = new Chart(ctx, {
  type: "line",
  data: {
    labels: labels,
    /*labels: [
      "Entusiasmo",
      "Felicidad",
      "Relajación",
      "Sorpresa",
      "Pasividad",
      "Ansiedad",
      "Aurrimiento",
    ],*/
    datasets: [
      {
        label: 'Triste',
        data: [65, 59, 80, 81, 56, 55, 40],
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        /*borderColor: "#007bff",*/
        tension: 0.1
      },
      {
        label: 'Miedo',
        data: [10, 25, 30, 25, 75, 6, 15],
        fill: false,
        /*borderColor: 'rgb(75, 192, 192)',*/
        borderColor: "#007bff",
        tension: 0.1
      },
      {
        label: 'Enojado',
        data: [2, 5, 40, 15, 40, 25, 30],
        fill: false,
        /*borderColor: 'rgb(75, 192, 192)',*/
        borderColor: "#FF8300",
        tension: 0.1
      },
    ],
  },
});
