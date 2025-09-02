from flask import Flask, render_template, request, redirect, url_for, flash, abort, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
from models import db, User, Evento, event_attendees, ForumPost
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, EventForm, ForumPostForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, func, Date
import io
import base64
import re
import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

with app.app_context():
    db.configure_mappers()
    db.create_all()

@app.route('/')
def index():
    eventos = Evento.query.order_by(Evento.fecha_inicio).limit(3).all()
    return render_template('index.html', eventos=eventos)

@app.route('/registrar/', methods=['GET', 'POST'])
def registrar():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            grado_data = form.grado.data if form.rol.data == 'Estudiante' else None
            is_admin_data = True if form.rol.data == 'admin' else False
            
            nuevo_usuario = User(
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                edad=form.edad.data,
                rol=form.rol.data,
                grado=grado_data,
                fecha_inscripcion=form.fecha_inscripcion.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                is_admin=is_admin_data
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('¡Usuario registrado exitosamente!', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('El correo electrónico ya está registrado. Por favor, usa otro.', 'error')
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al registrar el usuario: {e}")
            flash(f'Error al registrar el usuario: {str(e)}', 'error')
    else:
        if request.method == 'POST':
            print("❌ Errores en el formulario de registro:")
            print(form.errors)
    return render_template('registro.html', form=form)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('Correo o contraseña incorrectos', 'error')
        elif not check_password_hash(user.password, form.password.data):
            flash('Correo o contraseña incorrectos', 'error')
        else:
            login_user(user, remember=form.remember.data)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
    return render_template('login.html', form=form)

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión", "info")
    return redirect(url_for('index'))

@app.route('/eventos/')
def eventos():
    eventos = Evento.query.order_by(Evento.fecha_inicio).all()
    return render_template('eventos.html', eventos=eventos)

@app.route('/eventos/crear/', methods=['GET', 'POST'])
@login_required
def crear_evento():
    if not current_user.is_admin:
        flash('No tienes permisos para crear eventos.', 'error')
        abort(403)

    form = EventForm()
    if form.validate_on_submit():
        print(f"DEBUG: form.fecha_inicio.data = {form.fecha_inicio.data}")
        print(f"DEBUG: form.fecha_fin.data = {form.fecha_fin.data}")

        imagen_data = None
        imagen_mimetype = None
        if form.imagen.data:
            imagen_data = form.imagen.data.read()
            imagen_mimetype = form.imagen.data.mimetype

        try:
            nuevo_evento = Evento(
                titulo=form.titulo.data,
                descripcion=form.descripcion.data,
                fecha_inicio=form.fecha_inicio.data,
                fecha_fin=form.fecha_fin.data,
                ubicacion=form.ubicacion.data,
                organizador_id=current_user.id,
                imagen_data=imagen_data,
                imagen_mimetype=imagen_mimetype
            )
            db.session.add(nuevo_evento)
            db.session.commit()
            flash('✅ ¡Evento creado exitosamente!', 'success')
            return redirect(url_for('eventos'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear evento: {e}")
            flash(f'Error al crear el evento: {str(e)}', 'error')
    else:
        if request.method == 'POST':
            print("❌ Errores en formulario de evento:")
            print(form.errors)
            if 'imagen' in form.errors:
                flash(f"Error en la imagen: {', '.join(form.errors['imagen'])}", 'error')
    return render_template('crear_evento.html', form=form)

@app.route('/eventos/registrar/<int:event_id>/', methods=['POST'])
@login_required
def registrar_evento(event_id):
    evento = Evento.query.get_or_404(event_id)
    
    if current_user in evento.attendees:
        flash('Ya estás registrado en este evento.', 'info')
    else:
        try:
            evento.attendees.append(current_user)
            db.session.commit()
            flash(f'✅ Te has registrado exitosamente al evento "{evento.titulo}"!', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al registrar al usuario en el evento: {e}")
            flash(f'Error al registrarse al evento: {str(e)}', 'error')
    return redirect(url_for('eventos'))

@app.route('/eventos/eliminar/<int:event_id>/', methods=['POST'])
@login_required
def eliminar_evento(event_id):
    if not current_user.is_admin:
        flash('No tienes permisos para eliminar eventos.', 'error')
        abort(403)

    evento = Evento.query.get_or_404(event_id)
    try:
        # Asegúrate de que el nombre de la tabla de asociación sea correcto y entre comillas dobles
        db.session.execute(text(f'DELETE FROM "event_attendees" WHERE event_id = {event_id}'))
        db.session.delete(evento)
        db.session.commit()
        flash(f'✅ Evento "{evento.titulo}" eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al eliminar evento: {e}")
        flash(f'Error al eliminar el evento: {str(e)}', 'error')
    return redirect(url_for('eventos'))

@app.route('/soporte-pagos/')
def soporte_pagos():
    return render_template('soporte_pagos.html')

@app.route('/olvide-contrasena/', methods=['GET', 'POST'])
def olvide_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        flash('Si tu correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña.', 'info')
        return redirect(url_for('login'))
    return render_template('olvide_contrasena.html')

@app.route('/eventos/imagen/<int:event_id>/')
def evento_imagen(event_id):
    evento = Evento.query.get_or_404(event_id)
    if evento.imagen_data and evento.imagen_mimetype:
        return Response(evento.imagen_data, mimetype=evento.imagen_mimetype)
    return Response("No image available", status=404)

@app.route('/club-info/')
def club_info():
    return render_template('club_info.html')

@app.route('/foro/')
def foro():
    posts = ForumPost.query.order_by(ForumPost.fecha_creacion.desc()).all()
    return render_template('forum.html', posts=posts)

@app.route('/foro/crear/', methods=['GET', 'POST'])
@login_required
def crear_post():
    if not current_user.is_admin:
        flash('No tienes permisos para crear publicaciones en el foro.', 'error')
        abort(403)

    form = ForumPostForm()
    if form.validate_on_submit():
        imagen_data = None
        imagen_mimetype = None
        if form.imagen.data:
            imagen_data = form.imagen.data.read()
            imagen_mimetype = form.imagen.data.mimetype
        
        video_id = None
        if form.video_url.data:
            youtube_regex = (
                r'(https?://)?(www\.)?'
                r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
                r'(watch\?v=|embed/|v/|.+\?v=)?([^&?]{11})')
            match = re.match(youtube_regex, form.video_url.data)
            if match:
                video_id = match.group(6)
            else:
                flash('URL de video no válida. Solo se admiten URLs de YouTube.', 'error')
                return render_template('crear_post.html', form=form)

        try:
            nuevo_post = ForumPost(
                titulo=form.titulo.data,
                contenido=form.contenido.data,
                imagen_data=imagen_data,
                imagen_mimetype=imagen_mimetype,
                video_url=video_id,
                autor_id=current_user.id
            )
            db.session.add(nuevo_post)
            db.session.commit()
            flash('✅ Publicación del foro creada exitosamente!', 'success')
            return redirect(url_for('foro'))
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear publicación del foro: {e}")
            flash(f'Error al crear la publicación: {str(e)}', 'error')
    else:
        if request.method == 'POST':
            print("❌ Errores en formulario de publicación del foro:")
            print(form.errors)
            if 'imagen' in form.errors:
                flash(f"Error en la imagen: {', '.join(form.errors['imagen'])}", 'error')
            if 'video_url' in form.errors:
                flash(f"Error en la URL del video: {', '.join(form.errors['video_url'])}", 'error')
    return render_template('crear_post.html', form=form)

@app.route('/foro/eliminar/<int:post_id>/', methods=['POST'])
@login_required
def eliminar_post(post_id):
    if not current_user.is_admin:
        flash('No tienes permisos para eliminar publicaciones del foro.', 'error')
        abort(403)

    post = ForumPost.query.get_or_404(post_id)
    try:
        db.session.delete(post)
        db.session.commit()
        flash(f'✅ Publicación "{post.titulo}" eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al eliminar publicación del foro: {e}")
        flash(f'Error al eliminar la publicación: {str(e)}', 'error')
    return redirect(url_for('foro'))


@app.route('/foro/imagen/<int:post_id>/')
def foro_imagen(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if post.imagen_data and post.imagen_mimetype:
        return Response(post.imagen_data, mimetype=post.imagen_mimetype)
    return Response("No image available", status=404)

@app.route('/analisis')
@login_required
def analisis():
    if not current_user.is_admin:
        flash('Acceso restringido: Solo administradores', 'error')
        return redirect(url_for('index'))

    try:
        plt.style.use('dark_background')
        plt.rcParams.update({
            'text.color': 'white',
            'axes.labelcolor': 'white',
            'xtick.color': 'white',
            'ytick.color': 'white',
            'axes.edgecolor': '#FFD700',
            'figure.facecolor': '#1a1a1a',
            'axes.facecolor': 'black',
            'grid.color': '#333333',
            'grid.linestyle': '--',
            'grid.alpha': 0.7,
            'font.size': 12,
            'axes.titlesize': 16,
            'axes.titlecolor': '#FFD700'
        })

        # 1. Gráfica: Usuarios por evento
        usuarios_por_evento_data = db.session.query(
            Evento.titulo,
            func.count(event_attendees.c.user_id)
        ).join(event_attendees).group_by(Evento.titulo).all()

        df_usuarios_por_evento = pd.DataFrame(usuarios_por_evento_data, columns=['nombre_evento', 'total_usuarios'])

        plt.figure(figsize=(10, 6))
        plt.bar(df_usuarios_por_evento['nombre_evento'], df_usuarios_por_evento['total_usuarios'], color='#FFD700')
        plt.xlabel('Evento')
        plt.ylabel('Cantidad de Usuarios')
        plt.title('Usuarios Registrados por Evento')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        img_usuarios_por_evento = io.BytesIO()
        plt.savefig(img_usuarios_por_evento, format='png', bbox_inches='tight')
        plt.close()
        img_usuarios_por_evento.seek(0)
        plot_url_usuarios_por_evento = base64.b64encode(img_usuarios_por_evento.getvalue()).decode()

        # 2. Gráfica: Eventos por Fecha (agrupado por mes y año)
        eventos_por_fecha_data = db.session.query(
            text("TO_CHAR(fecha_inicio, 'YYYY-MM') AS fecha_mes"), # CAMBIO PARA POSTGRESQL
            func.count(Evento.id)
        ).group_by(
            text("TO_CHAR(fecha_inicio, 'YYYY-MM')") # CAMBIO PARA POSTGRESQL
        ).order_by(
            text("fecha_mes")
        ).all()

        df_eventos_por_fecha = pd.DataFrame(eventos_por_fecha_data, columns=['mes_año', 'total_eventos'])

        plt.figure(figsize=(10, 6))
        plt.plot(df_eventos_por_fecha['mes_año'], df_eventos_por_fecha['total_eventos'], marker='o', color='#FFD700', linestyle='-')
        plt.xlabel('Mes y Año')
        plt.ylabel('Cantidad de Eventos')
        plt.title('Eventos por Mes y Año')
        plt.xticks(rotation=45, ha='right')
        plt.grid(True)
        plt.tight_layout()
        img_eventos_por_fecha = io.BytesIO()
        plt.savefig(img_eventos_por_fecha, format='png', bbox_inches='tight')
        plt.close()
        img_eventos_por_fecha.seek(0)
        plot_url_eventos_por_fecha = base64.b64encode(img_eventos_por_fecha.getvalue()).decode()

        # 3. Gráfica: TOP 20 Usuarios Más Activos
        usuarios_activos_data = db.session.query(
            User.nombre,
            func.count(event_attendees.c.event_id)
        ).join(event_attendees).group_by(User.nombre).order_by(func.count(event_attendees.c.event_id).desc()).limit(20).all()

        df_usuarios_activos = pd.DataFrame(usuarios_activos_data, columns=['user_name', 'eventos_asistidos'])
        df_usuarios_activos = df_usuarios_activos.sort_values(by='eventos_asistidos', ascending=True)

        plt.figure(figsize=(10, 6))
        plt.barh(df_usuarios_activos['user_name'], df_usuarios_activos['eventos_asistidos'], color='#FFD700')
        plt.xlabel('Eventos Asistidos')
        plt.ylabel('Usuario')
        plt.title('TOP 20 Usuarios Más Activos')
        plt.tight_layout()
        img_usuarios_activos = io.BytesIO()
        plt.savefig(img_usuarios_activos, format='png', bbox_inches='tight')
        plt.close()
        img_usuarios_activos.seek(0)
        plot_url_usuarios_activos = base64.b64encode(img_usuarios_activos.getvalue()).decode()

        # 4. NUEVA Gráfica: Usuarios Registrados por Fecha de Inscripción
        # CORRECCIÓN: Delimitar la tabla y la columna correctamente y usar la función CONVERT.
        usuarios_por_inscripcion_data = db.session.query(
            text('"Users".fecha_inscripcion::date AS fecha_inscripcion'), # CAMBIO PARA POSTGRESQL
            func.count(User.id)
        ).group_by(
            text('"Users".fecha_inscripcion::date') # CAMBIO PARA POSTGRESQL
        ).order_by(
            text("fecha_inscripcion")
        ).all()

        df_usuarios_por_inscripcion = pd.DataFrame(usuarios_por_inscripcion_data, columns=['fecha_inscripcion', 'total_usuarios'])

        plt.figure(figsize=(10, 6))
        plt.bar(df_usuarios_por_inscripcion['fecha_inscripcion'], df_usuarios_por_inscripcion['total_usuarios'], color='#FFD700')
        plt.xlabel('Fecha de Inscripción')
        plt.ylabel('Cantidad de Usuarios')
        plt.title('Usuarios Registrados por Fecha de Inscripción')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        img_usuarios_por_inscripcion = io.BytesIO()
        plt.savefig(img_usuarios_por_inscripcion, format='png', bbox_inches='tight')
        plt.close()
        img_usuarios_por_inscripcion.seek(0)
        plot_url_usuarios_por_inscripcion = base64.b64encode(img_usuarios_por_inscripcion.getvalue()).decode()

        return render_template('analisis.html',
                               plot_url_usuarios_por_evento=plot_url_usuarios_por_evento,
                               plot_url_eventos_por_fecha=plot_url_eventos_por_fecha,
                               plot_url_usuarios_activos=plot_url_usuarios_activos,
                               plot_url_usuarios_por_inscripcion=plot_url_usuarios_por_inscripcion)

    except Exception as e:
        print(f"❌ Error al generar análisis: {e}")
        flash(f'Error al generar el análisis: {str(e)}', 'error')
        return render_template('analisis.html', error=f"Error al generar el análisis: {str(e)}")

def handler(event, context):
    with app.app_context():
        db.create_all()
    return app

if __name__ == '__main__':
    app.run(debug=True)
