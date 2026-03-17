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

// 1. Cargar lenguajes - CORREGIDO: Ahora recibe el array directo []
async function cargarLenguajes() {
    try {
        console.log('📡 Cargando lenguajes...');
        const response = await fetch(`${API_URL}/lenguajes`);
        const data = await response.json();
        
        // El app.py corregido envía el array directo, no dentro de 'detalles'
        const listaFull = Array.isArray(data) ? data : (data.detalles || []);
        
        lenguajeSelect.innerHTML = '<option value="">Selecciona un lenguaje...</option>';
        listaFull.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang.id;
            option.textContent = `${lang.icono} ${lang.nombre}`;
            lenguajeSelect.appendChild(option);
        });
        console.log('✅ Lenguajes cargados:', listaFull.length);
    } catch (error) {
        console.error('❌ Error cargando lenguajes:', error);
        lenguajeSelect.innerHTML = '<option value="">Error al cargar</option>';
    }
}

// 2. Buscar cursos - CORREGIDO: Sincronizado con el objeto de respuesta del backend
async function buscarCursos() {
    lenguajeSeleccionado = lenguajeSelect.value;
    if (!lenguajeSeleccionado) {
        alert('Por favor selecciona un lenguaje');
        return;
    }

    loadingDiv.style.display = 'block';
    resultadosDiv.style.display = 'none';
    recomendacionChat.style.display = 'none';
    
    try {
        const response = await fetch(`${API_URL}/buscar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lenguaje: lenguajeSeleccionado, nivel: nivelSeleccionado })
        });

        const data = await response.json();
        
        if (data.exito) {
            mostrarResultados(data); // Pasamos todo el objeto data
            
            if (data.recomendacion_chat) {
                recomendacionTexto.textContent = data.recomendacion_chat;
                recomendacionChat.style.display = 'flex';
            }
            agregarMensajeChat(`¡Listo! Encontré contenido de ${lenguajeSeleccionado.toUpperCase()} para ti. 🚀`, 'bot');
        } else {
            mostrarError(data.error || 'No se encontraron resultados.');
        }
    } catch (error) {
        mostrarError('Error de conexión. Verifica que el servidor esté activo.');
    } finally {
        loadingDiv.style.display = 'none';
    }
}

// 3. Cargar Estadísticas - CORREGIDO: Muestra ambos valores del app.py
async function cargarEstadisticas() {
    try {
        const response = await fetch(`${API_URL}/estadisticas`);
        const stats = await response.json();
        
        // Usamos las llaves exactas que definimos en app.py
        const cursos = stats.cursos_totales || 0;
        const busquedas = stats.busquedas_exitosas || 0;
        
        statsContainer.innerHTML = `
            <div class="stat-card">
                <i class="fas fa-graduation-cap"></i>
                <div class="stat-info">
                    <h4>${cursos}</h4>
                    <p>Cursos Disponibles</p>
                </div>
            </div>
            <div class="stat-card">
                <i class="fas fa-search"></i>
                <div class="stat-info">
                    <h4>${busquedas}</h4>
                    <p>Búsquedas</p>
                </div>
            </div>
        `;
    } catch (error) {
        console.warn('No se pudieron cargar las estadísticas');
    }
}

// 4. Mostrar Resultados - CORREGIDO: Usa los nombres del backend corregido
function mostrarResultados(data) {
    const nombreLenguaje = lenguajeSelect.options[lenguajeSelect.selectedIndex].text;
    resultadosTitulo.innerHTML = `<i class="fas fa-code"></i> Cursos de ${nombreLenguaje}`;
    
    videosContainer.innerHTML = '';
    if (!data.videos || data.videos.length === 0) {
        videosContainer.innerHTML = '<p class="no-results">No se encontraron videos adecuados.</p>';
    } else {
        data.videos.forEach(video => {
            videosContainer.appendChild(crearVideoCard(video));
        });
    }
    
    // Sincronizado con 'canales_recomendados' del app.py
    if (data.canales_recomendados && data.canales_recomendados.length > 0) {
        canalesSection.style.display = 'block';
        canalesContainer.innerHTML = '';
        data.canales_recomendados.forEach(canal => {
            canalesContainer.appendChild(crearCanalCard(canal));
        });
    } else {
        canalesSection.style.display = 'none';
    }
    
    resultadosDiv.style.display = 'block';
    cargarEstadisticas(); // Actualizar tras buscar
}

// --- FUNCIONES AUXILIARES (Eventos, Cards, Chat) ---

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
    chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') enviarMensajeChat(); });

    sugerenciaBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.getAttribute('data-msg');
            enviarMensajeChat();
        });
    });
}

async function enviarMensajeChat() {
    const mensaje = chatInput.value.trim();
    if (!mensaje) return;
    
    agregarMensajeChat(mensaje, 'user');
    chatInput.value = '';
    mostrarIndicadorEscritura();
    
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje: mensaje })
        });
        const data = await response.json();
        quitarIndicadorEscritura();
        agregarMensajeChat(data.respuesta || 'Lo siento, tuve un problema al procesar eso.', 'bot');
    } catch (error) {
        quitarIndicadorEscritura();
        agregarMensajeChat('Error de conexión con la IA.', 'bot');
    }
}

function crearVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    const nivel = video.nivel_detectado || 'principiante';
    const nivelIcon = nivel === 'avanzado' ? '🚀' : (nivel === 'intermedio' ? '📚' : '🌱');
    
    card.innerHTML = `
        <div class="video-thumbnail">
            <img src="${video.miniatura}" alt="Miniatura">
            <span class="video-duration">${video.duracion || 'N/A'}</span>
        </div>
        <div class="video-info">
            <h3 class="video-title">${video.titulo}</h3>
            <p class="video-channel"><i class="fas fa-user"></i> ${video.canal}</p>
            <div class="video-meta">
                <span><i class="fas fa-star"></i> IA: ${video.confianza_nivel}%</span>
            </div>
            <div style="margin: 10px 0;">
                <span class="nivel-badge nivel-${nivel}">${nivelIcon} ${nivel}</span>
            </div>
            <div class="video-footer">
                <a href="${video.enlace}" target="_blank" class="btn-ver">Ver en YouTube</a>
            </div>
        </div>
    `;
    return card;
}

function crearCanalCard(canal) {
    const card = document.createElement('div');
    card.className = 'canal-card';
    card.innerHTML = `
        <img src="${canal.miniatura}" alt="${canal.nombre}" onerror="this.src='https://via.placeholder.com/50'">
        <div class="canal-info">
            <h4>${canal.nombre}</h4>
            <p><i class="fas fa-users"></i> Recomendado</p>
        </div>
    `;
    return card;
}

function agregarMensajeChat(texto, tipo) {
    const div = document.createElement('div');
    div.className = `message ${tipo}`;
    const tiempo = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    div.innerHTML = `
        <div class="message-content">
            <i class="fas ${tipo === 'bot' ? 'fa-robot' : 'fa-user'} avatar"></i>
            <div class="message-text">${texto}</div>
        </div>
        <div class="message-time">${tiempo}</div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function mostrarIndicadorEscritura() {
    const div = document.createElement('div');
    div.className = 'message bot typing-indicator';
    div.id = 'typing-indicator';
    div.innerHTML = `<div class="message-content"><i class="fas fa-robot avatar"></i><div class="message-text">Escribiendo...</div></div>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function quitarIndicadorEscritura() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function mostrarError(mensaje) {
    resultadosDiv.style.display = 'block';
    resultadosMensaje.textContent = mensaje;
}
