/**
 * TRABAJITOS — JavaScript principal del sitio.
 * Maneja el menú de navegación en mobile y la vista ampliada ("lightbox")
 * de las fotos del portafolio en el perfil público de un colaborador.
 */

document.addEventListener("DOMContentLoaded", () => {
    const boton = document.getElementById("menu-toggle");
    const etiqueta = document.getElementById("menu-toggle-label");
    const nav = document.getElementById("nav-principal");

    if (!boton || !nav) return;

    // El botón hamburguesa solo es visible en mobile (ver media query en
    // style.css). Usamos eso para saber si el menú colapsable aplica ahora
    // mismo, en vez de repetir el ancho de la breakpoint acá en JS.
    const enModoMobile = () => getComputedStyle(boton).display !== "none";

    // Mientras el menú está cerrado en mobile, marcamos la navegación como
    // "inert": deja de ser alcanzable con Tab y con lectores de pantalla,
    // igual que ya es invisible visualmente. Evita que alguien navegando
    // por teclado caiga en enlaces que no puede ver.
    const cerrarMenu = () => {
        nav.classList.remove("header__nav--abierto");
        boton.setAttribute("aria-expanded", "false");
        if (etiqueta) etiqueta.textContent = "Abrir menú";
        if (enModoMobile()) nav.setAttribute("inert", "");
    };

    const abrirMenu = () => {
        nav.classList.add("header__nav--abierto");
        boton.setAttribute("aria-expanded", "true");
        if (etiqueta) etiqueta.textContent = "Cerrar menú";
        nav.removeAttribute("inert");
    };

    if (enModoMobile()) {
        nav.setAttribute("inert", "");
    }

    boton.addEventListener("click", () => {
        const abierto = nav.classList.contains("header__nav--abierto");
        if (abierto) {
            cerrarMenu();
        } else {
            abrirMenu();
        }
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && nav.classList.contains("header__nav--abierto")) {
            cerrarMenu();
            boton.focus();
        }
    });

    // Si la ventana cambia de mobile a desktop (o viceversa), reacomodamos
    // el atributo inert para que la navegación nunca quede inaccesible.
    window.addEventListener("resize", () => {
        if (!enModoMobile()) {
            nav.removeAttribute("inert");
        } else if (!nav.classList.contains("header__nav--abierto")) {
            nav.setAttribute("inert", "");
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    // Vista ampliada simple de las fotos del portafolio (perfil público de
    // un colaborador). Usa <dialog>, nativo del navegador: no hace falta
    // ninguna librería de "lightbox".
    const dialogo = document.getElementById("lightbox-portafolio");
    if (!dialogo) return;

    const img = document.getElementById("lightbox-img");
    const descripcion = document.getElementById("lightbox-desc");

    document.querySelectorAll(".portafolio-publico__item").forEach((boton) => {
        boton.addEventListener("click", () => {
            img.src = boton.dataset.src;
            img.alt = boton.dataset.desc || "Foto de un trabajo realizado";
            descripcion.textContent = boton.dataset.desc || "";
            dialogo.showModal();
        });
    });

    document.getElementById("lightbox-cerrar")?.addEventListener("click", () => dialogo.close());

    // Clic en el fondo oscuro (fuera de la imagen) también cierra.
    dialogo.addEventListener("click", (evento) => {
        if (evento.target === dialogo) dialogo.close();
    });
});
