# MultipleFiles/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, DateField, SelectField, TextAreaField, DateTimeField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, URL # Import URL
from flask_wtf.file import FileAllowed
from models import User
from datetime import date, datetime # Importar datetime aquí también

# Validador para asegurar que la fecha no sea futura
def fecha_no_futura(form, field):
    if field.data > date.today():
        raise ValidationError("La fecha no puede ser posterior a hoy.")

class RegistrationForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellido = StringField('Apellido', validators=[DataRequired()])
    edad = IntegerField('Edad', validators=[DataRequired()])
    rol = SelectField('Rol', choices=[('Estudiante', 'Estudiante'), ('Padre', 'Padre'), ('Docente', 'Docente')], validators=[DataRequired()])
    # El campo grado es opcional a menos que el rol sea 'Estudiante'
    grado = SelectField('Grado Escolar', choices=[
        ('', 'Selecciona un grado'), # Opción vacía para cuando no es estudiante
        ('Primero de Primaria', 'Primero de Primaria'),
        ('Segundo de Primaria', 'Segundo de Primaria'),
        ('Tercero de Primaria', 'Tercero de Primaria'),
        ('Cuarto de Primaria', 'Cuarto de Primaria'),
        ('Quinto de Primaria', 'Quinto de Primaria'),
        ('Sexto de Primaria', 'Sexto de Primaria'),
        ('Séptimo de Primaria', 'Séptimo de Primaria'),
        ('Octavo de Primaria', 'Octavo de Primaria'),
        ('Noveno de Primaria', 'Noveno de Primaria'),
        ('10 de Secundaria', '10 de Secundaria'),
        ('11 de Secundaria', '11 de Secundaria')
    ], validators=[Optional()]) # Usar Optional() para permitir que sea nulo

    fecha_inscripcion = DateField('Fecha de Inscripción', validators=[DataRequired(), fecha_no_futura])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8), EqualTo('confirm_password', message='Las contraseñas deben coincidir')])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired()])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('El correo electrónico ya está registrado.')
    
    # Validar el campo grado condicionalmente
    def validate_grado(self, field):
        if self.rol.data == 'Estudiante' and not field.data:
            raise ValidationError('El grado escolar es obligatorio para los estudiantes.')


class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    remember = BooleanField('Recordarme')

class EventForm(FlaskForm):
    titulo = StringField('Título', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción', validators=[DataRequired()])
    fecha_inicio = DateTimeField('Fecha de Inicio', format='%Y-%m-%dT%H:%M', validators=[DataRequired()], render_kw={'type': 'datetime-local'})
    fecha_fin = DateTimeField('Fecha de Fin', format='%Y-%m-%dT%H:%M', validators=[DataRequired()], render_kw={'type': 'datetime-local'})
    ubicacion = StringField('Ubicación', validators=[DataRequired()])
    imagen = FileField('Imagen del Evento', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo se permiten imágenes JPG, JPEG y PNG.')]) # New field

    # CORRECCIÓN: Añadidas validaciones para el rango de años de las fechas
    def validate_fecha_inicio(self, field):
        if field.data: # Solo validar si hay datos
            # SQL Server datetime range starts from 1753-01-01
            if field.data.year < 1753:
                raise ValidationError('El año de la fecha de inicio no puede ser anterior a 1753.')
            # Opcional: Si los eventos no pueden ser en el pasado
            # if field.data < datetime.now():
            #     raise ValidationError('La fecha de inicio no puede ser en el pasado.')

    def validate_fecha_fin(self, field):
        if field.data: # Solo validar si hay datos
            if field.data.year < 1753:
                raise ValidationError('El año de la fecha de fin no puede ser anterior a 1753.')
            if self.fecha_inicio.data and field.data < self.fecha_inicio.data:
                raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')
            # Opcional: Si los eventos no pueden ser en el pasado
            # if field.data < datetime.now():
            #     raise ValidationError('La fecha de fin no puede ser en el pasado.')

# Nuevo formulario para publicaciones del foro
class ForumPostForm(FlaskForm):
    titulo = StringField('Título de la Publicación', validators=[DataRequired(), Length(max=255)])
    contenido = TextAreaField('Contenido', validators=[DataRequired()])
    imagen = FileField('Imagen (opcional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Solo se permiten imágenes JPG, JPEG y PNG.'), Optional()])
    video_url = StringField('URL de Video (opcional)', validators=[Optional(), URL(message='Por favor, introduce una URL válida.')])

