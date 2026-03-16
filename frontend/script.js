// Configuración
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

// Cargar lenguajes
async function cargarLenguajes() {
    try {
        console.log('📡 Cargando lenguajes desde:', API_URL + '/lenguajes');
        
        const response = await fetch(`${API_URL}/lenguajes`);
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const lenguajes = await response.json();
        console.log('✅ Lenguajes cargados:', lenguajes);
        
        lenguajeSelect.innerHTML = '<option value="">Selecciona un lenguaje...</option>';
        lenguajes.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang.id;
            option.textContent = `${lang.icono} ${lang.nombre}`;
            lenguajeSelect.appendChild(option);
        });
        
    } catch (error) {
        console.error('❌ Error cargando lenguajes:', error);
        lenguajeSelect.innerHTML = '<option value="">Error cargando lenguajes</option>';
        mostrarError('No se pudieron cargar los lenguajes. ¿El backend está corriendo?');
    }
}

// Configurar event listeners
function configurarEventListeners() {
    // Selección de nivel
    nivelCards.forEach(card => {
        card.addEventListener('click', () => {
            const radio = card.querySelector('input');
            radio.checked = true;
            nivelSeleccionado = radio.value;
            
            // Actualizar UI
            nivelCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
        });
    });

    // Buscar
    buscarBtn.addEventListener('click', buscarCursos);
    
    // Enter en select
    lenguajeSelect.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            buscarCursos();
        }
    });

    // Chat eventos
    chatSend.addEventListener('click', enviarMensajeChat);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            enviarMensajeChat();
        }
    });

    // Botones de sugerencia
    sugerenciaBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mensaje = btn.getAttribute('data-msg');
            chatInput.value = mensaje;
            enviarMensajeChat();
        });
    });
}

// Buscar cursos
async function buscarCursos() {
    lenguajeSeleccionado = lenguajeSelect.value;
    
    if (!lenguajeSeleccionado) {
        alert('Por favor selecciona un lenguaje de programación');
        return;
    }

    // Mostrar loading
    loadingDiv.style.display = 'block';
    resultadosDiv.style.display = 'none';
    recomendacionChat.style.display = 'none';
    
    try {
        console.log('📡 Buscando cursos:', { lenguaje: lenguajeSeleccionado, nivel: nivelSeleccionado });
        
        const response = await fetch(`${API_URL}/buscar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lenguaje: lenguajeSeleccionado,
                nivel: nivelSeleccionado
            })
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }

        const data = await response.json();
        console.log('✅ Respuesta recibida:', data);
        
        if (data.exito) {
            mostrarResultados(data);
            
            // Mostrar recomendación del chat si existe
            if (data.recomendacion_chat) {
                recomendacionTexto.textContent = data.recomendacion_chat;
                recomendacionChat.style.display = 'flex';
            }
            
            // Mensaje del chatbot sobre la búsqueda
            agregarMensajeChat(`He encontrado ${data.total_videos} videos de ${data.lenguaje} nivel ${data.nivel}. ¡Espero que te sean útiles! 🚀`, 'bot');
            
        } else {
            mostrarError(data.error || 'Error en la búsqueda');
        }
    } catch (error) {
        console.error('❌ Error en búsqueda:', error);
        mostrarError('Error de conexión con el servidor');
    } finally {
        loadingDiv.style.display = 'none';
    }
}

// Funciones del Chat
async function enviarMensajeChat() {
    const mensaje = chatInput.value.trim();
    if (!mensaje) return;
    
    // Mostrar mensaje del usuario
    agregarMensajeChat(mensaje, 'user');
    chatInput.value = '';
    
    // Mostrar indicador de escritura
    mostrarIndicadorEscritura();
    
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                mensaje: mensaje,
                lenguaje: lenguajeSeleccionado || null
            })
        });
        
        const data = await response.json();
        
        // Quitar indicador de escritura
        quitarIndicadorEscritura();
        
        if (data.exito) {
            agregarMensajeChat(data.respuesta, 'bot');
        } else {
            agregarMensajeChat('Lo siento, tuve un problema. ¿Puedes repetirlo?', 'bot');
        }
        
    } catch (error) {
        console.error('Error en chat:', error);
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
    if (indicator) {
        indicator.remove();
    }
}

// Mostrar resultados
function mostrarResultados(data) {
    const nombreLenguaje = lenguajeSelect.options[lenguajeSelect.selectedIndex].text;
    resultadosTitulo.innerHTML = `<i class="fas fa-code"></i> Cursos de ${nombreLenguaje} - Nivel ${data.nivel}`;
    resultadosMensaje.textContent = data.mensaje;
    
    // Mostrar videos
    videosContainer.innerHTML = '';
    if (data.videos.length === 0) {
        videosContainer.innerHTML = '<p style="text-align: center; padding: 20px;">No se encontraron videos. Prueba con otro lenguaje o nivel.</p>';
    } else {
        data.videos.forEach(video => {
            videosContainer.appendChild(crearVideoCard(video));
        });
    }
    
    // Mostrar canales recomendados
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
    
    // Actualizar estadísticas
    cargarEstadisticas();
}

// Crear tarjeta de video
function crearVideoCard(video) {
    const card = document.createElement('div');
    card.className = 'video-card';
    
    const nivelClass = `nivel-${video.nivel_detectado}`;
    const nivelIcon = video.nivel_detectado === 'principiante' ? '🌱' : 
                     video.nivel_detectado === 'intermedio' ? '📚' : '🚀';
    
    card.innerHTML = `
        <div class="video-thumbnail">
            <img src="${video.miniatura}" alt="${video.titulo}">
            <span class="video-duration">${video.duracion || 'N/A'}</span>
        </div>
        <div class="video-info">
            <h3 class="video-title">${video.titulo}</h3>
            <p class="video-channel"><i class="fas fa-user"></i> ${video.canal}</p>
            <div class="video-meta">
                <span><i class="fas fa-eye"></i> ${video.vistas}</span>
                <span><i class="fas fa-thumbs-up"></i> ${video.likes}</span>
                <span><i class="fas fa-calendar"></i> ${video.fecha}</span>
            </div>
            <div>
                <span class="nivel-badge ${nivelClass}">${nivelIcon} ${video.nivel_detectado}</span>
                <span class="confianza"><i class="fas fa-microchip"></i> ${video.confianza_nivel}% confianza IA</span>
            </div>
            <div class="video-footer">
                <a href="${video.enlace}" target="_blank" class="btn-ver">
                    <i class="fas fa-play"></i> Ver en YouTube
                </a>
                <span class="relevancia"><i class="fas fa-star"></i> ${video.relevancia}% relevante</span>
            </div>
        </div>
    `;
    
    return card;
}

// Crear tarjeta de canal
function crearCanalCard(canal) {
    const card = document.createElement('div');
    card.className = 'canal-card';
    
    card.innerHTML = `
        <img src="${canal.miniatura}" alt="${canal.nombre}">
        <div class="canal-info">
            <h4>${canal.nombre}</h4>
            <p><i class="fas fa-users"></i> ${canal.suscriptores} suscriptores</p>
            <p><i class="fas fa-video"></i> ${canal.videos} videos</p>
        </div>
    `;
    
    return card;
}

// Cargar estadísticas
async function cargarEstadisticas() {
    try {
        const response = await fetch(`${API_URL}/estadisticas`);
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const stats = await response.json();
        
        if (stats.total_busquedas > 0) {
            statsContainer.innerHTML = `
                <div class="stat-card">
                    <i class="fas fa-search"></i>
                    <div class="stat-info">
                        <h4>${stats.total_busquedas}</h4>
                        <p>Búsquedas realizadas</p>
                    </div>
                </div>
                ${stats.lenguajes_populares.map(l => `
                    <div class="stat-card">
                        <i class="fas fa-code"></i>
                        <div class="stat-info">
                            <h4>${l.lenguaje}</h4>
                            <p>${l.busquedas} búsquedas</p>
                        </div>
                    </div>
                `).join('')}
            `;
        } else {
            statsContainer.innerHTML = '<p>No hay estadísticas disponibles aún. ¡Realiza tu primera búsqueda!</p>';
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
        statsContainer.innerHTML = '<p>Error cargando estadísticas</p>';
    }
}

// Mostrar error
function mostrarError(mensaje) {
    resultadosDiv.style.display = 'block';
    resultadosTitulo.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
    resultadosMensaje.textContent = mensaje;
    videosContainer.innerHTML = '<p style="text-align: center; padding: 20px;">No se pudieron cargar los resultados</p>';
    canalesSection.style.display = 'none';
}

// Añadir estilos para el indicador de escritura
const style = document.createElement('style');
style.textContent = `
    .typing-indicator .message-text {
        color: #666;
    }
    .dot {
        animation: dotPulse 1.5s infinite;
        opacity: 0;
    }
    .dot:nth-child(1) { animation-delay: 0s; }
    .dot:nth-child(2) { animation-delay: 0.3s; }
    .dot:nth-child(3) { animation-delay: 0.6s; }
    
    @keyframes dotPulse {
        0%, 100% { opacity: 0; }
        50% { opacity: 1; }
    }
`;
document.head.appendChild(style);
