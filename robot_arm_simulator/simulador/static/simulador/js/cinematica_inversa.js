/**
/**
 * cinematica_inversa.js
 * ---------------------
 * Lógica de la página de cinemática inversa.
 */


let robotActual = null;

//  Referencias al DOM 
const selectorRobot = document.getElementById("selector-robot");
const btnCalcular = document.getElementById("btn-calcular");
const panelResultado = document.getElementById("panel-resultado");
const estadoConvergencia = document.getElementById("estado-convergencia");
const resError = document.getElementById("res-error");
const resIter = document.getElementById("res-iter");
const listaArticulares  = document.getElementById("lista-articulares");
const mensajeError  = document.getElementById("mensaje-error");

// Inicialización
document.addEventListener("DOMContentLoaded", () => {
    Visualizador.inicializar("visualizador-3d");

    _cargarRobotsPersonalizados();
    _seleccionarRobot(selectorRobot.value);

    selectorRobot.addEventListener("change", () => {
        _seleccionarRobot(selectorRobot.value);
    });

    btnCalcular.addEventListener("click", _calcularInversa);
});

/**
 * _seleccionarRobot
 * Carga los datos del robot seleccionado en el estado.

 * @param {string} idRobot - ID del robot seleccionado.
 */
function _seleccionarRobot(idRobot) {
    if (idRobot === "__personalizado__") return;

    const robotsPredefinidos = typeof ROBOTS_PREDEFINIDOS !== "undefined" ? ROBOTS_PREDEFINIDOS : {};
    const robotsPersonalizados = _obtenerRobotsGuardados();

    robotActual = robotsPredefinidos[idRobot] || robotsPersonalizados[idRobot] || null;

    if (!robotActual) {
        _mostrarError("No se ha encontrado el robot seleccionado.");
        return;
    }

    _ocultarError();

    // Ocultar paneles de la configuración anterior
    panelResultado.style.display = "none";
    document.getElementById("panel-dh").style.display = "none";
    document.getElementById("dh-filas").innerHTML = "";  

    // Mostrar la configuración inicial del robot
    _llamarDirectaYDibujar(robotActual.articulaciones);
}

/**
 * _llamarDirectaYDibujar
 * Llama a la API de cinemática directa para dibujar la pose actual del robot.
 *
 * @param {Array} articulaciones - Lista de articulaciones con sus parámetros DH.
 */
async function _llamarDirectaYDibujar(articulaciones) {
    const datosRobot = { nombre: robotActual.nombre, articulaciones };

    try {
        const respuesta = await fetch("/api/cinematica-directa/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datosRobot),
        });
        const resultado = await respuesta.json();

        if (resultado.exito) {
            Visualizador.dibujarRobot(resultado.articulaciones, resultado.orientacion_efector);
        }
    } catch {
        // Error silencioso: el visualizador simplemente no se actualiza
    }
}

/**
 * _formatearValorArticular
 * Devuelve la cadena de texto con el valor y la unidad correcta según
 * el tipo de articulación:

 *
 * @param {number} valor - Valor articular de la solución.
 * @param {string} tipo - Tipo de articulación: "rotatoria" o "prismatica".
 * @returns {string}
 */
function _formatearValorArticular(valor, tipo) {
    if (tipo === "prismatica") {
        return `${valor.toFixed(4)} m`;
    }
    const grados = (valor * 180 / Math.PI).toFixed(2);
    return `${valor.toFixed(4)} rad (${grados}°)`;
}

/**
 * _calcularInversa
 * Lee el objetivo del formulario, llama a la API de cinemática inversa y actualiza el visualizador con el resultado.
 */
async function _calcularInversa() {
    if (!robotActual) {
        _mostrarError("Selecciona un robot primero.");
        return;
    }

    // Leer posición objetivo
    const x = parseFloat(document.getElementById("objetivo-x").value);
    const y = parseFloat(document.getElementById("objetivo-y").value);
    const z = parseFloat(document.getElementById("objetivo-z").value);

    if ([x, y, z].some(isNaN)) {
        _mostrarError("Introduce valores numéricos válidos para X, Y y Z.");
        return;
    }

    _ocultarError();
    btnCalcular.disabled = true;
    btnCalcular.textContent = "Calculando…";

    const cuerpo = {
        robot:    { nombre: robotActual.nombre, articulaciones: robotActual.articulaciones },
        objetivo: [x, y, z],
    };

    try {
        const respuesta = await fetch("/api/cinematica-inversa/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(cuerpo),
        });

        const resultado = await respuesta.json();

        if (!resultado.exito) {
            _mostrarError(resultado.error || "Error en el servidor.");
            return;
        }

        // Actualizar visualizador
        // Recalcular cinemática directa con los valores articulares solución
        const articulacionesSolucion = robotActual.articulaciones.map((art, i) => ({
            ...art,
            theta: art.tipo === "rotatoria"  ? resultado.valores_articulares[i] : art.theta,
            d: art.tipo === "prismatica" ? resultado.valores_articulares[i] : art.d,
        }));

        await _llamarDirectaYDibujar(articulacionesSolucion);

        // Marcar la posición objetivo en la escena
        Visualizador.marcarObjetivo([x, y, z]);
        // Mostrar valores de parametrización DH
        _actualizarTablaDH(robotActual.articulaciones, resultado.valores_articulares);

        // Mostrar resultados
        const converge = resultado["converge"];
        estadoConvergencia.textContent = converge ? "✓ Converge" : "✖ No converge";
        estadoConvergencia.className = converge ? "convergido"  : "no-convergido";

        // El error final es una distancia cartesiana: se expresa en metros
        resError.textContent = `${resultado.error_final.toFixed(6)} m`;
        resIter.textContent = resultado.iteraciones_usadas;

        // Lista de valores articulares con unidades según el tipo de cada articulación
        listaArticulares.innerHTML = "";

        resultado.valores_articulares.forEach((val, i) => {
            const tipo = robotActual.articulaciones[i]?.tipo ?? "rotatoria";
            const li = document.createElement("li");
            li.innerHTML = `q${i + 1}: <span>${_formatearValorArticular(val, tipo)}</span>`;
            listaArticulares.appendChild(li);
        });

        panelResultado.style.display = "block";

    } catch (err) {
        _mostrarError("Error de red al contactar con el servidor.");
    } finally {
        btnCalcular.disabled    = false;
        btnCalcular.textContent = "Calcular";
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
 * Reconstruye la tabla de parámetros D-H con los valores articulares dados.
 * La variable activa de cada articulación se resalta visualmente.
 *
 * @param {Array} articulaciones  - Definición base del robot (tipo, a, alpha, etc.).
 * @param {Array} valoresSolucion - Valores articulares calculados por la cinemática inversa.
 */
function _actualizarTablaDH(articulaciones, valoresSolucion) {
    const cuerpo = document.getElementById("dh-filas");
    const panel = document.getElementById("panel-dh");

    cuerpo.innerHTML = "";

    articulaciones.forEach((art, i) => {
        const esRotatoria = art.tipo === "rotatoria";
        const valorQ = valoresSolucion[i] ?? 0;

        // El valor de la variable activa viene de la solución; los valores fijos del robot
        const theta = esRotatoria  ? valorQ : art.theta;
        const d = !esRotatoria ? valorQ : art.d;

        const celdaTheta = `<td class="${esRotatoria  ? "dh-variable" : ""}">${theta.toFixed(3)}</td>`;
        const celdaD = `<td class="${!esRotatoria ? "dh-variable" : ""}">${d.toFixed(3)}</td>`;

        const fila = document.createElement("tr");
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