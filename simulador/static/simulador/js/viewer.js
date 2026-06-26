/**
 * viewer.js
 * Módulo de visualización 3D del robot usando Three.js.
 */

import * as THREE from 'three';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.183.0/examples/jsm/controls/OrbitControls.js';

const Visualizador = (function () {

    // Variables internas del visualizador
    let escena, camara, renderer, controles;
    let objetosRobot = [];  // geometrías del robot en escena

    // Materiales reutilizables
    const materialEsfera = new THREE.MeshPhongMaterial({ color: 0x7c9ff5 });
    const materialEsferaEfector = new THREE.MeshPhongMaterial({ color: 0xf5a07c });
    const materialCilindro = new THREE.MeshPhongMaterial({ color: 0x4a5a80 });
    const materialObjetivo = new THREE.MeshPhongMaterial({
        color: 0x80f0a0,
        transparent: true,
        opacity: 0.7,
    });

    /**
     * inicializar
     * Configura la escena Three.js y arranca el bucle de renderizado.
     *
     * @param {string} idContenedor - ID del elemento HTML donde montar el canvas.
     */
    function inicializar(idContenedor) {
        const contenedor = document.getElementById(idContenedor);

        // Escena
        escena = new THREE.Scene();
        escena.background = new THREE.Color(0x12151e);

        // Rejilla de referencia en el plano XZ
        const rejilla = new THREE.GridHelper(10, 20, 0x4a5270, 0x3a4060);
        escena.add(rejilla);

        // Ejes de coordenadas globales
        const ejes = new THREE.AxesHelper(1.5);
        escena.add(ejes);

        // Etiquetas de nombre de eje (X, Y, Z)
        escena.add(_crearEtiquetaSprite("X",1.75,0,0,"#f87171",48));
        escena.add(_crearEtiquetaSprite("Y",0,0,1.75,"#93c5fd",48));
        escena.add(_crearEtiquetaSprite("Z",0,1.75,0,"#86efac",48));

        // Cámara
        const ancho = contenedor.clientWidth  || 800;
        const alto  = contenedor.clientHeight || 600;
        camara = new THREE.PerspectiveCamera(55, ancho / alto, 0.01, 100);
        camara.position.set(4, 3, 5);
        camara.lookAt(0, 0, 0);

        // Iluminación
        const luzAmbiente = new THREE.AmbientLight(0xffffff, 0.5);
        const luzDireccional = new THREE.DirectionalLight(0xffffff, 0.8);
        luzDireccional.position.set(5, 8, 5);
        escena.add(luzAmbiente, luzDireccional);

        // Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(ancho, alto);
        renderer.setPixelRatio(window.devicePixelRatio);
        contenedor.appendChild(renderer.domElement);

        // OrbitControls
        controles = new OrbitControls(camara, renderer.domElement);
        controles.enableDamping = true;   // inercia suave al soltar
        controles.dampingFactor = 0.08;
        controles.minDistance = 2;
        controles.maxDistance = 20;
        controles.target.set(0, 0, 0);
        controles.update();

        // Redimensionar con la ventana
        window.addEventListener("resize", () => {
            const w = contenedor.clientWidth;
            const h = contenedor.clientHeight;
            camara.aspect = w / h;
            camara.updateProjectionMatrix();
            renderer.setSize(w, h);
        });

        // Bucle de animación
        function animar() {
            requestAnimationFrame(animar);
            controles.update(); // necesario cuando enableDamping = true
            renderer.render(escena, camara);
        }
        animar();
    }

    /**
     * dibujarRobot
     * Elimina la representación anterior y dibuja el robot a partir del array articulaciones.
     *
     * @param {Array<Array<number>>} articulaciones - Lista de posiciones [[x,y,z], ...].
     * @param {Array<Array<number>>} [orientacion] - Matriz 3x3 de rotación del efector.
     */
    function dibujarRobot(articulaciones, orientacion) {
        objetosRobot.forEach(obj => escena.remove(obj));
        objetosRobot = [];

        if (!articulaciones || articulaciones.length === 0) return;

        // Dibujar cada articulación como esfera
        articulaciones.forEach((pos, indice) => {
            const esEfector = (indice === articulaciones.length - 1);
            const radio     = esEfector ? 0.12 : 0.09;
            const material  = esEfector ? materialEsferaEfector : materialEsfera;

            const geo   = new THREE.SphereGeometry(radio, 16, 16);
            const malla = new THREE.Mesh(geo, material);
            malla.position.set(pos[0], pos[2], pos[1]);  // Cambiar ejes Z e Y para vista 3D
            escena.add(malla);
            objetosRobot.push(malla);
        });

        // Dibujar cilindros entre articulaciones consecutivas
        for (let i = 0; i < articulaciones.length - 1; i++) {
            const cilindro = _crearCilindroEntre(articulaciones[i], articulaciones[i + 1]);
            if (cilindro) {
                escena.add(cilindro);
                objetosRobot.push(cilindro);
            }
        }

        // Flechas de orientación del efector
        if (orientacion && articulaciones.length > 0) {
            const posEfector = articulaciones[articulaciones.length - 1];
            const flechas    = _crearFlechasEfector(posEfector, orientacion);
            flechas.forEach(f => { escena.add(f); objetosRobot.push(f); });
        }
    }

    /**
     * marcarObjetivo
     * Muestra una pequeña esfera semitransparente verde en la posición objetivo.
     *
     * @param {Array<number>} posicion - Posición [x, y, z] del objetivo.
     */
    function marcarObjetivo(posicion) {
        const geo   = new THREE.SphereGeometry(0.1, 12, 12);
        const malla = new THREE.Mesh(geo, materialObjetivo);
        malla.position.set(posicion[0], posicion[2], posicion[1]);
        escena.add(malla);
        objetosRobot.push(malla);
    }

    // ── Funciones privadas ────────────────────────────────────────────────────

    /**
     * _crearCilindroEntre
     * Crea una malla cilíndrica entre dos puntos 3D.
     *
     * @param {Array<number>} a - Punto de origen [x, y, z].
     * @param {Array<number>} b - Punto de destino [x, y, z].
     * @returns {THREE.Mesh|null}
     */
    function _crearCilindroEntre(a, b) {
        const vA = new THREE.Vector3(a[0], a[2], a[1]);
        const vB = new THREE.Vector3(b[0], b[2], b[1]);

        const longitud = vA.distanceTo(vB);
        if (longitud < 0.001) return null;

        const geo   = new THREE.CylinderGeometry(0.04, 0.04, longitud, 8);
        const malla = new THREE.Mesh(geo, materialCilindro);

        const medio     = new THREE.Vector3().addVectors(vA, vB).multiplyScalar(0.5);
        malla.position.copy(medio);

        const direccion  = new THREE.Vector3().subVectors(vB, vA).normalize();
        const quaternion = new THREE.Quaternion().setFromUnitVectors(
            new THREE.Vector3(0, 1, 0), direccion
        );
        malla.setRotationFromQuaternion(quaternion);

        return malla;
    }

    /**
     * _crearFlechasEfector
     * Construye tres ArrowHelper translúcidos (X=rojo, Y=azul, Z=verde) que
     * representan la orientación del efector final.
     *
     * @param {Array<number>} posEfector - Posición [x,y,z] del efector.
     * @param {Array<Array<number>>} orientacion - Matriz 3x3 de rotación del efector.
     * @returns {THREE.ArrowHelper[]}
     */
    function _crearFlechasEfector(posEfector, orientacion) {
        const origen = new THREE.Vector3(posEfector[0], posEfector[2], posEfector[1]);
        const longitud = 0.4;
        const opacidad = 0.55;

        const ejesRobot = [
            { col: 0, color: 0xff6060 }, // X - rojo
            { col: 1, color: 0x60b0ff }, // Y - azul
            { col: 2, color: 0x60e090 }, // Z - verde
        ];

        return ejesRobot.map(({ col, color }) => {
            const dir = new THREE.Vector3(
                orientacion[0][col],
                orientacion[2][col],
                orientacion[1][col]
            ).normalize();

            const flecha = new THREE.ArrowHelper(
                dir, origen, longitud, color, longitud * 0.28, longitud * 0.14
            );
            flecha.line.material.transparent = true;
            flecha.line.material.opacity = opacidad;
            flecha.cone.material.transparent = true;
            flecha.cone.material.opacity = opacidad;
            return flecha;
        });
    }

    /**
     * _crearEtiquetaSprite
     * Crea un sprite con texto renderizado sobre un canvas 2D.
     * El sprite siempre mira a la cámara.
     *
     * @param {string} texto  - Texto a mostrar.
     * @param {number} x - Posición X en la escena.
     * @param {number} y - Posición Y en la escena.
     * @param {number} z - Posición Z en la escena.
     * @param {string} color - Color CSS del texto.
     * @param {number} fontSize - Tamaño de fuente en píxeles del canvas.
     * @returns {THREE.Sprite}
     */
    function _crearEtiquetaSprite(texto, x, y, z, color, fontSize) {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const fuente = `bold ${fontSize}px 'Segoe UI', sans-serif`;
        ctx.font = fuente;

        const ancho = ctx.measureText(texto).width + fontSize * 0.6;
        const alto = fontSize * 1.4;
        canvas.width = ancho;
        canvas.height = alto;

        ctx.font = fuente;
        ctx.fillStyle = color;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(texto, ancho / 2, alto / 2);

        const textura  = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({ map: textura, depthTest: false });
        const sprite   = new THREE.Sprite(material);

        const escala = fontSize === 48 ? 0.35 : 0.22;
        sprite.scale.set(escala * (ancho / alto), escala, 1);
        sprite.position.set(x, y, z);
        return sprite;
    }

    // API pública del módulo
    return { inicializar, dibujarRobot, marcarObjetivo };

})();

// Exponer como global para que los scripts de cada página puedan acceder al visualizador
window.Visualizador = Visualizador;
