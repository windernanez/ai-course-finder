// Configuración - Ajustado para la URL de tu backend en Railway
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

// Cargar lenguajes - CORREGIDO para manejar objetos con iconos
async function cargarLenguajes() {
    try {
        console.log('📡 Cargando lenguajes...');
        const response = await fetch(`${API_URL}/lenguajes`);
        const data = await response.json();
        
        // Usamos 'detalles' que es el array de objetos {id, nombre, icono} del app.py
        const listaFull = data.detalles || [];
        
        lenguajeSelect.innerHTML = '<option value="">Selecciona un lenguaje...</option>';
        listaFull.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang.id;
            option.textContent = `${lang.icono} ${lang.nombre}`;
            lenguajeSelect.appendChild(option);
        });
        console.log('✅ Lenguajes cargados correctamente');
    } catch (error) {
        console.error('❌ Error cargando lenguajes:', error);
        lenguajeSelect.innerHTML = '<option value="">Error cargando lenguajes</option>';
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

    sugerenciaBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mensaje = btn.getAttribute('data-msg');
            chatInput.value = mensaje;
            enviarMensajeChat();
        });
    });
}

// Buscar cursos - CORREGIDO: Resiliencia ante diferentes formatos de respuesta
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
        
        // Mantenemos tu lógica de 'exito' pero con fallback por si llega un array directo
        if (data.exito || Array.isArray(data)) {
            const datosFinales = Array.isArray(data) ? { videos: data, exito: true, nivel: nivelSeleccionado, lenguaje: lenguajeSeleccionado } : data;
            mostrarResultados(datosFinales);
            
            if (datosFinales.recomendacion_chat) {
                recomendacionTexto.textContent = datosFinales.recomendacion_chat;
                recomendacionChat.style.display = 'flex';
            }
            agregarMensajeChat(`He encontrado cursos de ${lenguajeSeleccionado.toUpperCase()}. ¡A estudiar! 🚀`, 'bot');
        } else {
            mostrarError(data.error || 'No se encontraron resultados adecuados.');
        }
    } catch (error) {
        mostrarError('Error de conexión con Railway');
    } finally {
        loadingDiv.style.display = 'none';
    }
}

// Funciones del Chat
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
            body: JSON.stringify({ mensaje: mensaje, lenguaje: lenguajeSeleccionado || null })
        });
        const data = await response.json();
        quitarIndicadorEscritura();
        
        // Manejo de respuesta simple o estructurada
        const respuesta = data.respuesta || (data.exito ? data.respuesta : 'Lo siento, hubo un error.');
        agregarMensajeChat(respuesta, 'bot');
    } catch (error) {
        quitarIndicadorEscritura();
        agregarMensajeChat('Error de conexión con el servidor', 'bot');
    }
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
    div.innerHTML = `
        <div class="message-content">
            <i class="fas fa-robot avatar"></i>
            <div class="message-text">Escribiendo<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></div>
        </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function quitarIndicadorEscritura() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function mostrarResultados(data) {
    const nombreLenguaje = lenguajeSelect.options[lenguajeSelect.selectedIndex].text;
    resultadosTitulo.innerHTML = `<i class="fas fa-code"></i> Cursos de ${nombreLenguaje} - Nivel ${data.nivel || nivelSeleccionado}`;
    
    videosContainer.innerHTML = '';
    if (!data.videos || data.videos.length === 0) {
        videosContainer.innerHTML = '<p style="text-align: center; padding: 20px;">No se encontraron videos.</p>';
    } else {
        data.videos.forEach(video => {
            videosContainer.appendChild(crearVideoCard(video));
        });
    }
    
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
    cargarEstadisticas();
}

function crearVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    const nivelClass = `nivel-${video.nivel_detectado || 'principiante'}`;
    const nivelIcon = video.nivel_detectado === 'avanzado' ? '🚀' : (video.nivel_detectado === 'intermedio' ? '📚' : '🌱');
    
    card.innerHTML = `
        <div class="video-thumbnail">
            <img src="${video.miniatura}" alt="${video.titulo}">
            <span class="video-duration">${video.duracion || 'N/A'}</span>
        </div>
        <div class="video-info">
            <h3 class="video-title">${video.titulo}</h3>
            <p class="video-channel"><i class="fas fa-user"></i> ${video.canal}</p>
            <div class="video-meta">
                <span><i class="fas fa-star"></i> IA: ${video.confianza_nivel}%</span>
                <span><i class="fas fa-calendar"></i> ${video.fecha || ''}</span>
            </div>
            <div style="margin-top: 10px;">
                <span class="nivel-badge ${nivelClass}">${nivelIcon} ${video.nivel_detectado}</span>
            </div>
            <div class="video-footer">
                <a href="${video.enlace}" target="_blank" class="btn-ver">Ver Video</a>
            </div>
        </div>
    `;
    return card;
}

function crearCanalCard(canal) {
    const card = document.createElement('div');
    card.className = 'canal-card';
    card.innerHTML = `
        <img src="${canal.miniatura}" alt="${canal.nombre}">
        <div class="canal-info">
            <h4>${canal.nombre}</h4>
            <p><i class="fas fa-users"></i> ${canal.suscriptores || ''}</p>
        </div>
    `;
    return card;
}

async function cargarEstadisticas() {
    try {
        const response = await fetch(`${API_URL}/estadisticas`);
        const stats = await response.json();
        
        // Mapeo flexible para ambos formatos de respuesta (app.py)
        const total = stats.total_busquedas || stats.busquedas_exitosas || 0;
        
        statsContainer.innerHTML = `
            <div class="stat-card">
                <i class="fas fa-search"></i>
                <div class="stat-info">
                    <h4>${total}</h4>
                    <p>Búsquedas realizadas</p>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error stats');
    }
}

function mostrarError(mensaje) {
    resultadosDiv.style.display = 'block';
    resultadosMensaje.textContent = mensaje;
}

// Estilos del indicador de escritura (mantenidos)
const style = document.createElement('style');
style.textContent = `.dot { animation: dotPulse 1.5s infinite; opacity: 0; } .dot:nth-child(1) { animation-delay: 0s; } .dot:nth-child(2) { animation-delay: 0.3s; } .dot:nth-child(3) { animation-delay: 0.6s; } @keyframes dotPulse { 0%, 100% { opacity: 0; } 50% { opacity: 1; } }`;
document.head.appendChild(style);
