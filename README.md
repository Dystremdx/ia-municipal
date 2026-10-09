# 🏛️ IA Municipal · Priorización Inteligente

[![Curso](https://img.shields.io/badge/Curso-Gesti%C3%B3n%20de%20Proyectos%20TICs%20(EST315)-blue.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000.svg?logo=flask&logoColor=white)](#)
[![Cloud Deploy](https://img.shields.io/badge/Deploy-Render%2024%2F7-46E3B7.svg?logo=render&logoColor=white)](#)
[![Arquitectura](https://img.shields.io/badge/Roles-Ciudadano%20%2B%20Admin-green.svg)](#)

---

## 📌 1. Contexto del Proyecto

El proyecto **"IA Municipal · Priorización Inteligente"** es un **prototipo académico funcional** (no productivo) desarrollado para la asignatura **"Gestión de Proyectos TICs (EST315)"**. 

Presenta una **arquitectura de doble portal** inspirada en las plataformas de atención ciudadana y despacho de servicios públicos modernos:
1. **Portal Ciudadano (`/`):** Plataforma pública, transparente e intuitiva donde cualquier vecino puede registrar incidencias, consultar el estado de su ticket y ver las intervenciones en su comunidad.
2. **Portal Administrador / Municipal (`/admin`):** Consola operativa restringida para el personal de la municipalidad, donde el **Motor de IA Multicriterio** genera el ranking de 0 a 100, asigna semáforos de urgencia y permite a los funcionarios cambiar estados en tiempo real (disparando la regla **RN-08**).

* **Cliente Institucional (Simulado):** Municipalidad de Lima
* **Población Objetivo:** Distritos de Puno, Juliaca, Yunguyo, Ilave, Chucuito y otros.
* **Dataset Base:** 39 reportes reales de una encuesta a 39 ciudadanos.

---

## 👥 2. Equipo del Proyecto

| Rol | Integrante | Responsabilidad Principal |
| :--- | :--- | :--- |
| **Project Manager** | **Cristian Ronaldo** | Dirección general, cronograma y gestión de entregables |
| **Análisis de Datos** | **Ronald Wilder** | Procesamiento del dataset de 39 reportes y métricas |
| **Arquitectura IA** | **Yair Dilan** | Diseño del algoritmo multicriterio y reglas RN-01 a RN-08 |
| **Comunicaciones** | **Choucha** | Interfaz ciudadana, documentación y difusión institucional |

---

## 🔐 3. Credenciales de Acceso para Evaluación (Docente / Jurado)

El sistema incluye una pantalla de login institucional en `/login` con credenciales de prueba preconfiguradas:

* **URL de Login:** `/login`
* **Usuario:** `admin`
* **Contraseña:** `admin2026`
* *Facilidad Docente:* La pantalla de inicio de sesión cuenta con un botón **"⚡ Rellenar Automáticamente y Acceder"** para ingresar al panel con un solo clic.

---

## ⚙️ 4. Modelo Matemático y Motor de IA (`motor_ia.py`)

El sistema evalúa cada incidencia a través de una función de valor multicriterio acotada en una escala de **0 a 100 puntos**:

$$\text{Puntaje Base} = (P_G \times 0.35) + (P_P \times 0.30) + (P_T \times 0.20) + (P_R \times 0.15)$$

### 📊 Factores Evaluados y Normalización (0 - 100):
1. **Gravedad del Incidente ($35\%$):** Evaluada de 1 a 5 estrellas. $\text{Norm} = (\text{Gravedad} / 5) \times 100$.
2. **Población Afectada ($30\%$):** Rango de 10 a 5,000 habitantes. $\text{Norm} = \min(100, (\text{Población} / 5000) \times 100)$.
3. **Tiempo sin Resolver ($20\%$):** Días transcurridos (1 a 60 días). $\text{Norm} = \min(100, (\text{Días} / 60) \times 100)$.
4. **Recursos Necesarios ($15\%$):** Factibilidad técnica y agilidad operativa.
   * `Bajo`: **100 pts** *(Alta agilidad de despacho / Quick-Win)*
   * `Medio`: **60 pts** *(Despliegue operativo estándar)*
   * `Alto`: **30 pts** *(Requiere maquinaria pesada o licitación mayor)*

---

## 📜 5. Reglas de Negocio Implementadas (RN-01 a RN-08)

* **`RN-01: Concentración Zonal`** $\rightarrow$ Si un distrito y zona geográfica acumula 3 o más reportes activos, se identifica un foco crítico vecinal y se bonifica con **+7.0 puntos**.
* **`RN-02: Detección de Duplicados / Reincidencia Colectiva`** $\rightarrow$ Identifica reportes que coinciden en distrito, zona y categoría. Si hay reincidencia ciudadana, bonifica con **+5.0 puntos** por presión social reiterada.
* **`RN-03: Antigüedad Crítica`** $\rightarrow$ Todo reporte con más de **30 días sin resolver** recibe una bonificación de urgencia por abandono administrativo de **+8.0 puntos**.
* **`RN-04: Optimización de Recursos (Quick-Wins)`** $\rightarrow$ Las incidencias catalogadas con recursos `Bajo` reciben **+4.0 puntos** para favorecer soluciones inmediatas de alto retorno.
* **`RN-05: Umbral de Riesgo Extremo`** $\rightarrow$ Si la gravedad es 5 y la población afectada es $\ge 1,000$ habitantes (o son inundaciones/fugas mayores de gravedad 5), se activa la alarma de emergencia fijando un puntaje mínimo garantizado de **85.0 puntos** (+5 si supera).
* **`RN-06: Límites de Puntaje (Clamping)`** $\rightarrow$ El puntaje final se restringe estrictamente en el intervalo cerrado $[0.0, 100.0]$.
* **`RN-07: Clasificación Semáforo`** $\rightarrow$ Segmentación según rangos oficiales:
  * 🚨 **Crítica:** $\ge 80.0 \text{ pts}$ (Rojo)
  * ⚠️ **Alta:** $65.0 - 79.9 \text{ pts}$ (Naranja)
  * ⏳ **Media:** $45.0 - 64.9 \text{ pts}$ (Amarillo)
  * ✅ **Baja:** $< 45.0 \text{ pts}$ (Verde)
* **`RN-08: Gestión de Casos Resueltos`** $\rightarrow$ Al marcar un reporte como `Resuelto` desde el panel municipal, la IA asigna automáticamente **0.0 puntos**, lo sitúa al final de la cola y libera la prioridad de las cuadrillas.

---

## 📁 6. Estructura de Archivos del Proyecto

```text
ia-municipal/
│
├── app.py                  # Servidor Flask principal con gestión de sesiones y roles
├── motor_ia.py             # Motor de priorización multicriterio (RN-01 a RN-08)
├── requirements.txt        # Dependencias de producción para Render
├── Procfile                # Archivo de inicio para gunicorn en Render
├── runtime.txt             # Definición de Python 3.11.0 para el contenedor nube
├── .gitignore              # Exclusiones de Git (__pycache__, venv, etc.)
├── README.md               # Documentación integral del proyecto
│
├── data/
│   └── reportes.json       # Base de datos JSON con los 39 reportes ciudadanos
│
├── templates/
│   ├── ciudadano.html      # Portal público para vecinos (búsqueda y transparencia)
│   ├── login.html          # Inicio de sesión para personal municipal
│   ├── index.html          # Panel de administración con IA, semáforo y cambio de estado
│   ├── detalle.html        # Ficha técnica, desglose de factores y línea de tiempo
│   ├── registro.html       # Formulario interactivo para nuevos reportes ciudadanos
│   └── exportar_print.html # Vista optimizada para impresión y exportación PDF
│
└── static/
    ├── style.css           # Estilos corporativos, semáforo y diseño responsive
    └── script.js           # Filtros en vivo, gráficos dinámicos y validaciones
```

---

## 💻 7. Instrucciones de Instalación y Uso Local

```bash
cd "d:\6to semestre\TICS\proyecto"
pip install -r requirements.txt
python app.py
```

Abrir en su navegador:
* 🌐 **Portal Ciudadano:** `http://localhost:5000`
* 🔐 **Login de Funcionarios:** `http://localhost:5000/login`
* ⚙️ **Panel de Cuadrillas / IA:** `http://localhost:5000/admin`

---

## 🚀 8. Instrucciones para Subir a GitHub

```bash
git init
git add .
git commit -m "Proyecto IA Municipal - Doble Portal Ciudadano y Admin"
git branch -M main
git remote add origin https://github.com/tu-usuario/ia-municipal.git
git push -u origin main
```

---

## ☁️ 9. Despliegue en la Nube (Render) GRATIS 24/7

1. Ingrese a **[render.com](https://render.com/)** e inicie sesión con GitHub.
2. Haga clic en **New +** $\rightarrow$ **Web Service**.
3. Seleccione su repositorio de GitHub (`ia-municipal`).
4. Configurar:
   * **Name:** `ia-municipal`
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`
   * **Plan Type:** `Free`
5. Haga clic en **Create Web Service**.
6. En 2 minutos tendrá una URL pública activa las 24 horas del día tipo:
   ```text
   https://ia-municipal.onrender.com
   ```

---

## 🎓 10. Créditos

* **Curso:** Gestión de Proyectos TICs (EST315)
* **PM:** Cristian Ronaldo
* **Análisis de Datos:** Ronald Wilder
* **Arquitectura IA:** Yair Dilan
* **Comunicaciones:** Choucha
* **Cliente:** Municipalidad de Lima (Simulado)
