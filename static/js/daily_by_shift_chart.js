const fetchDailyData = async () => {
  try {
    const response = await fetch('/api/get_daily_chart_data/');
    if (!response.ok) {
      throw new Error('Error en la solicitud');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error:', error);
    return null;  // O puedes manejar el error de otra manera
  }
};

const setupDailyChart = async () => {
  let dataDaily = await fetchDailyData();
  //console.log(data);

  var ctxDaily = document.getElementById("emotionChartByDay");

  var emotionDaiyChart = new Chart(ctxDaily, {
    type: "bar",
    data: {
        labels: dataDaily.labels,  // Áreas en el eje horizontal
        datasets: dataDaily.datasets  // Datos de emociones para las horas
    },
    options: {
      //responsive: true,
      plugins: {
        title: {
          display: true,
          text: "Gráfico de videos diarios por turno",
          font: { size: 14 }
        },
        datalabels: {
          anchor: 'end',
          align: 'end',
          formatter: (value) => value,
          color: 'black',
          font: { weight: 'bold' }
        }
      },
      /*layout: {
          padding: {
              top: 40,  // Ajusta este valor según sea necesario
          }
      },*/
      scales: {
        x: {
            title: {
              display: true,
              text: 'Turno de Trabajo - Hora'  // Etiqueta del eje X
            }
        },
        y: {
            title: {
              display: true,
              text: 'Videos Totales'  // Etiqueta del eje Y
            },
            ticks: {
              padding: 2  // Ajusta este valor según sea necesario
            },
            afterDataLimits: (axis) => {
              axis.max += 2;  // Ajusta este valor según sea necesario para dejar espacio en la parte superior
            }
        }
      }
    },
    plugins: [ChartDataLabels]
  });
};

// Llamar a la función asíncrona
setupDailyChart();
