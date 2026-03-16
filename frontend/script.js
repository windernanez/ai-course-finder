// Configuración - URL de tu backend en Railway
const API_URL = 'https://ai-course-finder.up.railway.app/api';

// Elementos del DOM
const lenguajeSelect = document.getElementById('lenguaje');
const nivelCards = document.querySelectorAll('.nivel-card');
const buscarBtn = document.getElementById('buscarBtn');
const loadingDiv = document.getElementById('loading');
const resultadosDiv = document.getElementById('resultados');
const videosContainer = document.getElementById('videos-container');
const canalesContainer = document.getElementById('canales-container');
const resultadosTitulo = document.getElementById('resultados-titulo');
const resultadosMensaje = document.getElementById('resultados-mensaje');
const canalesSection = document.getElementById('canales-recomendados');
const statsContainer = document.getElementById('stats-container');

// Elementos del Chat
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');
const sugerenciaBtns = document.querySelectorAll('.sugerencia-btn');
const recomendacionChat = document.getElementById('recomendacion-chat');
const recomendacionTexto = document.getElementById('recomendacion-texto');

// Estado
let nivelSeleccionado = 'principiante';
let lenguajeSeleccionado = '';

// Inicialización
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔄 Inicializando aplicación...');
    await cargarLenguajes();
    await cargarEstadisticas();
    configurarEventListeners();
});

// Cargar lenguajes desde la API
async function cargarLenguajes() {
    try {
        console.log('📡 Cargando lenguajes...');
        const response = await fetch(`${API_URL}/lenguajes`);
        const data = await response.json();
        
        const listaLenguajes = data.lenguajes || [];
        
        lenguajeSelect.innerHTML = '<option value="">Selecciona un lenguaje...</option>';
        listaLenguajes.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang;
            option.textContent = lang.toUpperCase();
            lenguajeSelect.appendChild(option);
        });
        console.log('✅ Lenguajes cargados:', listaLenguajes);
        
    } catch (error) {
        console.error('❌ Error cargando lenguajes:', error);
        lenguajeSelect.innerHTML = '<option value="">Error al cargar</option>';
    }
}

// Configurar event listeners
function configurarEventListeners() {
    nivelCards.forEach(card => {
        card.addEventListener('click', () => {
            const radio = card.querySelector('input');
            radio.checked = true;
            nivelSeleccionado = radio.value;
            nivelCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
        });
    });

    buscarBtn.addEventListener('click', buscarCursos);
    chatSend.addEventListener('click', enviarMensajeChat);
    
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') enviarMensajeChat();
    });
}

// Buscar cursos mediante POST
async function buscarCursos() {
    lenguajeSeleccionado = lenguajeSelect.value;
    if (!lenguajeSeleccionado) {
        alert('Por favor selecciona un lenguaje');
        return;
    }

    loadingDiv.style.display = 'block';
    resultadosDiv.style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/buscar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lenguaje: lenguajeSeleccionado,
                nivel: nivelSeleccionado
            })
        });

        const data = await response.json();
        console.log("📡 Respuesta del servidor:", data);
        
        // CORRECCIÓN PARA IMAGEN 11: Manejar si la API devuelve un Array directo o un objeto con .videos
        if (Array.isArray(data) && data.length > 0) {
            mostrarResultados({ videos: data });
            agregarMensajeChat(`He encontrado ${data.length} cursos de ${lenguajeSeleccionado.toUpperCase()}.`, 'bot');
        } else if (data.videos && data.videos.length > 0) {
            mostrarResultados(data);
            agregarMensajeChat(`He encontrado videos de ${lenguajeSeleccionado.toUpperCase()}. ¡A estudiar! 🚀`, 'bot');
        } else {
            mostrarError('No se encontraron resultados adecuados. Intenta con otro nivel.');
        }
    } catch (error) {
        console.error('❌ Error:', error);
        mostrarError('Error de conexión con Railway');
    } finally {
        loadingDiv.style.display = 'none';
    }
}

// Chat con Gemini
async function enviarMensajeChat() {
    const mensaje = chatInput.value.trim();
    if (!mensaje) return;
    
    agregarMensajeChat(mensaje, 'user');
    chatInput.value = '';
    
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje: mensaje })
        });
        const data = await response.json();
        agregarMensajeChat(data.respuesta || 'No pude procesar tu mensaje.', 'bot');
    } catch (error) {
        agregarMensajeChat('Error de conexión.', 'bot');
    }
}

function agregarMensajeChat(texto, tipo) {
    const div = document.createElement('div');
    div.className = `message ${tipo}`;
    div.innerHTML = `<div class="message-text">${texto}</div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Renderizar videos encontrados
function mostrarResultados(data) {
    resultadosTitulo.textContent = `Cursos de ${lenguajeSeleccionado.toUpperCase()}`;
    videosContainer.innerHTML = '';
    
    data.videos.forEach(video => {
        const card = document.createElement('div');
        card.className = 'video-card';
        card.innerHTML = `
            <img src="${video.miniatura}" alt="${video.titulo}">
            <div class="video-info">
                <h4>${video.titulo}</h4>
                <p><i class="fas fa-user"></i> ${video.canal}</p>
                <div class="video-meta">
                   <span><i class="fas fa-star"></i> Confianza IA: ${video.confianza_nivel}%</span>
                </div>
                <a href="${video.enlace}" target="_blank" class="btn-ver">
                    <i class="fas fa-play"></i> Ver Video
                </a>
            </div>
        `;
        videosContainer.appendChild(card);
    });
    resultadosDiv.style.display = 'block';
}

// Cargar estadísticas
async function cargarEstadisticas() {
    try {
        const response = await fetch(`${API_URL}/estadisticas`);
        const data = await response.json();
        
        statsContainer.innerHTML = `
            <div class="stat-card">
                <h4>${data.cursos_totales}</h4>
                <p>Cursos Disponibles</p>
            </div>
            <div class="stat-card">
                <h4>${data.busquedas_exitosas}</h4>
                <p>Búsquedas</p>
            </div>
        `;
    } catch (error) {
        statsContainer.innerHTML = '<p>Estadísticas no disponibles</p>';
    }
}

function mostrarError(mensaje) {
    resultadosDiv.style.display = 'block';
    resultadosMensaje.textContent = mensaje;
    videosContainer.innerHTML = '';
}
