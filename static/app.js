// --- STATE MANAGEMENT ---
let appState = {
    preguntas: {},
    respuestasCargadasCount: 0,
    resultados: {},
    pollingInterval: null,
    currentTab: 'dashboard',
    maeChartInstance: null
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
    btnGenerarConceptosIa: document.getElementById('btn-generar-conceptos-ia'),
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
    verificarEstadoComparacion(); // Por si quedó corriendo la comparación en vivo
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
    elements.btnGenerarConceptosIa.addEventListener('click', generarConceptosConIa);

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

    // Event listeners para la pestaña de Comparación (Opción A: Estático)
    const dropZoneComp = document.getElementById('drop-zone-comparar');
    const fileComp = document.getElementById('file-comparar');
    if (dropZoneComp && fileComp) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZoneComp.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZoneComp.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZoneComp.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZoneComp.classList.remove('dragover');
            }, false);
        });
        
        dropZoneComp.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                fileComp.files = files;
                ejecutarComparacion(files[0]);
            }
        });
        
        dropZoneComp.addEventListener('click', () => {
            fileComp.click();
        });
        
        fileComp.addEventListener('change', (e) => {
            if (e.target.files.length) {
                ejecutarComparacion(e.target.files[0]);
            }
        });
    }

    // Event listeners para la pestaña de Comparación (Opción B: En Vivo)
    const dropZoneVivo = document.getElementById('drop-zone-vivo');
    const fileVivo = document.getElementById('file-vivo');
    const btnIniciarVivo = document.getElementById('btn-iniciar-vivo');
    
    if (dropZoneVivo && fileVivo) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZoneVivo.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZoneVivo.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZoneVivo.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZoneVivo.classList.remove('dragover');
            }, false);
        });
        
        dropZoneVivo.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length) {
                fileVivo.files = files;
                subirDatasetVivo(files[0]);
            }
        });
        
        dropZoneVivo.addEventListener('click', () => {
            fileVivo.click();
        });
        
        fileVivo.addEventListener('change', (e) => {
            if (e.target.files.length) {
                subirDatasetVivo(e.target.files[0]);
            }
        });
    }
    
    if (btnIniciarVivo) {
        btnIniciarVivo.addEventListener('click', iniciarEvaluacionVivo);
    }
    const btnCancelarVivo = document.getElementById('btn-cancelar-vivo');
    if (btnCancelarVivo) {
        btnCancelarVivo.addEventListener('click', cancelarEvaluacionVivo);
    }
    const btnExportarComparacion = document.getElementById('btn-exportar-comparacion');
    if (btnExportarComparacion) {
        btnExportarComparacion.addEventListener('click', exportarComparacionCSV);
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
    } else if (tabId === 'comparacion') {
        cargarResultadosComparacion();
        cargarHistorialMAE();
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

async function generarConceptosConIa() {
    const qText = document.getElementById('form-question-text').value.trim();
    const ideal = document.getElementById('form-ideal-answer').value.trim();

    if (!qText || !ideal) {
        showToast('Complete el Enunciado y la Respuesta de Referencia para generar las etiquetas.', 'error');
        return;
    }

    const btnGenerar = elements.btnGenerarConceptosIa;
    const originalText = btnGenerar.innerHTML;
    btnGenerar.disabled = true;
    btnGenerar.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generando...`;

    try {
        const res = await fetch('/api/preguntas/generar-conceptos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_text: qText, ideal_answer: ideal })
        });

        if (res.ok) {
            const data = await res.json();
            if (data.conceptos && data.conceptos.length > 0) {
                elements.conceptsRowsContainer.innerHTML = '';
                data.conceptos.forEach(c => addConceptoRow(c.tag, c.descripcion));
                showToast('Etiquetas generadas con IA exitosamente.', 'success');
            } else {
                showToast('No se pudieron generar etiquetas para esta respuesta.', 'error');
            }
        } else {
            showToast('Error al generar etiquetas con IA.', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Error de conexión al generar etiquetas.', 'error');
    } finally {
        btnGenerar.disabled = false;
        btnGenerar.innerHTML = originalText;
    }
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
            const data = await res.json();
            if (conceptos.length === 0 && data.conceptos && data.conceptos.length > 0) {
                showToast(`Pregunta guardada. Se generaron ${data.conceptos.length} etiquetas con IA.`, 'success');
            } else {
                showToast('Pregunta guardada correctamente.', 'success');
            }
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

// --- METODOS DE COMPARACION (ESTATICO Y EN VIVO) ---

async function ejecutarComparacion(file) {
    const statusDiv = document.getElementById('comparar-status');
    statusDiv.className = 'status-alert hidden';
    statusDiv.innerHTML = '';
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/api/examenes/comparar', {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            statusDiv.className = 'status-alert error';
            statusDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div>${data.detail || 'Error al procesar la comparación.'}</div>`;
            return;
        }
        
        statusDiv.className = 'status-alert success';
        statusDiv.innerHTML = `<i class="fa-solid fa-circle-check"></i> <div>Comparación exitosa: ${data.total_comparados} respuestas emparejadas y evaluadas.</div>`;
        
        mostrarMetricasComparacion(data);
        
    } catch (err) {
        statusDiv.className = 'status-alert error';
        statusDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div>Error de conexión al procesar la comparación.</div>`;
        showToast('Error de red al comparar resultados.', 'error');
    }
}

async function subirDatasetVivo(file) {
    const statusDiv = document.getElementById('vivo-status');
    const btnIniciar = document.getElementById('btn-iniciar-vivo');
    const progContainer = document.getElementById('vivo-progress-container');
    
    statusDiv.className = 'status-alert hidden';
    statusDiv.innerHTML = '';
    progContainer.style.display = 'none';
    btnIniciar.disabled = true;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await fetch('/api/examenes/comparar-upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            statusDiv.className = 'status-alert error';
            statusDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div>${data.detail || 'Error al subir el dataset.'}</div>`;
            return;
        }
        
        statusDiv.className = 'status-alert success';
        statusDiv.innerHTML = `<i class="fa-solid fa-circle-check"></i> <div>Dataset cargado: ${data.total_registros} respuestas listas para corregir y comparar.</div>`;
        
        btnIniciar.disabled = false;
        showToast('Dataset cargado para evaluar.', 'success');
        
    } catch (err) {
        statusDiv.className = 'status-alert error';
        statusDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <div>Error de conexión al subir el dataset.</div>`;
        showToast('Error de red al subir dataset.', 'error');
    }
}

async function iniciarEvaluacionVivo() {
    const btnIniciar = document.getElementById('btn-iniciar-vivo');
    btnIniciar.disabled = true;
    
    try {
        const res = await fetch('/api/examenes/comparar-corregir', { method: 'POST' });
        const data = await res.json();
        
        showToast('Evaluación y comparación en vivo iniciada.', 'success');
        
        document.getElementById('btn-cancelar-vivo').style.display = 'inline-block';
        document.getElementById('btn-cancelar-vivo').disabled = false;
        document.getElementById('btn-cancelar-vivo').innerHTML = `<i class="fa-solid fa-ban"></i> Cancelar`;
        document.getElementById('vivo-progress-container').style.display = 'block';
        verificarEstadoComparacion();
    } catch (err) {
        showToast('Error al iniciar la evaluación.', 'error');
        btnIniciar.disabled = false;
    }
}
function verificarEstadoComparacion() {
    if (appState.pollingIntervalComparacion) clearInterval(appState.pollingIntervalComparacion);

    appState.pollingIntervalComparacion = setInterval(async () => {
        try {
            const res = await fetch('/api/examenes/comparar-estado');
            const status = await res.json();
            
            document.getElementById('vivo-processed').textContent = status.procesado;
            document.getElementById('vivo-total').textContent = status.total;
            document.getElementById('vivo-errors').textContent = status.errores;
            document.getElementById('vivo-running-mae').textContent = status.mae.toFixed(2);
            
            const percent = status.total > 0 ? Math.round((status.procesado / status.total) * 100) : 0;
            document.getElementById('vivo-progress-fill').style.width = `${percent}%`;
            document.getElementById('vivo-percent').textContent = `${percent}%`;
            
            // Render chart and table in real-time if comparisons are available
            if (status.comparaciones && status.comparaciones.length > 0) {
                document.getElementById('comparar-chart-card').style.display = 'block';
                renderMaeChart(status.comparaciones);
                
                document.getElementById('comparar-table-card').style.display = 'block';
                renderTablaComparacionBody(status.comparaciones);
            }
            
            if (status.status === 'running') {
                document.getElementById('btn-iniciar-vivo').innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Evaluando (${percent}%)`;
                document.getElementById('btn-iniciar-vivo').disabled = true;
                document.getElementById('btn-cancelar-vivo').style.display = 'inline-block';
                document.getElementById('btn-cancelar-vivo').disabled = false;
            } else if (status.status === 'cancelling') {
                document.getElementById('btn-iniciar-vivo').innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Cancelando...`;
                document.getElementById('btn-iniciar-vivo').disabled = true;
                document.getElementById('btn-cancelar-vivo').style.display = 'inline-block';
                document.getElementById('btn-cancelar-vivo').disabled = true;
                document.getElementById('btn-cancelar-vivo').innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Cancelando...`;
            } else {
                clearInterval(appState.pollingIntervalComparacion);
                appState.pollingIntervalComparacion = null;

                document.getElementById('btn-iniciar-vivo').innerHTML = `<i class="fa-solid fa-play"></i> Iniciar Evaluación en Vivo`;
                document.getElementById('btn-iniciar-vivo').disabled = false;
                document.getElementById('btn-cancelar-vivo').style.display = 'none';
                
                if (status.status === 'completed') {
                    showToast('Evaluación en vivo completada.', 'success');
                    cargarResultadosComparacion();
                } else if (status.status === 'failed') {
                    showToast('La evaluación terminó con algunos fallos de conexión.', 'error');
                    cargarResultadosComparacion();
                } else if (status.status === 'cancelled') {
                    showToast('La evaluación en vivo fue cancelada. Mostrando resultados parciales.', 'error');
                    cargarResultadosComparacion();
                }
            }
        } catch (err) {
            console.error('Error sondeando estado de comparación:', err);
        }
    }, 1000);
}

async function cancelarEvaluacionVivo() {
    const btnCancelar = document.getElementById('btn-cancelar-vivo');
    btnCancelar.disabled = true;
    btnCancelar.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Cancelando...`;
    
    try {
        const res = await fetch('/api/examenes/comparar-cancelar', { method: 'POST' });
        if (res.ok) {
            showToast('Cancelación solicitada.', 'success');
        } else {
            const data = await res.json();
            showToast(data.detail || 'Error al cancelar la evaluación.', 'error');
            btnCancelar.disabled = false;
            btnCancelar.innerHTML = `<i class="fa-solid fa-ban"></i> Cancelar`;
        }
    } catch (err) {
        showToast('Error de red al intentar cancelar.', 'error');
        btnCancelar.disabled = false;
        btnCancelar.innerHTML = `<i class="fa-solid fa-ban"></i> Cancelar`;
    }
}

async function cargarResultadosComparacion() {
    try {
        const res = await fetch('/api/examenes/comparar-resultados');
        const data = await res.json();
        appState.resultadosComparacion = data;
        mostrarMetricasComparacion(data);
    } catch (err) {
        showToast('Error al obtener los resultados de comparación.', 'error');
    }
}

// --- MAE EVOLUTION CHART & DETAIL TABLE ---
function renderMaeChart(comparaciones) {
    const canvas = document.getElementById('final-mae-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    if (appState.maeChartInstance) {
        appState.maeChartInstance.destroy();
    }
    
    const labels = comparaciones.map((_, index) => `#${index + 1}`);
    const dataPoints = comparaciones.map(c => c.running_mae !== undefined ? c.running_mae : 0.0);
    const questionIds = comparaciones.map(c => c.question_id);
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 250);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.35)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.00)');
    
    appState.maeChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'MAE Acumulado',
                data: dataPoints,
                borderColor: '#818cf8',
                borderWidth: 3,
                pointBackgroundColor: '#6366f1',
                pointBorderColor: '#ffffff',
                pointHoverRadius: 6,
                pointRadius: dataPoints.length > 50 ? 0 : 4,
                fill: true,
                backgroundColor: gradient,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        title: function(context) {
                            const idx = context[0].dataIndex;
                            return `Caso ${idx + 1}: ${questionIds[idx]}`;
                        },
                        label: function(context) {
                            return `MAE: ${context.parsed.y.toFixed(3)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', borderColor: 'transparent' },
                    ticks: { color: '#94a3b8', font: { family: 'Outfit, sans-serif' } }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', borderColor: 'transparent' },
                    ticks: { color: '#94a3b8', font: { family: 'Outfit, sans-serif' } },
                    suggestedMin: 0
                }
            }
        }
    });
}

function renderTablaComparacionBody(comparaciones) {
    const tableBody = document.getElementById('tabla-comparacion-body');
    if (!tableBody) return;
    tableBody.innerHTML = '';
    
    comparaciones.forEach(c => {
        const tr = document.createElement('tr');
        const diffClass = c.diff === 0 ? 'color: var(--color-excelente); font-weight:700;' 
                         : Math.abs(c.diff) <= 1 ? 'color: var(--color-bueno); font-weight:600;' 
                         : Math.abs(c.diff) <= 2 ? 'color: var(--color-aceptable); font-weight:600;'
                         : 'color: var(--color-insuficiente); font-weight:600;';
        
        let algoText = 'Pesos';
        let algoStyle = 'background:rgba(245, 158, 11, 0.08); border:1px solid rgba(245, 158, 11, 0.2); color:#fbbf24;';
        if (c.usó_promedio === true) {
            algoText = 'Promedio';
            algoStyle = 'background:rgba(16, 185, 129, 0.08); border:1px solid rgba(16, 185, 129, 0.2); color:#34d399;';
        } else if (c.usó_promedio === null) {
            algoText = 'N/A';
            algoStyle = 'background:rgba(255,255,255,0.03); border:1px solid var(--border-glass); color:var(--text-secondary);';
        }

        tr.innerHTML = `
            <td><strong>${c.question_id}</strong></td>
            <td style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${c.student_answer_short}</td>
            <td><span class="badge-grade" style="background:rgba(255,255,255,0.03); border:1px solid var(--border-glass); color:var(--text-primary); font-weight:600;">${c.teacher_grade}</span></td>
            <td><span class="badge-grade" style="background:rgba(99, 102, 241, 0.08); border:1px solid rgba(99, 102, 241, 0.2); color:#818cf8; font-weight:600;">${c.agent_grade}</span></td>
            <td><span class="badge-grade" style="${algoStyle} font-weight:600;">${algoText}</span></td>
            <td><span style="${diffClass}">${c.diff > 0 ? '+' : ''}${c.diff}</span></td>
            <td><strong style="color: var(--accent-secondary); font-weight:600;">${c.running_mae !== undefined ? c.running_mae.toFixed(2) : '-'}</strong></td>
        `;
        tableBody.appendChild(tr);
    });
}

function mostrarMetricasComparacion(data) {
    // Actualizar Tarjetas de Métricas
    document.getElementById('metric-mae').textContent = data.mae.toFixed(2);
    document.getElementById('metric-mae-menor-2').textContent = data.mae_menor_2 !== undefined ? data.mae_menor_2.toFixed(2) : '-';
    document.getElementById('metric-mae-mayor-2').textContent = data.mae_mayor_2 !== undefined ? data.mae_mayor_2.toFixed(2) : '-';
    document.getElementById('metric-bias').textContent = data.bias > 0 ? `+${data.bias.toFixed(2)}` : data.bias.toFixed(2);
    document.getElementById('metric-exact').textContent = `${data.pct_exacto}%`;
    document.getElementById('metric-tolerance').textContent = `${data.pct_tolerancia}%`;
    
    document.getElementById('metrics-placeholder').style.display = 'none';
    document.getElementById('comparar-metrics-grid').style.display = 'grid';

    // Actualizar Matriz de Confusión de Aprobación
    if (data.confusion_matrix) {
        const cm = data.confusion_matrix;
        document.getElementById('metric-cm-tp').textContent = `${cm.tp} (${cm.tp_pct}%)`;
        document.getElementById('metric-cm-fn').textContent = `${cm.fn} (${cm.fn_pct}%)`;
        document.getElementById('metric-cm-fp').textContent = `${cm.fp} (${cm.fp_pct}%)`;
        document.getElementById('metric-cm-tn').textContent = `${cm.tn} (${cm.tn_pct}%)`;
        document.getElementById('metric-cm-accuracy').textContent = `${cm.accuracy}%`;
        document.getElementById('metric-cm-recall').textContent = `${cm.recall}%`;
        document.getElementById('confusion-matrix-container').style.display = 'block';
    } else {
        document.getElementById('confusion-matrix-container').style.display = 'none';
    }
    
    // Renderizar barra de distribución de errores
    const distBars = document.getElementById('error-dist-bars');
    distBars.innerHTML = '';
    
    const maxCount = Math.max(...Object.values(data.distribucion_errores), 1);
    
    Object.entries(data.distribucion_errores).forEach(([diff, count]) => {
        const percentage = Math.round((count / data.total_comparados) * 100);
        const widthPct = Math.round((count / maxCount) * 100);
        
        let barColor = 'rgba(255, 255, 255, 0.2)';
        const diffVal = parseInt(diff);
        if (diffVal === 0) barColor = 'var(--color-excelente)';
        else if (Math.abs(diffVal) <= 1) barColor = 'var(--color-bueno)';
        else if (Math.abs(diffVal) <= 2) barColor = 'var(--color-aceptable)';
        else barColor = 'var(--color-insuficiente)';
        
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.alignItems = 'center';
        row.style.gap = '1rem';
        row.style.fontSize = '0.85rem';
        row.innerHTML = `
            <span style="min-width: 60px; font-weight:600; text-align:right;">${diffVal > 0 ? '+' : ''}${diffVal} pts:</span>
            <div style="flex-grow: 1; height: 12px; background: rgba(255,255,255,0.05); border-radius: 6px; overflow: hidden;">
                <div style="width: ${widthPct}%; height: 100%; background: ${barColor}; border-radius: 6px;"></div>
            </div>
            <span style="min-width: 100px; color: var(--text-secondary);">${count} casos (${percentage}%)</span>
        `;
        distBars.appendChild(row);
    });
    
    // Renderizar tabla de detalle
    renderTablaComparacionBody(data.comparaciones);
    
    // Mostrar y renderizar gráfico de evolución
    document.getElementById('comparar-chart-card').style.display = 'block';
    renderMaeChart(data.comparaciones);
    
    // Cargar historial de MAEs
    cargarHistorialMAE();
    
    document.getElementById('comparar-table-card').style.display = 'block';
    showToast('Métricas de comparación cargadas.', 'success');
}

function exportarComparacionCSV() {
    const data = appState.resultadosComparacion;
    if (!data || !data.comparaciones || data.comparaciones.length === 0) {
        showToast('No hay resultados de comparación para exportar.', 'error');
        return;
    }
    
    // Generar cabeceras y filas del CSV con el desglose de los 3 experimentos
    let csvContent = "\uFEFF"; // BOM para soportar caracteres utf-8 en Excel
    csvContent += "Pregunta ID,Respuesta estudiante,Nota Profesor,Nota Agente (Ensamble),Diferencia,Rango de nota,Nota Conceptos (Exp 1),Nota Rango (Exp 2),Nota Directa (Exp 3)\n";
    
    data.comparaciones.forEach(c => {
        const fullAnswer = c.student_answer || c.student_answer_short || "";
        const studentAnsEscaped = `"${fullAnswer.replace(/"/g, '""')}"`;
        
        // Obtener las notas del desglose si están disponibles
        const nConceptos = c.nota_conceptos !== undefined ? c.nota_conceptos : "";
        const nRango = c.nota_rango !== undefined ? c.nota_rango : "";
        const nDirecta = c.nota_directa !== undefined ? c.nota_directa : "";

        const row = [
            c.question_id,
            studentAnsEscaped,
            c.teacher_grade,
            c.agent_grade,
            c.diff,
            c.rango_nota || "",
            nConceptos,
            nRango,
            nDirecta
        ].join(",");
        csvContent += row + "\n";
    });
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `resultados_comparacion_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Archivo CSV exportado con éxito.', 'success');
}

async function cargarHistorialMAE() {
    try {
        const res = await fetch('/api/examenes/comparar-historial');
        if (!res.ok) throw new Error('Error al cargar historial');
        const historial = await res.json();
        
        const tbody = document.getElementById('tabla-historial-mae-body');
        tbody.innerHTML = '';
        
        if (historial.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-secondary);">No hay historial registrado aún.</td></tr>`;
            return;
        }
        
        historial.forEach(h => {
            const tr = document.createElement('tr');
            
            // Origen con badge
            const badgeStyle = h.origen === 'live' 
                ? 'background:rgba(99, 102, 241, 0.08); border:1px solid rgba(99, 102, 241, 0.2); color:#818cf8;'
                : 'background:rgba(139, 92, 246, 0.08); border:1px solid rgba(139, 92, 246, 0.2); color:#a78bfa;';
            const labelText = h.origen === 'live' ? 'En Vivo' : h.filename;
            
            // Color para MAE total
            const maeColor = h.mae <= 1.0 ? '#34d399' : (h.mae <= 1.5 ? '#a7f3d0' : (h.mae <= 2.0 ? '#fbbf24' : '#f87171'));
            
            tr.innerHTML = `
                <td><small>${h.timestamp}</small></td>
                <td><span class="badge-grade" style="${badgeStyle}">${labelText}</span></td>
                <td>${h.total_casos}</td>
                <td><strong style="color: ${maeColor}; font-size:1rem;">${h.mae.toFixed(2)}</strong></td>
                <td><span style="color:#a7f3d0; font-weight:600;">${h.mae_menor_2 !== undefined ? h.mae_menor_2.toFixed(2) : '-'}</span></td>
                <td><span style="color:#fca5a5; font-weight:600;">${h.mae_mayor_2 !== undefined ? h.mae_mayor_2.toFixed(2) : '-'}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error cargando historial de MAE:", e);
    }
}

async function limpiarHistorialMAE() {
    if (!confirm('¿Estás seguro de que deseas vaciar el historial de MAE?')) return;
    try {
        const res = await fetch('/api/examenes/comparar-historial/clear', { method: 'POST' });
        if (!res.ok) throw new Error('Error al limpiar historial');
        showToast('Historial de MAE eliminado.', 'success');
        cargarHistorialMAE();
    } catch (e) {
        showToast('Error al limpiar el historial.', 'error');
    }
}

