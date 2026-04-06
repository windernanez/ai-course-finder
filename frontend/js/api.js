const API_URL = '/api';

export function getSessionId() {
    let sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2);
        localStorage.setItem('session_id', sessionId);
    }
    return sessionId;
}

export async function fetchLenguajes() {
    const response = await fetch(`${API_URL}/lenguajes`);
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function fetchEstadisticas() {
    const response = await fetch(`${API_URL}/estadisticas`);
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function postBuscarCursos(lenguaje, nivel) {
    const response = await fetch(`${API_URL}/buscar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            lenguaje: lenguaje,
            nivel: nivel,
            session_id: getSessionId()
        })
    });
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function postMensajeChat(mensaje, lenguajeSeleccionado) {
    const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            mensaje: mensaje,
            lenguaje: lenguajeSeleccionado || null,
            session_id: getSessionId()
        })
    });
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function fetchPresentacion(lenguaje) {
    const response = await fetch(`${API_URL}/presentacion/${lenguaje}`);
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function fetchMe() {
    const response = await fetch(`${API_URL}/user/me`);
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function fetchProgreso(lenguaje, nivel) {
    const response = await fetch(`${API_URL}/progreso?lenguaje=${lenguaje}&nivel=${nivel}`);
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function postCompletarVideo(videoId, lenguaje, nivel, totalVideos) {
    const response = await fetch(`${API_URL}/completar-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_id: videoId, lenguaje, nivel, total_videos: totalVideos })
    });
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function postGenerarQuiz(lenguaje, nivel) {
    const response = await fetch(`${API_URL}/generar-quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lenguaje, nivel })
    });
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function postValidarQuiz(lenguaje, nivel, respuestas) {
    const response = await fetch(`${API_URL}/validar-quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lenguaje, nivel, respuestas })
    });
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}

export async function postEnviarCertificado(lenguaje, nivel) {
    const response = await fetch(`${API_URL}/enviar-certificado`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lenguaje, nivel })
    });
    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
    return await response.json();
}
