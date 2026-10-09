/**
 * =============================================================================
 * PROYECTO: IA Municipal · Priorización Inteligente (EST315)
 * SCRIPT: Interactividad frontend, filtros dinámicos, Chart.js y validaciones
 * =============================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  inicializarFiltros();
  inicializarGraficos();
  inicializarFormularioRegistro();
  inicializarKpiClicks();
});

/**
 * 1. FILTROS DINÁMICOS EN VIVO (Sin recargar la página)
 */
function inicializarFiltros() {
  const selectCategoria = document.getElementById("filtroCategoria");
  const selectDistrito = document.getElementById("filtroDistrito");
  const selectPrioridad = document.getElementById("filtroPrioridad");
  const inputBusqueda = document.getElementById("filtroBusqueda");
  const contadorFilas = document.getElementById("contadorFilas");
  const btnLimpiar = document.getElementById("btnLimpiarFiltros");
  const filas = document.querySelectorAll("#tablaRanking tbody tr");

  if (!filas.length) return;

  function aplicarFiltros() {
    const catFiltro = selectCategoria ? selectCategoria.value.toLowerCase().trim() : "";
    const distFiltro = selectDistrito ? selectDistrito.value.toLowerCase().trim() : "";
    const prioFiltro = selectPrioridad ? selectPrioridad.value.toLowerCase().trim() : "";
    const textoFiltro = inputBusqueda ? inputBusqueda.value.toLowerCase().trim() : "";

    let visibles = 0;

    filas.forEach((fila) => {
      const catFila = (fila.getAttribute("data-categoria") || "").toLowerCase();
      const distFila = (fila.getAttribute("data-distrito") || "").toLowerCase();
      const prioFila = (fila.getAttribute("data-prioridad") || "").toLowerCase();
      const textoFila = fila.textContent.toLowerCase();

      const cumpleCat = !catFiltro || catFila === catFiltro;
      const cumpleDist = !distFiltro || distFila === distFiltro;
      const cumplePrio = !prioFiltro || prioFila === prioFiltro;
      const cumpleTexto = !textoFiltro || textoFila.includes(textoFiltro);

      if (cumpleCat && cumpleDist && cumplePrio && cumpleTexto) {
        fila.style.display = "";
        visibles++;
      } else {
        fila.style.display = "none";
      }
    });

    if (contadorFilas) {
      contadorFilas.textContent = visibles;
    }

    if (btnLimpiar) {
      const hayFiltroActivo = catFiltro || distFiltro || prioFiltro || textoFiltro;
      btnLimpiar.style.display = hayFiltroActivo ? "inline-block" : "none";
    }
  }

  // Event Listeners para cambios
  if (selectCategoria) selectCategoria.addEventListener("change", aplicarFiltros);
  if (selectDistrito) selectDistrito.addEventListener("change", aplicarFiltros);
  if (selectPrioridad) selectPrioridad.addEventListener("change", aplicarFiltros);
  if (inputBusqueda) inputBusqueda.addEventListener("input", aplicarFiltros);

  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", () => {
      if (selectCategoria) selectCategoria.value = "";
      if (selectDistrito) selectDistrito.value = "";
      if (selectPrioridad) selectPrioridad.value = "";
      if (inputBusqueda) inputBusqueda.value = "";
      aplicarFiltros();
    });
  }
}

/**
 * 2. CLICK DIRECTO EN TARJETAS KPI PARA FILTRAR RÁPIDAMENTE
 */
function inicializarKpiClicks() {
  const kpiCards = document.querySelectorAll(".kpi-card[data-filter-quick]");
  const selectPrioridad = document.getElementById("filtroPrioridad");

  if (!selectPrioridad) return;

  kpiCards.forEach((card) => {
    card.addEventListener("click", () => {
      const targetPrio = card.getAttribute("data-filter-quick");
      if (selectPrioridad.value === targetPrio) {
        selectPrioridad.value = ""; // Deseleccionar
      } else {
        selectPrioridad.value = targetPrio;
      }
      selectPrioridad.dispatchEvent(new Event("change"));

      // Scroll suave a la tabla
      const tabla = document.getElementById("tablaRanking");
      if (tabla) {
        tabla.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
}

/**
 * 3. GRÁFICOS DINÁMICOS CON CHART.JS (Distribución y Semáforo)
 */
function inicializarGraficos() {
  const canvasCat = document.getElementById("graficoCategorias");
  const canvasPrio = document.getElementById("graficoPrioridades");

  // Gráfico de Categorías (Barras horizontales estilizadas)
  if (canvasCat && window.DATOS_CATEGORIAS) {
    const labels = Object.keys(window.DATOS_CATEGORIAS);
    const dataValues = Object.values(window.DATOS_CATEGORIAS);

    new Chart(canvasCat, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Cantidad de Reportes",
            data: dataValues,
            backgroundColor: [
              "#3b82f6", // Basura
              "#f97316", // Baches
              "#06b6d4", // Fugas
              "#eab308", // Alumbrado
              "#6366f1", // Inundaciones
              "#64748b"  // Otros
            ],
            borderRadius: 6,
            borderWidth: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.raw} incidentes registrados`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 2 },
            grid: { color: "#f1f5f9" }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // Gráfico de Prioridades (Doughnut Semáforo)
  if (canvasPrio && window.DATOS_PRIORIDADES) {
    const prioLabels = ["Crítica", "Alta", "Media", "Baja"];
    const prioValues = [
      window.DATOS_PRIORIDADES["Crítica"] || 0,
      window.DATOS_PRIORIDADES["Alta"] || 0,
      window.DATOS_PRIORIDADES["Media"] || 0,
      window.DATOS_PRIORIDADES["Baja"] || 0
    ];

    new Chart(canvasPrio, {
      type: "doughnut",
      data: {
        labels: prioLabels,
        datasets: [
          {
            data: prioValues,
            backgroundColor: [
              "#dc2626", // Crítica
              "#ea580c", // Alta
              "#ca8a04", // Media
              "#16a34a"  // Baja
            ],
            borderColor: "#ffffff",
            borderWidth: 3,
            hoverOffset: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              boxWidth: 12,
              padding: 15,
              font: { size: 12, family: "'Inter', sans-serif" }
            }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw} reportes`
            }
          }
        }
      }
    });
  }
}

/**
 * 4. VALIDACIÓN Y CONFIRMACIÓN ANTES DE REGISTRAR REPORTE
 */
function inicializarFormularioRegistro() {
  const form = document.getElementById("formRegistroReporte");
  if (!form) return;

  form.addEventListener("submit", (e) => {
    const cat = document.getElementById("categoria").value;
    const dist = document.getElementById("distrito").value;
    const grav = document.getElementById("gravedad").value;
    const desc = document.getElementById("descripcion").value.trim();

    if (!cat || !dist || !desc) {
      alert("Por favor complete todos los campos obligatorios.");
      e.preventDefault();
      return;
    }

    const mensaje = `¿Confirma el registro del siguiente reporte municipal?\n\n• Categoría: ${cat}\n• Distrito: ${dist}\n• Gravedad: ${grav}/5\n\nEl Motor de IA recalculará automáticamente la matriz de prioridades.`;
    const confirmado = confirm(mensaje);

    if (!confirmado) {
      e.preventDefault();
    }
  });
}
