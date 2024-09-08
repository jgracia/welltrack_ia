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
  });
};

// Llamar a la función asíncrona
setupChart();
