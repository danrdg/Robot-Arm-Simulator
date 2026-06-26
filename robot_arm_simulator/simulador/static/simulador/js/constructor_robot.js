/**
 * constructor_robot.js
 * --------------------
 * Lógica de la página de construcción de robots personalizados.
 *
 */

const numArticulaciones = document.getElementById("num-articulaciones");
const btnGenerar = document.getElementById("btn-generar");
const tablaDHContenedor = document.getElementById("tabla-dh-contenedor");
const filasArticulaciones = document.getElementById("filas-articulaciones");
const btnGuardar = document.getElementById("btn-guardar");
const listaRobotsGuardados = document.getElementById("lista-robots-guardados");
const seccionRobotsGuardados = document.getElementById("robots-guardados-seccion");
const mensajeGuardado = document.getElementById("mensaje-guardado");
const mensajeError = document.getElementById("mensaje-error");

// Inicialización
document.addEventListener("DOMContentLoaded", () => {
    Visualizador.inicializar("visualizador-3d");

    _actualizarListaGuardados();

    btnGenerar.addEventListener("click", _generarTabla);
    btnGuardar.addEventListener("click", _guardarRobot);
});

/**
 * _generarTabla
 * Crea una fila por articulación en la tabla de parámetros DH.
 */
function _generarTabla() {
    const n = parseInt(numArticulaciones.value, 10);
    filasArticulaciones.innerHTML = "";

    for (let i = 0; i < n; i++) {
        const fila = document.createElement("tr");
        fila.innerHTML = `
            <td>${i + 1}</td>
            <td>
                <select id="tipo-${i}">
                    <option value="rotatoria">Rotatoria</option>
                    <option value="prismatica">Prismática</option>
                </select>
            </td>
            <td><input type="number" id="theta-${i}" value="0" step="0.1" style="width:55px"></td>
            <td><input type="number" id="d-${i}" value="0" step="0.1" style="width:55px"></td>
            <td><input type="number" id="a-${i}" value="1" step="0.1" style="width:55px"></td>
            <td><input type="number" id="alpha-${i}" value="0" step="0.1" style="width:55px"></td>
        `;
        filasArticulaciones.appendChild(fila);
    }

    tablaDHContenedor.style.display = "block";
    _ocultarMensajes();
}

/**
 * _leerArticulaciones
 * Lee los valores actuales de la tabla DH y devuelve una lista de articulaciones.
 *
 * @returns {Array} Lista de objetos articulación con parámetros DH.
 */
function _leerArticulaciones() {
    const n = parseInt(numArticulaciones.value, 10);
    const articulaciones = [];

    for (let i = 0; i < n; i++) {
        articulaciones.push({
            tipo:  document.getElementById(`tipo-${i}`).value,
            theta: parseFloat(document.getElementById(`theta-${i}`).value),
            d: parseFloat(document.getElementById(`d-${i}`).value),
            a: parseFloat(document.getElementById(`a-${i}`).value),
            alpha: parseFloat(document.getElementById(`alpha-${i}`).value),
        });
    }

    return articulaciones;
}

/**
 * _guardarRobot
 * Valida los datos del formulario, guarda el robot en localStorage y
 * muestra una confirmación al usuario.
 */
async function _guardarRobot() {
    _ocultarMensajes();

    const nombreRobot = document.getElementById("nombre-robot").value.trim();

    if (!nombreRobot) {
        _mostrarError("Introduce un nombre para el robot.");
        return;
    }

    if (filasArticulaciones.children.length === 0) {
        _mostrarError("Genera primero la tabla de articulaciones.");
        return;
    }

    const articulaciones = _leerArticulaciones();

    // Validar que los valores sean numéricos
    const hayInvalidos = articulaciones.some(art =>
        [art.theta, art.d, art.a, art.alpha].some(isNaN)
    );
    if (hayInvalidos) {
        _mostrarError("Hay valores inválidos en la tabla de parámetros DH.");
        return;
    }

    // Construir objeto robot
    const idRobot = `custom_${Date.now()}`;
    const robot = { nombre: nombreRobot, articulaciones };

    // Guardar en localStorage
    const guardados = _obtenerRobotsGuardados();
    guardados[idRobot] = robot;
    localStorage.setItem("robots_personalizados", JSON.stringify(guardados));

    // Actualizar lista y mostrar confirmación
    _actualizarListaGuardados();

    mensajeGuardado.textContent = `✓ Robot "${nombreRobot}" guardado correctamente.`;
    mensajeGuardado.style.display = "block";

    // Previsualizar en el visualizador
    _previsualizarRobot(robot);
}

/**
 * _previsualizarRobot
 * Llama a la API de cinemática directa con la configuración inicial del robot
 * y dibuja el resultado en el visualizador 3D.
 *
 * @param {Object} robot - Datos del robot a previsualizar.
 */
async function _previsualizarRobot(robot) {
    const datosRobot = { nombre: robot.nombre, articulaciones: robot.articulaciones };

    try {
        const respuesta = await fetch("/api/cinematica-directa/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datosRobot),
        });

        const resultado = await respuesta.json();

        if (resultado.exito) {
            Visualizador.dibujarRobot(resultado.articulaciones, resultado.orientacion_efector);
        } else {
            _mostrarError(`No se pudo previsualizar: ${resultado.error}`);
        }
    } catch {
        _mostrarError("Error de red al previsualizar el robot.");
    }
}

/**
 * _actualizarListaGuardados
 * Renderiza la lista de robots guardados en localStorage.
 */
function _actualizarListaGuardados() {
    const robots = _obtenerRobotsGuardados();
    const ids = Object.keys(robots);

    listaRobotsGuardados.innerHTML = "";

    if (ids.length === 0) {
        seccionRobotsGuardados.style.display = "none";
        return;
    }

    seccionRobotsGuardados.style.display = "block";

    ids.forEach(id => {
        const robot = robots[id];
        const li = document.createElement("li");

        const nombre = document.createElement("span");
        nombre.textContent = `${robot.nombre} (${robot.articulaciones.length} GDL)`;

        const btnEliminar = document.createElement("button");
        btnEliminar.textContent = "✕ Eliminar";
        btnEliminar.addEventListener("click", () => _eliminarRobot(id));

        li.appendChild(nombre);
        li.appendChild(btnEliminar);
        listaRobotsGuardados.appendChild(li);
    });
}

/**
 * _eliminarRobot
 * Elimina un robot guardado de localStorage por su ID.
 *
 * @param {string} id - ID del robot a eliminar.
 */
function _eliminarRobot(id) {
    const robots = _obtenerRobotsGuardados();
    delete robots[id];
    localStorage.setItem("robots_personalizados", JSON.stringify(robots));
    _actualizarListaGuardados();
}


function _mostrarError(mensaje) {
    mensajeError.textContent = mensaje;
    mensajeError.style.display = "block";
}

function _ocultarMensajes() {
    mensajeError.style.display = "none";
    mensajeGuardado.style.display = "none";
}

function _obtenerRobotsGuardados() {
    try {
        return JSON.parse(localStorage.getItem("robots_personalizados") || "{}");
    } catch {
        return {};
    }
}