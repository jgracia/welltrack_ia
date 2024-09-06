// Función para obtener el token CSRF de las cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}


// Renderiza Formulario Modal (llamada en el template)
const popupModalElement = document.getElementById('popup');
let popupModal;

function loadModalContent(url) {
  return fetch(url, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.text();
  });
}

function openModal(url) {
  loadModalContent(url)
  .then(modalContent => {
    popupModalElement.innerHTML = modalContent;
    popupModal = new mdb.Modal(popupModalElement, {
      backdrop: 'static',
      keyboard: false
    });
    popupModal.show();

    // Ejecutar scripts manualmente
    const scripts = document.getElementById('popup').getElementsByTagName('script');
    for (let i = 0; i < scripts.length; i++) {
      eval(scripts[i].innerText); // Ejecutar el contenido del script
    }
    
  })
  .catch(error => {
    console.error('Error loading modal content:', error);
  });

  return false;
}

function closeModal() {
  if (popupModal) {
    popupModal.hide();
  }
  return false;
}

// Hacer que las funciones estén disponibles globalmente
window.openModal = openModal;
window.closeModal = closeModal;


