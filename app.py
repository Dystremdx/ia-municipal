"""
=============================================================================
PROYECTO: IA Municipal · Priorización Inteligente
CURSO: Gestión de Proyectos TICs (EST315)
CLIENTE: Municipalidad de Lima (Simulado)
EQUIPO:
  - Project Manager: Cristian Ronaldo
  - Análisis de Datos: Ronald Wilder
  - Arquitectura IA: Yair Dilan
  - Comunicaciones: Choucha
ARCHIVO: app.py
DESCRIPCIÓN:
  Servidor web Flask con arquitectura de doble portal:
  1. Portal Ciudadano (/): Registro cívico y seguimiento de tickets vecinales.
  2. Portal Administrador (/admin): Dashboard de priorización con IA,
     control de cuadrillas, cambio de estados (RN-08) y exportación de reportes.
=============================================================================
"""

import os
import json
import io
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, jsonify, flash, send_file, session
)
from motor_ia import calcular_ranking, consolidar_duplicados

# Inicialización de Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ia-municipal-tics-2026-secret-key-segura")

# Ruta relativa del archivo de base de datos JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "reportes.json")

# Credenciales de acceso para el personal municipal (Prototipo Académico)
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin2026")


def cargar_reportes():
    """Lee el archivo JSON de reportes con codificación UTF-8."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def guardar_reportes(reportes):
    """Escribe los reportes en el archivo JSON con formato legible."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(reportes, f, ensure_ascii=False, indent=2)


def admin_requerido(f):
    """Decorador para proteger rutas exclusivas del Administrador Municipal."""
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get("es_admin"):
            flash("Debe iniciar sesión como funcionario municipal para acceder al panel de IA.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorada


@app.context_processor
def inyectar_variables_globales():
    """Variables accesibles en todas las plantillas HTML."""
    return {
        "anio_actual": datetime.now().year,
        "cliente": "Municipalidad de Lima",
        "curso": "Gestión de Proyectos TICs (EST315)",
        "es_admin": session.get("es_admin", False),
        "usuario_admin": session.get("usuario_admin", "Cristian Ronaldo (PM)"),
        "equipo": {
            "pm": "Cristian Ronaldo",
            "datos": "Ronald Wilder",
            "ia": "Yair Dilan",
            "comunicaciones": "Choucha"
        }
    }


# =============================================================================
# 1. RUTAS DEL PORTAL CIUDADANO (PÚBLICO)
# =============================================================================

@app.route("/")
def portal_ciudadano():
    """
    Portal Ciudadano: Vista pública y amigable orientada a los vecinos.
    Permite consultar tickets, revisar avances en su distrito y reportar problemas.
    """
    reportes = cargar_reportes()

    # Métricas de cara al ciudadano
    total_reportes = len(reportes)
    resueltos = sum(1 for r in reportes if r.get("estado") == "Resuelto")
    en_atencion = sum(1 for r in reportes if r.get("estado") == "En atención")
    pendientes = sum(1 for r in reportes if r.get("estado") == "Pendiente")

    # Ordenar por fecha descendente para los ciudadanos
    reportes_recientes = sorted(
        reportes,
        key=lambda r: (r.get("fecha_reporte", ""), r.get("id", 0)),
        reverse=True
    )

    return render_template(
        "ciudadano.html",
        reportes=reportes_recientes,
        total=total_reportes,
        resueltos=resueltos,
        en_atencion=en_atencion,
        pendientes=pendientes
    )


@app.route("/registro", methods=["GET", "POST"])
def registro():
    """
    Formulario de Registro Ciudadano:
    Permite a cualquier vecino registrar una nueva incidencia.
    El motor de IA recalculará automáticamente la matriz de prioridades en el backend.
    """
    if request.method == "POST":
        reportes = cargar_reportes()
        nuevo_id = max([r.get("id", 0) for r in reportes], default=0) + 1

        try:
            gravedad = int(request.form.get("gravedad", 3))
            poblacion = int(request.form.get("poblacion_afectada", 100))
            tiempo = int(request.form.get("tiempo_sin_resolver", 1))
        except ValueError:
            gravedad = 3
            poblacion = 100
            tiempo = 1

        nuevo_reporte = {
            "id": nuevo_id,
            "categoria": request.form.get("categoria", "Otros").strip(),
            "distrito": request.form.get("distrito", "Puno").strip(),
            "zona": request.form.get("zona", "Centro").strip(),
            "descripcion": request.form.get("descripcion", "").strip(),
            "fecha_reporte": datetime.now().strftime("%Y-%m-%d"),
            "gravedad": max(1, min(5, gravedad)),
            "poblacion_afectada": max(10, min(5000, poblacion)),
            "tiempo_sin_resolver": max(1, min(60, tiempo)),
            "recursos_requeridos": request.form.get("recursos_requeridos", "Medio").strip(),
            "estado": "Pendiente" if not session.get("es_admin") else request.form.get("estado", "Pendiente").strip()
        }

        reportes.append(nuevo_reporte)
        guardar_reportes(reportes)

        flash(f"¡Su reporte ha sido recibido con el Ticket #{nuevo_id}! El sistema municipal ya lo ingresó a la cola de atención.", "success")
        
        if session.get("es_admin"):
            return redirect(url_for("panel_admin"))
        return redirect(url_for("detalle", id=nuevo_id))

    return render_template("registro.html")


@app.route("/detalle/<int:id>")
def detalle(id):
    """
    Vista de Detalle: Muestra la información del reporte.
    - Si es Admin: desglose completo de IA, factores ponderados y reglas activadas.
    - Si es Ciudadano: estado del ticket, nivel de avance y explicación de atención.
    """
    reportes = cargar_reportes()
    ranking = calcular_ranking(reportes)

    reporte_encontrado = next((r for r in ranking if r.get("id") == id), None)

    if not reporte_encontrado:
        flash(f"El reporte con ticket #{id} no fue encontrado.", "warning")
        return redirect(url_for("portal_ciudadano"))

    return render_template("detalle.html", reporte=reporte_encontrado)


# =============================================================================
# 2. AUTENTICACIÓN DE FUNCIONARIOS MUNICIPALES
# =============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Pantalla de inicio de sesión para el personal municipal.
    """
    if session.get("es_admin"):
        return redirect(url_for("panel_admin"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        if usuario == ADMIN_USER and password == ADMIN_PASS:
            session["es_admin"] = True
            session["usuario_admin"] = "Cristian Ronaldo (PM)"
            flash("¡Bienvenido al Panel de Control de Priorización IA!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("panel_admin"))
        else:
            flash("Credenciales incorrectas. Verifique el usuario y contraseña.", "danger")

    return render_template("login.html", admin_user=ADMIN_USER, admin_pass=ADMIN_PASS)


@app.route("/logout")
def logout():
    """Cierra la sesión del administrador y retorna al portal ciudadano."""
    session.clear()
    flash("Sesión cerrada correctamente. Ahora estás en el Portal Ciudadano.", "info")
    return redirect(url_for("portal_ciudadano"))


# =============================================================================
# 3. RUTAS DEL PORTAL ADMINISTRADOR / MUNICIPAL (PROTEGIDAS)
# =============================================================================

@app.route("/admin")
@admin_requerido
def panel_admin():
    """
    Dashboard del Administrador Municipal:
    Muestra el ranking de IA de 0 a 100, semáforo, KPIs, gráficos de cuadrilla,
    filtros avanzados y acciones operativas.
    """
    reportes = cargar_reportes()
    ranking = calcular_ranking(reportes)

    # Métricas y KPIs operativos
    total = len(ranking)
    criticos = sum(1 for r in ranking if r.get("clasificacion") == "Crítica")
    altos = sum(1 for r in ranking if r.get("clasificacion") == "Alta")
    medios = sum(1 for r in ranking if r.get("clasificacion") == "Media")
    bajos = sum(1 for r in ranking if r.get("clasificacion") == "Baja")
    resueltos = sum(1 for r in ranking if r.get("estado") == "Resuelto")
    en_atencion = sum(1 for r in ranking if r.get("estado") == "En atención")
    pendientes = sum(1 for r in ranking if r.get("estado") == "Pendiente")

    # Distribución por Categoría para Chart.js
    categorias_conteo = {}
    for r in reportes:
        cat = r.get("categoria", "Otros")
        categorias_conteo[cat] = categorias_conteo.get(cat, 0) + 1

    # Distribución por Distrito para Chart.js
    distritos_conteo = {}
    for r in reportes:
        dist = r.get("distrito", "Otro")
        distritos_conteo[dist] = distritos_conteo.get(dist, 0) + 1

    distritos_unicos = sorted(list({r.get("distrito") for r in reportes if r.get("distrito")}))
    categorias_unicas = sorted(list({r.get("categoria") for r in reportes if r.get("categoria")}))

    return render_template(
        "index.html",
        ranking=ranking,
        total=total,
        criticos=criticos,
        altos=altos,
        medios=medios,
        bajos=bajos,
        resueltos=resueltos,
        en_atencion=en_atencion,
        pendientes=pendientes,
        categorias_conteo=categorias_conteo,
        distritos_conteo=distritos_conteo,
        distritos_unicos=distritos_unicos,
        categorias_unicas=categorias_unicas
    )


@app.route("/admin/cambiar_estado/<int:id>", methods=["POST"])
@admin_requerido
def cambiar_estado(id):
    """
    Permite al funcionario cambiar el estado operativo de una incidencia
    (Pendiente -> En atención -> Resuelto).
    Al marcar 'Resuelto', la regla RN-08 asigna puntaje 0.0 y lo mueve al final.
    """
    nuevo_estado = request.form.get("nuevo_estado", "").strip()
    if nuevo_estado not in ["Pendiente", "En atención", "Resuelto"]:
        flash("Estado inválido seleccionado.", "warning")
        return redirect(url_for("panel_admin"))

    reportes = cargar_reportes()
    encontrado = False

    for rep in reportes:
        if rep.get("id") == id:
            estado_anterior = rep.get("estado")
            rep["estado"] = nuevo_estado
            encontrado = True
            break

    if encontrado:
        guardar_reportes(reportes)
        if nuevo_estado == "Resuelto":
            flash(f"Incidencia #{id} marcada como RESUELTA. La regla RN-08 actualizó el ranking y liberó prioridad operativa.", "success")
        else:
            flash(f"Estado de incidencia #{id} actualizado de '{estado_anterior}' a '{nuevo_estado}'.", "info")
    else:
        flash(f"No se encontró el reporte #{id}.", "danger")

    # Retornar a la vista correspondiente
    referer = request.headers.get("Referer", "")
    if f"/detalle/{id}" in referer:
        return redirect(url_for("detalle", id=id))
    return redirect(url_for("panel_admin"))


# =============================================================================
# 4. API REST Y EXPORTACIÓN A PDF
# =============================================================================

@app.route("/api/ranking")
def api_ranking():
    """Retorna la matriz de priorización en formato JSON estándar."""
    reportes = cargar_reportes()
    ranking = calcular_ranking(reportes)
    return jsonify({
        "proyecto": "IA Municipal · Priorización Inteligente",
        "cliente": "Municipalidad de Lima (Simulado)",
        "timestamp": datetime.now().isoformat(),
        "total_reportes": len(ranking),
        "ranking": ranking
    })


@app.route("/exportar_pdf")
def exportar_pdf():
    """Genera documento PDF oficial del ranking para cuadrillas operativas."""
    reportes = cargar_reportes()
    ranking = calcular_ranking(reportes)

    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=25,
            leftMargin=25,
            topMargin=25,
            bottomMargin=25
        )

        elementos = []
        estilos = getSampleStyleSheet()

        titulo_style = ParagraphStyle(
            'TituloDoc',
            parent=estilos['Heading1'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1e3a8a'),
            alignment=1
        )
        subtitulo_style = ParagraphStyle(
            'SubtituloDoc',
            parent=estilos['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#475569'),
            alignment=1
        )
        celda_style = ParagraphStyle(
            'CeldaTexto',
            parent=estilos['Normal'],
            fontSize=8,
            leading=10
        )
        celda_head = ParagraphStyle(
            'CeldaHead',
            parent=estilos['Normal'],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )

        elementos.append(Paragraph("MUNICIPALIDAD DE LIMA · SISTEMA DE PRIORIZACIÓN INTELIGENTE CON IA", titulo_style))
        elementos.append(Paragraph("Proyecto: Gestión de Proyectos TICs (EST315) | PM: Cristian Ronaldo | Ranking de Cuadrillas", subtitulo_style))
        elementos.append(Spacer(1, 12))

        datos_tabla = [[
            Paragraph("Rank", celda_head),
            Paragraph("ID", celda_head),
            Paragraph("Categoría", celda_head),
            Paragraph("Distrito / Zona", celda_head),
            Paragraph("Descripción", celda_head),
            Paragraph("Grav.", celda_head),
            Paragraph("Poblac.", celda_head),
            Paragraph("Días", celda_head),
            Paragraph("Puntaje", celda_head),
            Paragraph("Prioridad", celda_head),
            Paragraph("Estado", celda_head)
        ]]

        for r in ranking:
            desc_corta = (r.get("descripcion", "")[:45] + "...") if len(r.get("descripcion", "")) > 45 else r.get("descripcion", "")
            datos_tabla.append([
                Paragraph(str(r.get("ranking_posicion", "")), celda_style),
                Paragraph(f"#{r.get('id', '')}", celda_style),
                Paragraph(r.get("categoria", ""), celda_style),
                Paragraph(f"{r.get('distrito', '')} ({r.get('zona', '')})", celda_style),
                Paragraph(desc_corta, celda_style),
                Paragraph(str(r.get("gravedad", "")), celda_style),
                Paragraph(f"{r.get('poblacion_afectada', 0):,}", celda_style),
                Paragraph(str(r.get("tiempo_sin_resolver", 0)), celda_style),
                Paragraph(f"<b>{r.get('puntaje', 0.0)}</b>", celda_style),
                Paragraph(r.get("clasificacion", ""), celda_style),
                Paragraph(r.get("estado", ""), celda_style)
            ])

        tabla = Table(datos_tabla, colWidths=[30, 25, 65, 80, 210, 32, 45, 30, 45, 55, 55])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ]))
        elementos.append(tabla)

        elementos.append(Spacer(1, 10))
        pie_texto = f"Generado oficialmente el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} · Total: {len(ranking)} reportes."
        elementos.append(Paragraph(pie_texto, subtitulo_style))

        doc.build(elementos)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"ranking_ia_municipal_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mimetype="application/pdf"
        )

    except ImportError:
        return render_template("exportar_print.html", ranking=ranking, fecha=datetime.now())


# =============================================================================
# INICIO DEL SERVIDOR
# =============================================================================
if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    print(f"[*] Servidor IA Municipal en ejecución en http://localhost:{puerto}")
    app.run(host="0.0.0.0", port=puerto, debug=False)
