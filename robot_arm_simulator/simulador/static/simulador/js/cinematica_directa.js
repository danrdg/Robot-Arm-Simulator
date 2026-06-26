/**
 * cinematica_directa.js
 * ---------------------
 * Lógica de la página de cinemática directa.
 *
 */
 
let robotActual = null;  // datos del robot cargado actualmente

// Referencias al DOM
const selectorRobot = document.getElementById("selector-robot");
const panelArticulaciones = document.getElementById("panel-articulaciones");
const panelResultado = document.getElementById("panel-resultado");
const mensajeError = document.getElementById("mensaje-error");

// Inicialización
document.addEventListener("DOMContentLoaded", () => {
    // Inicializar el visualizador 3D
    Visualizador.inicializar("visualizador-3d");

    // Cargar robots personalizados desde localStorage y añadirlos al selector
    _cargarRobotsPersonalizados();

    // Cargar el primer robot al iniciar
    _cargarRobot(selectorRobot.value);

    // Escuchar cambios en el selector
    selectorRobot.addEventListener("change", () => {
        _cargarRobot(selectorRobot.value);
    });
});

/**
 * _cargarRobot
 * Obtiene los datos del robot seleccionado y genera los sliders.
 * @param {string} idRobot - ID del robot a cargar.
 */
function _cargarRobot(idRobot) {
    // Buscar robot en predefinidos o en localStorage
    if (idRobot === "__personalizado__") return;

    const robotsPredefinidos   = typeof ROBOTS_PREDEFINIDOS !== "undefined" ? ROBOTS_PREDEFINIDOS : {};
    const robotsPersonalizados = _obtenerRobotsGuardados();

    robotActual = robotsPredefinidos[idRobot] || robotsPersonalizados[idRobot] || null;

    if (!robotActual) {
        _mostrarError("No se encontró el robot seleccionado.");
        return;
    }

    _ocultarError();
    _generarSliders(robotActual);
    _llamarAPI();  // mostrar posición inicial
}

/**
 * _generarSliders
 * Crea dinámicamente los controles de ángulo para cada articulación.
 *
 * @param {Object} robot - Datos del robot con su lista de articulaciones.
 */
function _generarSliders(robot) {
    panelArticulaciones.innerHTML = "";

    robot.articulaciones.forEach((art, indice) => {
        

        const div = document.createElement("div");
        div.className = "grupo-slider";

        // Etiqueta con nombre y valor actual
        const etiqueta = document.createElement("div");
        etiqueta.className = "etiqueta-slider";

        const nombre = document.createElement("span");
        nombre.textContent = `q${indice + 1} (${art.tipo})`;
        const esRotatoria = art.tipo === "rotatoria";
        const unidad = esRotatoria ? "rad" : "m";
        const valorSpan = document.createElement("span");
        valorSpan.id = `valor-q${indice}`;
        valorSpan.textContent = `0.00 ${unidad}`;

        etiqueta.appendChild(nombre);
        etiqueta.appendChild(valorSpan);

        // Slider
        const slider = document.createElement("input");
        slider.type  = "range";
        slider.id = `slider-q${indice}`;
        slider.min = esRotatoria ? -3.14 : 0.2;
        slider.max = esRotatoria ?  3.14 : 1;
        slider.step = 0.01;
        slider.value = esRotatoria ? art.theta : art.d;

        valorSpan.textContent = `${parseFloat(slider.value).toFixed(2)} ${unidad}`;

        // Al mover el slider: actualizar label y llamar a la API
        slider.addEventListener("input", () => {
            valorSpan.textContent = `${parseFloat(slider.value).toFixed(2)} ${unidad}`;
            _llamarAPI();
        });

        div.appendChild(etiqueta);
        div.appendChild(slider);
        panelArticulaciones.appendChild(div);
    });
}

/**
 * _recogerDatosRobot
 * Lee los valores actuales de todos los sliders y construye el JSON del robot.
 *
 * @returns {Object} Datos del robot listos para enviar a la API.
 */
function _recogerDatosRobot() {
    const articulaciones = robotActual.articulaciones.map((art, indice) => {
        const slider = document.getElementById(`slider-q${indice}`);
        const valor  = slider ? parseFloat(slider.value) : 0;

        return {
            tipo:  art.tipo,
            theta: art.tipo === "rotatoria"  ? valor : art.theta,
            d: art.tipo === "prismatica" ? valor : art.d,
            a: art.a,
            alpha: art.alpha,
        };
    });

    return { nombre: robotActual.nombre, articulaciones };
}

/**
 * _llamarAPI
 * Envía los datos del robot al endpoint de cinemática directa y actualiza el visualizador.
 */
async function _llamarAPI() {
    if (!robotActual) return;

    const datosRobot = _recogerDatosRobot();

    try {
        const respuesta = await fetch("/api/cinematica-directa/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datosRobot),
        });

        const resultado = await respuesta.json();

        if (!resultado.exito) {
            _mostrarError(resultado.error || "Error desconocido del servidor.");
            return;
        }

        _ocultarError();

        // Actualizar el visualizador 3D con las nuevas posiciones y orientación del efector
        Visualizador.dibujarRobot(resultado.articulaciones, resultado.orientacion_efector);
        // Actualizar valores de parámetros D-H en tiempo real
        _actualizarTablaDH(_recogerDatosRobot().articulaciones);

        // Mostrar posición del efector
        const pos = resultado.posicion_efector;
        document.getElementById("res-x").textContent = pos[0].toFixed(4);
        document.getElementById("res-y").textContent = pos[1].toFixed(4);
        document.getElementById("res-z").textContent = pos[2].toFixed(4);
        panelResultado.style.display = "block";

    } catch (err) {
        _mostrarError("Error de red al contactar con el servidor.");
    }
}


function _mostrarError(mensaje) {
    mensajeError.textContent = mensaje;
    mensajeError.style.display = "block";
}

function _ocultarError() {
    mensajeError.style.display = "none";
}

function _obtenerRobotsGuardados() {
    try {
        return JSON.parse(localStorage.getItem("robots_personalizados") || "{}");
    } catch {
        return {};
    }
}

function _cargarRobotsPersonalizados() {
    const robots = _obtenerRobotsGuardados();
    Object.entries(robots).forEach(([id, robot]) => {
        const opcion = document.createElement("option");
        opcion.value = id;
        opcion.textContent = `★ ${robot.nombre}`;
        selectorRobot.appendChild(opcion);
    });
}

/**
 * _actualizarTablaDH
 * Reconstruye la tabla de parámetros D-H con los valores actuales del robot.
 * La variable articular activa de cada fila se resalta visualmente.
 * @param {Array} articulaciones - Lista de articulaciones con sus parámetros DH actuales.
 */
function _actualizarTablaDH(articulaciones) {
    const cuerpo = document.getElementById("dh-filas");
    const panel = document.getElementById("panel-dh");

    cuerpo.innerHTML = "";

    articulaciones.forEach((art, i) => {
        const esRotatoria = art.tipo === "rotatoria";
        const fila = document.createElement("tr");

        // Resaltar en azul la celda de la variable activa (θ o d)
        const celdaTheta = `<td class="${esRotatoria  ? "dh-variable" : ""}">${art.theta.toFixed(3)}</td>`;
        const celdaD = `<td class="${!esRotatoria ? "dh-variable" : ""}">${art.d.toFixed(3)}</td>`;

        fila.innerHTML = `
            <td>${i + 1}</td>
            <td>${art.tipo}</td>
            ${celdaTheta}
            ${celdaD}
            <td>${art.a.toFixed(3)}</td>
            <td>${art.alpha.toFixed(3)}</td>
        `;
        cuerpo.appendChild(fila);
    });

    panel.style.display = "block";
}