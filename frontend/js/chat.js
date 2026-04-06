import { postMensajeChat } from './api.js';
import { mostrarToast } from './ui.js';

let appState = null;

export function initChat(state) {
    appState = state;
    const chatSend = document.getElementById('chat-send');
    const chatInput = document.getElementById('chat-input');
    const sugerenciaBtns = document.querySelectorAll('.sugerencia-btn');
    
    const avatarBtn = document.getElementById('chat-avatar-btn');
    const chatWindow = document.getElementById('chat-window');
    const closeBtn = document.getElementById('close-chat-btn');

    // Lógica para abrir/cerrar Byte
    avatarBtn.addEventListener('click', () => {
        chatWindow.style.display = 'flex';
        chatWindow.classList.remove('fade-out');
    });

    closeBtn.addEventListener('click', () => {
        chatWindow.classList.add('fade-out');
        setTimeout(() => {
            chatWindow.style.display = 'none';
        }, 400); // 400ms = time in fadeOut animation
    });

    chatSend.addEventListener('click', enviarMensajeChat);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') enviarMensajeChat();
    });

    sugerenciaBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.getAttribute('data-msg');
            enviarMensajeChat();
        });
    });
}

export function abrirChatObj() {
    const chatWindow = document.getElementById('chat-window');
    chatWindow.style.display = 'flex';
    chatWindow.classList.remove('fade-out');
}

export async function enviarMensajeChat() {
    const chatInput = document.getElementById('chat-input');
    const mensaje = chatInput.value.trim();
    if (!mensaje) return;
    
    agregarMensajeChat(mensaje, 'user');
    chatInput.value = '';
    mostrarIndicadorEscritura();
    
    try {
        const data = await postMensajeChat(mensaje, appState.lenguajeSeleccionado);
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
        mostrarToast('Error de conexión en el chat', 'error');
    }
}

export function agregarMensajeChat(texto, tipo) {
    const chatMessages = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${tipo}`;
    
    const tiempo = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Evitamos innerHTML plano para el texto ingresado
    div.innerHTML = `
        <div class="message-content">
            ${tipo === 'bot' 
                ? '<div class="bubble-avatar-small">🤖</div>' 
                : '<div class="bubble-avatar-small" style="background: linear-gradient(135deg, #48bb78, #3ca860);">👤</div>'}
            <div class="message-text"></div>
        </div>
        <div class="message-time">${tiempo}</div>
    `;
    div.querySelector('.message-text').textContent = texto;
    
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function mostrarIndicadorEscritura() {
    const chatMessages = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message bot typing-indicator';
    div.id = 'typing-indicator';
    div.innerHTML = `
        <div class="message-content">
            <div class="bubble-avatar-small">🤖</div>
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
