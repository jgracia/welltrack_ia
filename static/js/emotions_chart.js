const fetchData = async () => {
  try {
    const response = await fetch('/api/get_chart_data/');
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

const setupChart = async () => {
  let data = await fetchData();
  //console.log(data);

  var ctx = document.getElementById("emotionChart");

  var emotionChart = new Chart(ctx, {
    type: "line",
    data: data,
    options: {
      //responsive: true,
      plugins: {
        title: {
          display: true,
          text: "Gráfico de emociones del presente año",
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
              text: 'Meses del año'  // Etiqueta del eje X
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
setupChart();
