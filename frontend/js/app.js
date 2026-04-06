import { 
    fetchLenguajes, 
    fetchEstadisticas, 
    postBuscarCursos, 
    fetchPresentacion, 
    fetchMe, 
    fetchProgreso, 
    postCompletarVideo, 
    postGenerarQuiz, 
    postValidarQuiz, 
    postEnviarCertificado 
} from './api.js';

import { 
    renderLenguajes, 
    mostrarError, 
    mostrarResultados, 
    renderEstadisticas, 
    mostrarToast, 
    renderPresentacion,
    renderUserProfile,
    updateProgressBar,
    mostrarQuizModal
} from './ui.js';

import { initChat, agregarMensajeChat, abrirChatObj } from './chat.js';

const state = {
    nivelSeleccionado: 'principiante',
    lenguajeSeleccionado: '',
    ultimaRecomendacion: null,
    user: null,
    progresoActual: null
};

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔄 Inicializando aplicación con Progreso y Certificación...');
    initChat(state);
    
    await checkAuth();
    await cargarDatosIniciales();
    configurarEventListeners();
    
    // Bienvenida interactiva
    setTimeout(() => {
        const ggBubble = document.getElementById('gg-bubble');
        if (ggBubble) {
            const msg = state.user 
                ? `¡Hola de nuevo, ${state.user.nombre}! 👋 ¿Listo para seguir aprendiendo?`
                : "¡Hola! 👋 Inicia sesión con Google para guardar tu progreso y obtener certificados.";
            ggBubble.textContent = msg;
            ggBubble.style.display = 'block';
            setTimeout(() => ggBubble.style.display = 'none', 6000);
        }
    }, 1000);
});

async function checkAuth() {
    try {
        const data = await fetchMe();
        state.user = data.logged_in ? data.user : null;
        renderUserProfile(data, onLogin, onLogout);
    } catch (err) {
        console.error('Error checking auth:', err);
        renderUserProfile(null, onLogin, onLogout);
    }
}

async function onLogin() {
    try {
        const response = await fetch('/login');
        const data = await response.json();
        if (data.auth_url) {
            window.location.href = data.auth_url;
        } else {
            mostrarToast('Error al iniciar sesión: No se pudo generar la URL de autenticación', 'error');
        }
    } catch (error) {
        console.error('Error login:', error);
        mostrarToast('Error de conexión al intentar iniciar sesión', 'error');
    }
}

function onLogout() {
    window.location.href = '/logout';
}

async function cargarDatosIniciales() {
    try {
        const lenguajes = await fetchLenguajes();
        renderLenguajes(lenguajes);
    } catch(err) {
        mostrarError('No se pudieron cargar los lenguajes.');
    }
    
    try {
        const stats = await fetchEstadisticas();
        renderEstadisticas(stats);
    } catch(err) {
        console.error('Error stats:', err);
    }
}

function configurarEventListeners() {
    const nivelCards = document.querySelectorAll('.nivel-card');
    const buscarBtn = document.getElementById('buscarBtn');
    const lenguajeSelect = document.getElementById('lenguaje');

    nivelCards.forEach(card => {
        card.addEventListener('click', () => {
            const radio = card.querySelector('input');
            radio.checked = true;
            state.nivelSeleccionado = radio.value;
            nivelCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
        });
    });

    buscarBtn.addEventListener('click', onBuscar);
    lenguajeSelect.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') onBuscar();
    });

    // Botones de banners de progreso
    document.getElementById('tomarExamenBtn').onclick = onTomarExamen;
    document.getElementById('descargarCertificadoBtn').onclick = onEnviarCertificado;

    // Lógica Ggbyte Avatar
    const ggAvatarBtn = document.getElementById('gg-avatar-btn');
    const ggBubble = document.getElementById('gg-bubble');
    ggAvatarBtn.addEventListener('click', () => {
        const frases = [
            "¡Sigue así, vas por muy buen camino! 🌟",
            "El código perfecto no existe, ¡pero tú estás cerca! 💻",
            "Cada error es una nueva oportunidad para aprender. 🚀",
            "¡Eres capaz de dominar cualquier lenguaje! ✨",
            "Recuerda tomar descansos, ¡tu cerebro te lo agradecerá! ☕"
        ];
        let mensaje = state.ultimaRecomendacion || frases[Math.floor(Math.random() * frases.length)];
        ggBubble.textContent = mensaje;
        ggBubble.style.display = 'block';
        setTimeout(() => ggBubble.style.display = 'none', 6000);
    });
}

async function onBuscar() {
    const lenguajeSelect = document.getElementById('lenguaje');
    state.lenguajeSeleccionado = lenguajeSelect.value;
    
    if (!state.lenguajeSeleccionado) {
        mostrarToast('¡Alto ahí! Debes seleccionar un lenguaje de programación', 'error');
        return;
    }

    const loadingDiv = document.getElementById('loading');
    const resultadosDiv = document.getElementById('resultados');
    const containerProgreso = document.getElementById('progreso-curso-container');
    
    loadingDiv.style.display = 'block';
    resultadosDiv.style.display = 'none';
    containerProgreso.style.display = 'none';
    
    try {
        abrirChatObj();
        agregarMensajeChat(`Buscando las mejores clases de ${state.lenguajeSeleccionado} para ti... ⏳`, 'bot');
        
        const data = await postBuscarCursos(state.lenguajeSeleccionado, state.nivelSeleccionado);
        
        if (data.exito) {
            const textLenguaje = lenguajeSelect.options[lenguajeSelect.selectedIndex].text.replace(/^[^\s]+\s/, '');
            
            let videoVistos = [];
            if (state.user) {
                const progData = await fetchProgreso(state.lenguajeSeleccionado, state.nivelSeleccionado);
                state.progresoActual = progData;
                videoVistos = progData.videos_vistos || [];
                updateProgressBar(progData);
            }
            
            mostrarResultados(data, textLenguaje, !!state.user, videoVistos, onMarcarVisto);
            
            try {
                const presData = await fetchPresentacion(state.lenguajeSeleccionado);
                renderPresentacion(presData);
            } catch (presErr) { console.error('Error pres:', presErr); }
            
            state.ultimaRecomendacion = data.recomendacion_chat || `¡Buena elección! Traje ${data.total_videos} videos. 🚀`;
            
            const stats = await fetchEstadisticas();
            renderEstadisticas(stats);
            mostrarToast('Búsqueda completada', 'success');
        } else {
            mostrarError(data.error || 'Error en la búsqueda');
        }
    } catch (error) {
        console.error('Error:', error);
        mostrarError('Error de conexión');
    } finally {
        loadingDiv.style.display = 'none';
    }
}

async function onMarcarVisto(videoId, visto, totalVideos) {
    if (!state.user) return;
    try {
        const res = await postCompletarVideo(videoId, state.lenguajeSeleccionado, state.nivelSeleccionado, totalVideos, visto);
        if (res && res.progreso !== undefined) {
            state.progresoActual = res;
            updateProgressBar(res);
            mostrarToast(visto ? '¡Video completado! +Progreso' : 'Video marcado como no visto', 'success');
        } else {
            console.error('Error en respuesta de progreso:', res);
        }
    } catch (err) {
        console.error('Error marcando visto:', err);
        mostrarToast('Error al actualizar progreso', 'error');
    }
}

async function onTomarExamen() {
    try {
        mostrarToast('Generando tu examen con Gemini... 🧠', 'info');
        const quizData = await postGenerarQuiz(state.lenguajeSeleccionado, state.nivelSeleccionado);
        
        mostrarQuizModal(quizData, async (respuestas) => {
            const res = await postValidarQuiz(state.lenguajeSeleccionado, state.nivelSeleccionado, respuestas);
            if (res.aprobado !== undefined && state.progresoActual) {
                state.progresoActual.examen_aprobado = res.aprobado;
                state.progresoActual.puntuacion_examen = res.puntuacion;
                updateProgressBar(state.progresoActual);
            }
            return res;
        });
    } catch (err) {
        console.error('Error quiz:', err);
        mostrarToast('Error al generar el examen', 'error');
    }
}

async function onEnviarCertificado() {
    const btn = document.getElementById('descargarCertificadoBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
    
    try {
        const res = await postEnviarCertificado(state.lenguajeSeleccionado, state.nivelSeleccionado);
        if (res.exito) {
            mostrarToast('¡Certificado enviado a tu correo Gmail! 📧', 'success');
            state.progresoActual.certificado_generado = true;
            updateProgressBar(state.progresoActual);
        } else {
            mostrarToast(res.error || 'Error al enviar certificado', 'error');
        }
    } catch (err) {
        console.error('Error cert:', err);
        mostrarToast('Error de conexión al enviar el certificado', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-certificate"></i> Enviar Certificado a Gmail';
    }
}
