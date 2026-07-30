// --- STATE MANAGEMENT ---
let appState = {
    preguntas: {},
    respuestasCargadasCount: 0,
    resultados: {},
    pollingInterval: null,
    currentTab: 'dashboard'
};

// --- DOM ELEMENTS ---
const elements = {
    // Navigation
    navBtns: document.querySelectorAll('.nav-btn'),
    tabPanels: document.querySelectorAll('.tab-panel'),
    serverStatus: document.getElementById('server-status'),
    
    // Dashboard / Evaluation
    dropZoneRespuestas: document.getElementById('drop-zone-respuestas'),
    fileRespuestas: document.getElementById('file-respuestas'),
    uploadStatus: document.getElementById('upload-status'),
    btnIniciarCorreccion: document.getElementById('btn-iniciar-correccion'),
    
    // Stats
    statTotal: document.getElementById('stat-total'),
    statProcesado: document.getElementById('stat-procesado'),
    statErrores: document.getElementById('stat-errores'),
    progressFill: document.getElementById('progress-fill'),
    progressPercent: document.getElementById('progress-percent'),
    
    // Questions Bank
    questionsGrid: document.getElementById('questions-grid'),
    filterPreguntas: document.getElementById('filter-preguntas'),
    btnNuevaPregunta: document.getElementById('btn-nueva-pregunta'),
    filePreguntas: document.getElementById('file-preguntas'),
    
    // Questions Modal
    modalPregunta: document.getElementById('modal-pregunta'),
    formPregunta: document.getElementById('form-pregunta'),
    closeModalPregunta: document.getElementById('close-modal-pregunta'),
    btnCancelarPregunta: document.getElementById('btn-cancelar-pregunta'),
    btnAddConceptoRow: document.getElementById('btn-add-concepto-row'),
    conceptsRowsContainer: document.getElementById('concepts-rows-container'),
    
    // Results
    filterResultados: document.getElementById('filter-resultados'),
    tablaResultadosBody: document.getElementById('tabla-resultados-body'),
    btnExportarCsv: document.getElementById('btn-exportar-csv'),
    resTotalAlumnos: document.getElementById('res-total-alumnos'),
    resPromedioGeneral: document.getElementById('res-promedio-general'),
    resAprobados: document.getElementById('res-aprobados'),
    
    // Student Detail Slide-Over
    modalDetalleAlumno: document.getElementById('modal-detalle-alumno'),
    closeModalDetalle: document.getElementById('close-modal-detalle'),
    detailAlumnoId: document.getElementById('detail-alumno-id'),
    detailAlumnoPromedio: document.getElementById('detail-alumno-promedio'),
    detailAnswersContainer: document.getElementById('detail-answers-container'),
    
    // Connection settings
    inputUrlLlm: document.getElementById('input-url-llm'),
    btnProbarConexion: document.getElementById('btn-probar-conexion'),
    btnGuardarConexion: document.getElementById('btn-guardar-conexion'),
    
    // Global Toast
    toast: document.getElementById('toast')
};

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
});

function initApp() {
    checkServerConfig();
    cargarPreguntas();
    cargarResultados();
    verificarEstadoCorreccion(); // Por si quedó corriendo
}

// --- NETWORK CALLS & DATA RETRIEVAL ---

async function checkServerConfig() {
    try {
        const res = await fetch('/api/config');
        if (!res.ok) throw new Error();
        const data = await res.json();
        
        if (elements.inputUrlLlm) {
            elements.inputUrlLlm.value = data.url_llm || '';
        }
        
        updateServerStatusUI(data.online, data.url_llm);
    } catch (err) {
        updateServerStatusUI(false, '');
        showToast('No se pudo verificar la conexión al LLM.', 'error');
    }
}

function updateServerStatusUI(online, url) {
    if (online) {
        elements.serverStatus.classList.remove('offline');
        elements.serverStatus.classList.add('online');
        const shortUrl = url.replace(/^https?:\/\//, '').substring(0, 18);
        elements.serverStatus.querySelector('.status-text').innerHTML = `Online: <small>${shortUrl}...</small>`;
    } else {
        elements.serverStatus.classList.remove('online');
        elements.serverStatus.classList.add('offline');
        elements.serverStatus.querySelector('.status-text').textContent = 'Agente Offline';
    }
}

async function cargarPreguntas() {
    try {
        const res = await fetch('/api/preguntas');
        appState.preguntas = await res.json();
        renderPreguntas();
    } catch (err) {
        showToast('Error al cargar banco de preguntas.', 'error');
    }
}

async function cargarResultados() {
    try {
        const res = await fetch('/api/examenes/resultados');
        const data = await res.json();
        appState.resultados = data.resultados || {};
        renderResultados();
    } catch (err) {
        console.error('Error al cargar resultados:', err);
    }
}

// --- TAB ROUTING ---
function setupEventListeners() {
    elements.navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
    
    // Drop zone drag events
    const dropZone = elements.dropZoneRespuestas;
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });
    
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            elements.fileRespuestas.files = files;
            subirRespuestas(files[0]);
        }
    });
    
    dropZone.addEventListener('click', () => {
        elements.fileRespuestas.click();
    });
    
    elements.fileRespuestas.addEventListener('change', (e) => {
        if (e.target.files.length) {
            subirRespuestas(e.target.files[0]);
        }
    });
    
    // Iniciar corrección
    elements.btnIniciarCorreccion.addEventListener('click', iniciarCorreccionIA);
    
    // Banco de preguntas search & actions
    elements.filterPreguntas.addEventListener('input', renderPreguntas);
    
    elements.btnNuevaPregunta.addEventListener('click', () => {
        elements.formPregunta.reset();
        elements.conceptsRowsContainer.innerHTML = '';
        elements.modalPregunta.classList.add('active');
    });
    
    elements.closeModalPregunta.addEventListener('click', () => {
        elements.modalPregunta.classList.remove('active');
    });
    elements.btnCancelarPregunta.addEventListener('click', () => {
        elements.modalPregunta.classList.remove('active');
    });
    
    elements.btnAddConceptoRow.addEventListener('click', () => addConceptoRow());
    
    elements.formPregunta.addEventListener('submit', guardarPreguntaManual);
    
    // Preguntas CSV Upload
    elements.filePreguntas.addEventListener('change', (e) => {
        if (e.target.files.length) {
            subirPreguntasCSV(e.target.files[0]);
        }
    });
    
    // Resultados search & export
    elements.filterResultados.addEventListener('input', renderResultados);
    elements.btnExportarCsv.addEventListener('click', exportarResultadosCSV);
    
    // Modales close
    elements.closeModalDetalle.addEventListener('click', () => {
        elements.modalDetalleAlumno.classList.remove('active');
    });
    
    // Cierre al cliquear fuera del modal
    window.addEventListener('click', (e) => {
        if (e.target === elements.modalPregunta) {
            elements.modalPregunta.classList.remove('active');
        }
        if (e.target === elements.modalDetalleAlumno) {
            elements.modalDetalleAlumno.classList.remove('active');
        }
    });

    // Probar conexión
    if (elements.btnProbarConexion) {
        elements.btnProbarConexion.addEventListener('click', async () => {
            const url = elements.inputUrlLlm.value.trim();
            if (!url) {
                showToast('Ingrese una URL válida.', 'error');
                return;
            }
            elements.btnProbarConexion.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Probando...`;
            elements.btnProbarConexion.disabled = true;
            
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url_llm: url })
                });
                const data = await res.json();
                
                updateServerStatusUI(data.online, url);
                if (data.online) {
                    showToast('¡Conexión exitosa con el agente LLM!', 'success');
                } else {
                    showToast('El agente no responde en la URL ingresada.', 'error');
                }
            } catch (err) {
                showToast('Error al establecer conexión con esa URL.', 'error');
                updateServerStatusUI(false, '');
            } finally {
                elements.btnProbarConexion.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Probar`;
                elements.btnProbarConexion.disabled = false;
            }
        });
    }

    // Guardar configuración
    if (elements.btnGuardarConexion) {
        elements.btnGuardarConexion.addEventListener('click', async () => {
            const url = elements.inputUrlLlm.value.trim();
            if (!url) {
                showToast('Ingrese una URL válida.', 'error');
                return;
            }
            elements.btnGuardarConexion.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Guardando...`;
            elements.btnGuardarConexion.disabled = true;
            
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url_llm: url })
                });
                const data = await res.json();
                
                updateServerStatusUI(data.online, url);
                if (res.ok) {
                    showToast('URL del Agente configurada y guardada.', 'success');
                } else {
                    showToast('Error al guardar la URL.', 'error');
                }
            } catch (err) {
                showToast('Error al enviar la configuración.', 'error');
            } finally {
                elements.btnGuardarConexion.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Guardar`;
                elements.btnGuardarConexion.disabled = false;
            }
        });
    }
}

function switchTab(tabId) {
    appState.currentTab = tabId;
    elements.navBtns.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
    });
    
    elements.tabPanels.forEach(panel => {
        panel.classList.toggle('active', panel.id === `tab-${tabId}`);
    });
    
    if (tabId === 'preguntas') {
        cargarPreguntas();
    } else if (tabId === 'resultados') {
        cargarResultados();
    }
}

// --- MANAGE RESPUESTAS DE ESTUDIANTES ---

async function subirRespuestas(file) {
    elements.uploadStatus.className = 'status-alert hidden';
    elements.uploadStatus.innerHTML = '';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/api/examenes/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            // Error de validación estructurada
            let errorMsg = `<strong>La validación del CSV falló:</strong><br>`;
            if (data.detalles && Array.isArray(data.detalles)) {
                errorMsg += `<ul style="margin-left: 1.25rem; margin-top: 0.5rem; text-align: left;">`;
                data.detalles.slice(0, 5).forEach(err => {
                    errorMsg += `<li>${err}</li>`;
                });
                if (data.detalles.length > 5) {
                    errorMsg += `<li>... y otros ${data.detalles.length - 5} errores más.</li>`;
                }
                errorMsg += `</ul>`;
            } else {
                errorMsg += data.error || 'Formato inválido.';
            }
            
            elements.uploadStatus.className = 'status-alert error';
            elements.uploadStatus.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div>${errorMsg}</div>`;
            elements.btnIniciarCorreccion.disabled = true;
            elements.statTotal.textContent = '0';
            return;
        }
        
        elements.uploadStatus.className = 'status-alert success';
        elements.uploadStatus.innerHTML = `<i class="fa-solid fa-circle-check"></i> <div>Cargado con éxito: ${data.total_respuestas} respuestas de ${data.total_alumnos} alumnos listas para evaluar.</div>`;
        
        elements.statTotal.textContent = data.total_respuestas;
        elements.statProcesado.textContent = '0';
        elements.statErrores.textContent = '0';
        elements.progressFill.style.width = '0%';
        elements.progressPercent.textContent = '0%';
        
        elements.btnIniciarCorreccion.disabled = false;
        showToast('Respuestas cargadas y validadas.', 'success');
        
    } catch (err) {
        elements.uploadStatus.className = 'status-alert error';
        elements.uploadStatus.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div>Error al subir el archivo CSV.</div>`;
        showToast('Error de red al subir respuestas.', 'error');
    }
}

// --- PROCESAMIENTO CON IA ---

async function iniciarCorreccionIA() {
    elements.btnIniciarCorreccion.disabled = true;
    
    try {
        const res = await fetch('/api/examenes/corregir', { method: 'POST' });
        const data = await res.json();
        
        showToast('Corrección iniciada en segundo plano.', 'success');
        verificarEstadoCorreccion();
    } catch (err) {
        showToast('Error al iniciar la corrección.', 'error');
        elements.btnIniciarCorreccion.disabled = false;
    }
}

function verificarEstadoCorreccion() {
    if (appState.pollingInterval) clearInterval(appState.pollingInterval);
    
    appState.pollingInterval = setInterval(async () => {
        try {
            const res = await fetch('/api/examenes/estado');
            const status = await res.json();
            
            elements.statTotal.textContent = status.total;
            elements.statProcesado.textContent = status.procesado;
            elements.statErrores.textContent = status.errores;
            
            const percent = status.total > 0 ? Math.round((status.procesado / status.total) * 100) : 0;
            elements.progressFill.style.width = `${percent}%`;
            elements.progressPercent.textContent = `${percent}%`;
            
            if (status.status === 'running') {
                elements.btnIniciarCorreccion.disabled = true;
                elements.btnIniciarCorreccion.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Evaluando (${percent}%)`;
            } else {
                clearInterval(appState.pollingInterval);
                appState.pollingInterval = null;
                
                elements.btnIniciarCorreccion.innerHTML = `<i class="fa-solid fa-play"></i> Iniciar Corrección con IA`;
                elements.btnIniciarCorreccion.disabled = status.total === 0;
                
                if (status.status === 'completed') {
                    showToast('Corrección finalizada con éxito.', 'success');
                    cargarResultados();
                } else if (status.status === 'failed') {
                    showToast('El proceso terminó con fallos en la conexión al LLM.', 'error');
                    cargarResultados();
                }
            }
        } catch (err) {
            console.error('Error sondeando estado:', err);
        }
    }, 1000);
}

// --- QUESTIONS BANK ---

function renderPreguntas() {
    const filter = elements.filterPreguntas.value.toLowerCase();
    elements.questionsGrid.innerHTML = '';
    
    const preguntasList = Object.entries(appState.preguntas);
    const filtered = preguntasList.filter(([qId, data]) => {
        return qId.toLowerCase().includes(filter) || data.question_text.toLowerCase().includes(filter);
    });
    
    if (filtered.length === 0) {
        elements.questionsGrid.innerHTML = `<div class="loading-spinner">No se encontraron preguntas en el banco.</div>`;
        return;
    }
    
    filtered.forEach(([qId, qData]) => {
        const card = document.createElement('div');
        card.className = 'card glass-card question-card';
        card.innerHTML = `
            <div>
                <div class="question-card-header">
                    <span class="question-id">${qId}</span>
                    <span class="badge-count">${qData.conceptos ? qData.conceptos.length : 0} conceptos</span>
                </div>
                <p class="question-card-text">${qData.question_text}</p>
            </div>
            <div class="question-card-footer">
                <span>Pauta disponible</span>
                <span class="view-more-lbl">Ver Detalles <i class="fa-solid fa-chevron-right"></i></span>
            </div>
        `;
        
        card.addEventListener('click', () => verDetallePregunta(qId, qData));
        elements.questionsGrid.appendChild(card);
    });
}

function verDetallePregunta(qId, qData) {
    // Reutilizar modal pero de sólo lectura/visualización rápida
    elements.formPregunta.reset();
    document.getElementById('form-question-id').value = qId;
    document.getElementById('form-question-text').value = qData.question_text;
    document.getElementById('form-ideal-answer').value = qData.ideal_answer;
    
    elements.conceptsRowsContainer.innerHTML = '';
    if (qData.conceptos && qData.conceptos.length) {
        qData.conceptos.forEach(c => addConceptoRow(c.tag, c.descripcion));
    }
    
    elements.modalPregunta.querySelector('h3').textContent = `Editar Pregunta: ${qId}`;
    elements.modalPregunta.classList.add('active');
}

function addConceptoRow(tag = '', desc = '') {
    const row = document.createElement('div');
    row.className = 'concept-row';
    row.innerHTML = `
        <input type="text" placeholder="TAG" class="concept-tag-input" required value="${tag}">
        <input type="text" placeholder="Descripción del concepto" class="concept-desc-input" required value="${desc}">
        <button type="button" class="delete-row-btn"><i class="fa-solid fa-trash-can"></i></button>
    `;
    
    row.querySelector('.delete-row-btn').addEventListener('click', () => {
        row.remove();
    });
    
    elements.conceptsRowsContainer.appendChild(row);
}

async function guardarPreguntaManual(e) {
    e.preventDefault();
    
    const qId = document.getElementById('form-question-id').value.trim();
    const qText = document.getElementById('form-question-text').value.trim();
    const ideal = document.getElementById('form-ideal-answer').value.trim();
    
    const conceptos = [];
    const rows = elements.conceptsRowsContainer.querySelectorAll('.concept-row');
    rows.forEach(row => {
        const tag = row.querySelector('.concept-tag-input').value.trim();
        const desc = row.querySelector('.concept-desc-input').value.trim();
        if (tag && desc) {
            conceptos.push({ tag, descripcion: desc });
        }
    });
    
    const payload = {
        question_id: qId,
        question_text: qText,
        ideal_answer: ideal,
        conceptos: conceptos
    };
    
    try {
        const res = await fetch('/api/preguntas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            showToast('Pregunta guardada correctamente.', 'success');
            elements.modalPregunta.classList.remove('active');
            cargarPreguntas();
        } else {
            showToast('Error al guardar pregunta.', 'error');
        }
    } catch (err) {
        showToast('Error de conexión al guardar pregunta.', 'error');
    }
}

async function subirPreguntasCSV(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/api/preguntas/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (res.ok) {
            showToast(data.mensaje, 'success');
            cargarPreguntas();
        } else {
            showToast(data.detail || 'Error al subir preguntas.', 'error');
        }
    } catch (err) {
        showToast('Error de red al subir preguntas.', 'error');
    }
}

// --- RESULTS TABLE & DETAILS ---

function renderResultados() {
    const filter = elements.filterResultados.value.trim().toLowerCase();
    elements.tablaResultadosBody.innerHTML = '';
    
    const alumnosEntries = Object.entries(appState.resultados);
    const filtered = alumnosEntries.filter(([alumnoId]) => alumnoId.toLowerCase().includes(filter));
    
    // Calcular estadísticas globales
    const totalAlumnos = alumnosEntries.length;
    let sumaPromedios = 0;
    let totalAprobados = 0;
    
    alumnosEntries.forEach(([_, data]) => {
        sumaPromedios += data.promedio;
        if (data.promedio >= 4.0) totalAprobados++;
    });
    
    const promedioGeneral = totalAlumnos > 0 ? (sumaPromedios / totalAlumnos).toFixed(2) : '0.00';
    const tasaAprobacion = totalAlumnos > 0 ? Math.round((totalAprobados / totalAlumnos) * 100) : 0;
    
    elements.resTotalAlumnos.textContent = totalAlumnos;
    elements.resPromedioGeneral.textContent = promedioGeneral;
    elements.resAprobados.textContent = `${tasaAprobacion}%`;
    
    if (filtered.length === 0) {
        elements.tablaResultadosBody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-table">No se encontraron resultados de estudiantes.</td>
            </tr>
        `;
        return;
    }
    
    filtered.forEach(([alumnoId, data]) => {
        const row = document.createElement('tr');
        
        let badgeClass = 'insuficiente';
        let rango = 'INSUFICIENTE';
        if (data.promedio >= 9.0) {
            badgeClass = 'excelente';
            rango = 'EXCELENTE';
        } else if (data.promedio >= 7.0) {
            badgeClass = 'bueno';
            rango = 'BUENO';
        } else if (data.promedio >= 4.0) {
            badgeClass = 'aceptable';
            rango = 'ACEPTABLE';
        }
        
        row.innerHTML = `
            <td><strong>${alumnoId}</strong></td>
            <td>${data.respuestas ? data.respuestas.length : 0}</td>
            <td><span class="badge-grade ${badgeClass}">${data.promedio.toFixed(2)}</span></td>
            <td><span style="font-weight:600; font-size:0.8rem; letter-spacing:0.5px;">${rango}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm btn-ver-detalle" data-alumno="${alumnoId}">
                    <i class="fa-solid fa-magnifying-glass"></i> Detalle
                </button>
            </td>
        `;
        
        row.querySelector('.btn-ver-detalle').addEventListener('click', () => {
            verDetalleEstudiante(alumnoId, data);
        });
        
        elements.tablaResultadosBody.appendChild(row);
    });
}

function verDetalleEstudiante(alumnoId, data) {
    elements.detailAlumnoId.textContent = `Estudiante: ${alumnoId}`;
    elements.detailAlumnoPromedio.textContent = data.promedio.toFixed(2);
    
    elements.detailAnswersContainer.innerHTML = '';
    
    data.respuestas.forEach(ans => {
        const card = document.createElement('div');
        card.className = 'detail-card';
        
        let badgeClass = 'insuficiente';
        if (ans.nota_final >= 9) badgeClass = 'excelente';
        else if (ans.nota_final >= 7) badgeClass = 'bueno';
        else if (ans.nota_final >= 4) badgeClass = 'aceptable';
        
        // Concept tags html
        let conceptsHtml = '';
        if (ans.conceptos_evaluados && Object.keys(ans.conceptos_evaluados).length) {
            conceptsHtml = `<div class="concept-tags-container">`;
            Object.entries(ans.conceptos_evaluados).forEach(([tag, val]) => {
                const tagClass = val === 'sí' ? 'yes' : 'no';
                conceptsHtml += `
                    <div class="concept-tag-item">
                        <span class="badge-tag ${tagClass}">${val.toUpperCase()}</span>
                        <span>${tag}</span>
                    </div>
                `;
            });
            conceptsHtml += `</div>`;
        } else {
            conceptsHtml = `<p style="font-size:0.8rem; color:var(--text-muted);">No se detectaron conceptos para calificar.</p>`;
        }
        
        card.innerHTML = `
            <div class="detail-section">
                <h5 style="color: var(--accent-secondary)">Pregunta ${ans.question_id}</h5>
                <p style="font-weight: 500;">${ans.question_text || 'Detalle no disponible.'}</p>
            </div>
            
            <div class="detail-section">
                <h5>Respuesta de Referencia (Pauta)</h5>
                <p class="answer-box" style="color: var(--text-secondary); font-size: 0.85rem">${ans.ideal_answer || 'Sin respuesta ideal de cátedra.'}</p>
            </div>
            
            <div class="detail-section">
                <h5>Respuesta del Estudiante</h5>
                <p class="answer-box">${ans.student_answer}</p>
            </div>

            <div class="detail-section">
                <h5>Conceptos Clave Verificados</h5>
                ${conceptsHtml}
            </div>
            
            <div class="detail-meta-grid">
                <div class="detail-section">
                    <h5>Calificación IA</h5>
                    <div><span class="badge-grade ${badgeClass}">${ans.nota_final} / 10</span></div>
                </div>
                <div class="detail-section">
                    <h5>Rango Sugerido</h5>
                    <p style="font-weight: 700; font-size:0.9rem; color:var(--text-secondary)">${ans.rango_nota}</p>
                </div>
                <div class="detail-section">
                    <h5>Tiempo Ejecución</h5>
                    <p style="font-size:0.9rem; color:var(--text-muted)"><i class="fa-regular fa-clock"></i> ${ans.tiempo}s</p>
                </div>
            </div>
        `;
        
        elements.detailAnswersContainer.appendChild(card);
    });
    
    elements.modalDetalleAlumno.classList.add('active');
}

// --- EXPORT TO CSV (CLIENT SIDE) ---

function exportarResultadosCSV() {
    const alumnosEntries = Object.entries(appState.resultados);
    if (alumnosEntries.length === 0) {
        showToast('No hay resultados cargados para exportar.', 'error');
        return;
    }
    
    let csvContent = "data:text/csv;charset=utf-8,";
    // Encabezado del CSV
    csvContent += "alumno_id,promedio_general,preguntas_calificadas\n";
    
    alumnosEntries.forEach(([alumnoId, data]) => {
        csvContent += `${alumnoId},${data.promedio},${data.respuestas.length}\n`;
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "resultados_notas_utn_lis.csv");
    document.body.appendChild(link); // Required for FF
    
    link.click();
    document.body.removeChild(link);
    showToast('Notas exportadas como CSV.', 'success');
}

// --- UTILS: TOAST NOTIFICATIONS ---

function showToast(message, type = 'success') {
    elements.toast.className = 'toast';
    elements.toast.classList.add('active', type);
    elements.toast.innerHTML = type === 'success' 
        ? `<i class="fa-solid fa-circle-check" style="color:var(--color-excelente)"></i> <span>${message}</span>`
        : `<i class="fa-solid fa-circle-exclamation" style="color:var(--color-insuficiente)"></i> <span>${message}</span>`;
        
    setTimeout(() => {
        elements.toast.classList.remove('active');
    }, 3500);
}
