export function mostrarToast(mensaje, tipo = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.bottom = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.style.background = tipo === 'error' ? '#ff4c4c' : tipo === 'success' ? '#4caf50' : '#333';
    toast.style.color = '#fff';
    toast.style.padding = '12px 20px';
    toast.style.borderRadius = '8px';
    toast.style.marginTop = '10px';
    toast.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    toast.textContent = mensaje;

    container.appendChild(toast);

    setTimeout(() => toast.style.opacity = '1', 10);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

export function renderLenguajes(lenguajes) {
    const selector = document.getElementById('lenguaje');
    selector.innerHTML = '<option value="">Selecciona un lenguaje...</option>';
    lenguajes.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang.id;
        option.textContent = `${lang.icono} ${lang.nombre}`;
        selector.appendChild(option);
    });
}

export function mostrarError(mensaje) {
    const resultadosDiv = document.getElementById('resultados');
    const resultadosTitulo = document.getElementById('resultados-titulo');
    const resultadosMensaje = document.getElementById('resultados-mensaje');
    const videosContainer = document.getElementById('videos-container');
    const canalesSection = document.getElementById('canales-recomendados');

    resultadosDiv.style.display = 'block';
    resultadosTitulo.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
    resultadosMensaje.textContent = mensaje;
    videosContainer.innerHTML = '<p style="text-align: center; padding: 20px;">No se pudieron cargar los resultados</p>';
    canalesSection.style.display = 'none';
    mostrarToast(mensaje, 'error');
}

export function renderUserProfile(userData, onLogin, onLogout) {
    const container = document.getElementById('user-profile');
    if (!userData || !userData.logged_in) {
        container.innerHTML = `
            <button id="loginBtn" class="btn-login">
                <i class="fab fa-google"></i> Iniciar sesión con Gmail
            </button>
        `;
        document.getElementById('loginBtn').onclick = onLogin;
    } else {
        const user = userData.user;
        container.innerHTML = `
            <div class="user-info" style="display: flex; align-items: center; gap: 10px;">
                <img src="${user.imagen || 'https://via.placeholder.com/35'}" class="user-avatar" alt="${user.nombre}">
                <div style="display: flex; flex-direction: column;">
                    <span class="user-name">${user.nombre}</span>
                    <button id="logoutBtn" class="btn-logout">Cerrar sesión</button>
                </div>
            </div>
        `;
        document.getElementById('logoutBtn').onclick = onLogout;
    }
}

export function updateProgressBar(progresoData) {
    const container = document.getElementById('progreso-curso-container');
    const fill = document.getElementById('progreso-bar-fill');
    const percentText = document.getElementById('progreso-porcentaje');
    const quizBanner = document.getElementById('quiz-ready-banner');
    const certBanner = document.getElementById('certificado-ready-banner');

    if (!progresoData || progresoData.progreso === undefined) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    const p = Math.round(progresoData.progreso || 0);
    const numVistos = (progresoData.videos_vistos || []).length;
    
    fill.style.width = `${p}%`;
    percentText.textContent = `Vistos: ${numVistos} / 4 (${p}%)`;

    // Gestionar banners
    quizBanner.style.display = (p >= 99 && !progresoData.examen_aprobado) ? 'block' : 'none';
    certBanner.style.display = (progresoData.examen_aprobado && !progresoData.certificado_generado) ? 'block' : 'none';
}

export function mostrarQuizModal(quizData, onValidate) {
    const modal = document.getElementById('quiz-modal');
    const titulo = document.getElementById('quiz-titulo');
    const preguntasCont = document.getElementById('quiz-preguntas');
    const resultadoDiv = document.getElementById('quiz-resultado');
    const form = document.getElementById('quiz-form');
    const enviarBtn = document.getElementById('enviarQuizBtn');

    try {
        titulo.textContent = quizData.titulo || 'Examen de Conocimiento';
        preguntasCont.innerHTML = '';
        resultadoDiv.style.display = 'none';
        form.style.display = 'block';
        enviarBtn.style.display = 'block';

        if (!quizData.preguntas) {
            throw new Error("El objeto quizData no tiene propiedad 'preguntas'. Datos recibidos: " + JSON.stringify(quizData).substring(0, 50));
        }

        quizData.preguntas.forEach((p, i) => {
            const pDiv = document.createElement('div');
            pDiv.className = 'quiz-per-pregunta';
            pDiv.innerHTML = `
                <p class="quiz-pregunta-texto">${i + 1}. ${p.pregunta}</p>
                <div class="quiz-opciones">
                    ${p.opciones.map((opt, j) => `
                        <label class="quiz-opcion">
                            <input type="radio" name="pregunta_${i}" value="${j}" required>
                            <span>${opt}</span>
                        </label>
                    `).join('')}
                </div>
            `;
            preguntasCont.appendChild(pDiv);
        });

        modal.classList.add('active');
    } catch(err) {
        alert("Error al mostrar Modal de Quiz: " + err.message);
        console.error(err);
    }
    
    enviarBtn.onclick = async () => {
        const formData = new FormData(form);
        const respuestas = [];
        let todasRespondidas = true;
        
        for(let i=0; i < quizData.preguntas.length; i++) {
            const val = formData.get(`pregunta_${i}`);
            if (val === null) {
                todasRespondidas = false;
                break;
            }
            respuestas.push(parseInt(val));
        }

        if (!todasRespondidas) {
            mostrarToast('Por favor responde todas las preguntas', 'error');
            return;
        }

        enviarBtn.disabled = true;
        enviarBtn.textContent = 'Validando...';
        
        try {
            const result = await onValidate(respuestas);
            
            form.style.display = 'none';
            enviarBtn.style.display = 'none';
            resultadoDiv.style.display = 'block';
            
            if (result.aprobado) {
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        <i class="fas fa-certificate" style="color: #ffd966; font-size: 5rem; margin-bottom: 15px;"></i>
                        <div class="quiz-score aprobado" style="font-size: 2.5rem; margin-bottom: 10px;">${result.puntuacion}%</div>
                        <h3 style="color: #4caf50; font-size: 1.8rem; margin: 10px 0;">¡HAS APROBADO!</h3>
                        <p style="font-size: 1.1rem; color: #e2e8f0;">${result.mensaje}</p>
                        <p style="color: #a6c1ff; margin-bottom: 25px;">Ya puedes solicitar tu certificado desde el panel principal.</p>
                        <button class="btn-modal-primary" id="cerrarQuizResultadoBtn">Cerrar y Ver Certificado</button>
                    </div>
                `;
            } else {
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        <i class="fab fa-android" style="color: #3DDC84; font-size: 5rem; margin-bottom: 15px; animation: popIn 0.5s ease-out;"></i>
                        <div class="quiz-score reprobado" style="font-size: 2.5rem; margin-bottom: 10px;">${result.puntuacion}%</div>
                        <h3 style="color: #ff4c4c; font-size: 1.8rem; margin: 10px 0; letter-spacing: 2px;">SIGUE INTENTANDO</h3>
                        <p style="font-size: 1.1rem; color: #e2e8f0; margin-bottom: 25px;">No has alcanzado la puntuación mínima requerida (80%). ¡Repasa los conceptos y vuelve a intentarlo!</p>
                        <button class="btn-modal-secondary" id="cerrarQuizResultadoBtn">Volver a estudiar</button>
                    </div>
                `;
            }
            document.getElementById('cerrarQuizResultadoBtn').onclick = () => {
                modal.classList.remove('active');
                enviarBtn.disabled = false;
                enviarBtn.textContent = 'Finalizar Examen';
                
                if (result.aprobado) {
                    const btnCert = document.getElementById('descargarCertificadoBtn');
                    if (btnCert) btnCert.click();
                }
            };
        } catch (err) {
            let errorMsg = err.message;
            if (errorMsg.includes('401')) {
                errorMsg = 'Debes iniciar sesión para finalizar el examen.';
            } else if (errorMsg.includes('400')) {
                errorMsg = 'El examen ha expirado. Por favor, ciérralo e intenta generarlo de nuevo.';
            }
            mostrarToast('Problema: ' + errorMsg, 'error');
            enviarBtn.disabled = false;
            enviarBtn.textContent = 'Finalizar Examen';
        }
    };

    document.getElementById('close-quiz-modal').onclick = () => modal.classList.remove('active');
    document.getElementById('cancelarQuizBtn').onclick = () => modal.classList.remove('active');
}

export function mostrarResultados(data, textLenguaje, userLogged, videoVistos = [], onMarcarVisto) {
    const resultadosDiv = document.getElementById('resultados');
    const resultadosTitulo = document.getElementById('resultados-titulo');
    const resultadosMensaje = document.getElementById('resultados-mensaje');
    const videosContainer = document.getElementById('videos-container');
    const canalesContainer = document.getElementById('canales-container');
    const canalesSection = document.getElementById('canales-recomendados');
    const recomendacionChat = document.getElementById('recomendacion-chat');
    const recomendacionTexto = document.getElementById('recomendacion-texto');

    resultadosTitulo.innerHTML = `<i class="fas fa-code"></i> Cursos de ${textLenguaje} - Nivel ${data.nivel}`;
    resultadosMensaje.textContent = data.mensaje;

    videosContainer.innerHTML = '';
    if (data.videos.length === 0) {
        videosContainer.innerHTML = '<p style="text-align: center; padding: 20px;">No se encontraron videos.</p>';
    } else {
        data.videos.forEach((video, index) => {
            const isVisto = videoVistos.includes(video.id);
            const card = crearVideoCard(video, userLogged, isVisto, (visto) => onMarcarVisto(video.id, visto, data.videos.length));
            card.style.opacity = '0';
            card.style.animation = `fadeInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards ${index * 0.08}s`;
            videosContainer.appendChild(card);
        });
    }

    if (data.canales_recomendados && data.canales_recomendados.length > 0) {
        canalesSection.style.display = 'block';
        canalesContainer.innerHTML = '';
        data.canales_recomendados.forEach((canal, index) => {
            const card = crearCanalCard(canal);
            card.style.opacity = '0';
            card.style.animation = `fadeInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards ${(index * 0.1) + 0.3}s`;
            canalesContainer.appendChild(card);
        });
    } else {
        canalesSection.style.display = 'none';
    }

    if (data.recomendacion_chat) {
        recomendacionTexto.textContent = data.recomendacion_chat;
        recomendacionChat.style.display = 'flex';
    } else {
        recomendacionChat.style.display = 'none';
    }

    resultadosDiv.style.display = 'block';
}

function crearVideoCard(video, userLogged, isVisto, onToggleVisto) {
    const card = document.createElement('div');
    card.className = `video-card ${isVisto ? 'card-visto' : ''}`;
    const nivelClass = `nivel-${video.nivel_detectado}`;
    const nivelIcon = video.nivel_detectado === 'principiante' ? '🌱' : video.nivel_detectado === 'intermedio' ? '📚' : '🚀';

    const thumbnail = document.createElement('div');
    thumbnail.className = 'video-thumbnail';
    thumbnail.innerHTML = `<img src="" alt=""><span class="video-duration"></span>`;
    
    // Checkbox de visto
    if (userLogged) {
        const check = document.createElement('label');
        check.className = 'video-visto-check';
        check.innerHTML = `<input type="checkbox" ${isVisto ? 'checked' : ''}> <span>Visto</span>`;
        check.onclick = (e) => e.stopPropagation();
        check.querySelector('input').onchange = (e) => {
            const visto = e.target.checked;
            if (visto) card.classList.add('card-visto');
            else card.classList.remove('card-visto');
            onToggleVisto(visto);
        };
        thumbnail.appendChild(check);
    }

    thumbnail.querySelector('img').src = video.miniatura;
    thumbnail.querySelector('img').alt = video.titulo;
    thumbnail.querySelector('.video-duration').textContent = video.duracion || 'N/A';

    const info = document.createElement('div');
    info.className = 'video-info';

    const title = document.createElement('h3');
    title.className = 'video-title';
    title.textContent = video.titulo;

    const channel = document.createElement('p');
    channel.className = 'video-channel';
    channel.innerHTML = `<i class="fas fa-user"></i> `;
    channel.appendChild(document.createTextNode(video.canal));

    const meta = document.createElement('div');
    meta.className = 'video-meta';
    meta.innerHTML = `<span><i class="fas fa-eye"></i> ${video.vistas}</span>
                      <span><i class="fas fa-thumbs-up"></i> ${video.likes}</span>
                      <span><i class="fas fa-calendar"></i> ${video.fecha}</span>`;

    const badges = document.createElement('div');
    badges.innerHTML = `<span class="nivel-badge ${nivelClass}">${nivelIcon} ${video.nivel_detectado}</span>
                        <span class="confianza"><i class="fas fa-microchip"></i> ${video.confianza_nivel}% confianza</span>`;

    const footer = document.createElement('div');
    footer.className = 'video-footer';
    footer.innerHTML = `<a href="${video.enlace}" target="_blank" class="btn-ver"><i class="fas fa-play"></i> Ver en YouTube</a>
                        <span class="relevancia"><i class="fas fa-star"></i> ${video.relevancia}% relevante</span>`;

    info.append(title, channel, meta, badges, footer);
    card.append(thumbnail, info);

    return card;
}

function crearCanalCard(canal) {
    const card = document.createElement('div');
    card.className = 'canal-card';

    const img = document.createElement('img');
    img.src = canal.miniatura;
    img.alt = canal.nombre;

    const info = document.createElement('div');
    info.className = 'canal-info';

    const name = document.createElement('h4');
    name.textContent = canal.nombre;

    const p1 = document.createElement('p');
    p1.innerHTML = `<i class="fas fa-users"></i> ${canal.suscriptores} subs`;

    const p2 = document.createElement('p');
    p2.innerHTML = `<i class="fas fa-video"></i> ${canal.videos} videos`;

    info.append(name, p1, p2);
    card.append(img, info);
    return card;
}

export function renderEstadisticas(stats) {
    const container = document.getElementById('stats-container');
    if (stats.total_busquedas > 0) {
        container.innerHTML = '';

        const mainStat = document.createElement('div');
        mainStat.className = 'stat-card';
        mainStat.style.opacity = '0';
        mainStat.style.animation = `fadeInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards`;
        mainStat.innerHTML = `
            <i class="fas fa-search"></i>
            <div class="stat-info">
                <h4>${stats.total_busquedas}</h4>
                <p>Búsquedas registradas</p>
            </div>
        `;
        container.appendChild(mainStat);

        stats.lenguajes_populares.forEach((l, index) => {
            const statCard = document.createElement('div');
            statCard.className = 'stat-card';
            statCard.style.opacity = '0';
            statCard.style.animation = `fadeInUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards ${(index + 1) * 0.1}s`;
            statCard.innerHTML = `
                <i class="fas fa-code"></i>
                <div class="stat-info">
                    <h4>${l.lenguaje}</h4>
                    <p>${l.busquedas} búsquedas</p>
                </div>
            `;
            container.appendChild(statCard);
        });
    } else {
        container.innerHTML = '<p>No hay estadísticas disponibles aún...</p>';
    }
}

export function renderPresentacion(data) {
    const container = document.getElementById('presentacion-container');
    if (!data || !data.exito) {
        container.style.display = 'none';
        return;
    }

    const info = data.data;
    const accentColor = info.estetica_color || '#ff6b4a';

    const hexToRgb = (hex) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '255, 107, 74';
    };
    const accentRgb = hexToRgb(accentColor);

    container.innerHTML = `
        <div class="presentation-card" style="--lang-accent: ${accentColor}; --lang-accent-rgb: ${accentRgb}">
            <div class="presentation-accent"></div>
            <div class="pres-header">
                <div class="pres-title-group">
                    <h3>Lo más relevante de ${info.nombre}</h3>
                    <span class="pres-badge"><i class="fas fa-microchip"></i> Ficha Técnica Generativa</span>
                </div>
                <div class="pres-type-icon">
                    <i class="fas fa-terminal" style="font-size: 2.5rem; color: ${accentColor}; opacity: 0.8;"></i>
                </div>
            </div>
            
            <div class="pres-content">
                <div class="pres-main">
                    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
                        <span style="font-size: 1rem; background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); font-weight: 600;">
                            <i class="fas fa-user-edit"></i> ${info.creador || 'Comunidad'}
                        </span>
                        <span style="font-size: 1rem; background: rgba(255,255,255,0.1); padding: 4px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); font-weight: 600;">
                            <i class="fas fa-calendar-alt"></i> ${info.anio_creacion || 'N/A'}
                        </span>
                    </div>
                    <p class="pres-desc">${info.descripcion}</p>
                    
                    ${info.curiosidad ? `
                    <div class="pres-curiosidad" style="background: rgba(var(--lang-accent-rgb, 255, 107, 74), 0.1); border-left: 4px solid ${accentColor}; padding: 1.2rem; margin: 1.5rem 0; border-radius: 0 12px 12px 0;">
                        <p style="margin: 0; font-size: 1.1rem; font-style: italic; line-height: 1.5;">
                            <i class="fas fa-lightbulb" style="color: #ffd966; font-size: 1.3rem;"></i> <strong>¿Sabías que?</strong> ${info.curiosidad}
                        </p>
                    </div>
                    ` : ''}

                    <div class="pres-features">
                        ${info.caracteristicas.map(f => `
                            <span class="feature-tag">
                                <i class="fas fa-check-circle"></i> ${f}
                            </span>
                        `).join('')}
                    </div>

                    <div class="pres-examples-enhanced" style="margin-top: 2.5rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 2rem;">
                        <h4 class="enhanced-title" style="color: #ffd966; font-size: 1.2rem; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 2px; font-weight: 800; text-align: center;">
                            <i class="fas fa-magic"></i> Creaciones Destacadas
                        </h4>
                        <p style="text-align: center; font-size: 0.9rem; color: #94a3b8; margin-bottom: 2rem;">
                            Proyectos icónicos logrados con este lenguaje. ¡Haz clic para explorar! ✨
                        </p>
                        
                        <div class="examples-grid-dynamic">
                            <!-- Categoría: Sistemas -->
                            <div class="example-category-card system-card">
                                <div class="category-header">
                                    <div class="category-icon"><i class="fas fa-server"></i></div>
                                    <div class="category-info">
                                        <span class="category-label">Arquitectura</span>
                                        <h5>Sistemas</h5>
                                    </div>
                                </div>
                                <div class="category-items">
                                    ${(info.ejemplos_relevantes?.sistemas || []).length > 0 ?
            (info.ejemplos_relevantes.sistemas).map((s, index) => {
                const nombre = typeof s === 'object' ? s.nombre : s;
                const icono = typeof s === 'object' ? s.icono : 'fas fa-cog';
                return `<div class="dynamic-item-tag" data-name="${nombre}" style="--item-index: ${index}"><i class="${icono}"></i> <span>${nombre}</span></div>`;
            }).join('') :
            '<span class="no-data">Consultando...</span>'}
                                </div>
                            </div>

                            <!-- Categoría: Apps -->
                            <div class="example-category-card app-card">
                                <div class="category-header">
                                    <div class="category-icon"><i class="fas fa-mobile-alt"></i></div>
                                    <div class="category-info">
                                        <span class="category-label">Producto</span>
                                        <h5>Aplicaciones</h5>
                                    </div>
                                </div>
                                <div class="category-items">
                                    ${(info.ejemplos_relevantes?.apps || []).length > 0 ?
            (info.ejemplos_relevantes.apps).map((a, index) => {
                const nombre = typeof a === 'object' ? a.nombre : a;
                const icono = typeof a === 'object' ? a.icono : 'fas fa-mobile-alt';
                return `<div class="dynamic-item-tag" data-name="${nombre}" style="--item-index: ${index}"><i class="${icono}"></i> <span>${nombre}</span></div>`;
            }).join('') :
            '<span class="no-data">Consultando...</span>'}
                                </div>
                            </div>

                            <!-- Categoría: Juegos -->
                            <div class="example-category-card game-card">
                                <div class="category-header">
                                    <div class="category-icon"><i class="fas fa-gamepad"></i></div>
                                    <div class="category-info">
                                        <span class="category-label">Entretenimiento</span>
                                        <h5>Juegos</h5>
                                    </div>
                                </div>
                                <div class="category-items">
                                    ${(info.ejemplos_relevantes?.juegos || []).length > 0 ?
            (info.ejemplos_relevantes.juegos).map((j, index) => {
                const nombre = typeof j === 'object' ? j.nombre : j;
                const icono = typeof j === 'object' ? j.icono : 'fas fa-gamepad';
                return `<div class="dynamic-item-tag" data-name="${nombre}" style="--item-index: ${index}"><i class="${icono}"></i> <span>${nombre}</span></div>`;
            }).join('') :
            '<span class="no-data">Consultando...</span>'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="pres-sidebar">
                    <h4><i class="fas fa-rocket"></i> Casos de Uso</h4>
                    <ul class="pres-list">
                        ${info.casos_uso.map(cu => `
                            <li><i class="fas fa-arrow-right"></i> ${cu}</li>
                        `).join('')}
                    </ul>
                    <div class="popularity-card" style="margin-top: 3rem; border-top: 2px solid rgba(255,255,255,0.2); padding-top: 2.5rem;">
                        <h4 style="font-size: 1.4rem; opacity: 1; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 1rem; color: #ffd966; font-weight: 800;">
                            <i class="fas fa-chart-line"></i> Popularidad
                        </h4>
                        <p style="font-size: 1.6rem; color: #ffffff; line-height: 1.6; font-weight: 600; text-shadow: 0 2px 10px rgba(0,0,0,0.5);">${info.popularidad}</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Event Delegation para los items clicables (más robusto)
    container.onclick = (e) => {
        const item = e.target.closest('.dynamic-item-tag');
        if (!item) return;

        const projectName = item.getAttribute('data-name');
        const proyectos = info.proyectos_famosos || [];

        const projectData = proyectos.find(p => p.nombre === projectName) ||
            proyectos.find(p => projectName.toLowerCase().includes(p.nombre.toLowerCase())) ||
        {
            nombre: projectName,
            descripcion: "Un proyecto destacado desarrollado con este lenguaje.",
            info_detallada: "Este es uno de los muchos proyectos exitosos que demuestran la versatilidad de este lenguaje en el mundo real.",
            anio: "N/A",
            tipo: "Proyecto",
            icono: item.querySelector('i')?.className || 'fas fa-rocket'
        };

        mostrarModalProyecto(projectData);
    };

    container.style.display = 'block';
}

function mostrarModalProyecto(datos) {
    const modal = document.getElementById('project-modal');
    document.getElementById('modal-project-name').innerHTML = `<i class="${datos.icono || 'fas fa-rocket'}"></i> ${datos.nombre}`;
    document.getElementById('modal-project-type').textContent = datos.tipo || 'Proyecto';
    document.getElementById('modal-project-year').textContent = datos.anio || 'N/A';
    document.getElementById('modal-project-desc').textContent = datos.descripcion;
    document.getElementById('modal-project-details').textContent = datos.info_detallada;

    modal.classList.add('active'); // Usar clase para visibilidad
    document.body.style.overflow = 'hidden'; // Evitar scroll de fondo

    // Configurar cierre
    const closeBtn = document.getElementById('close-project-modal');
    const okBtn = document.getElementById('modal-btn-ok');

    const cerrar = () => {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    };

    closeBtn.onclick = cerrar;
    okBtn.onclick = cerrar;
    modal.onclick = (e) => {
        if (e.target === modal) cerrar();
    };
}
