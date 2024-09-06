# Pasos seguidos para el desarrollo de WellTrack IA

# PYENV/COMMANDS
- Listar versiones disponibles
pyenv versions

- Cambiar de version especificada
pyenv local system

- Instalar nueva versión
pyenv install 3.12.3
pyenv install 3.10.14

- Desinstalar versión
pyenv uninstall 3.12.3

- Cambiar a la version instalada para desarrollo
pyenv local 3.10.14

# SISTEMA OPERATIVO
lsb_release -a

# Crear carpeta principal de proyecto
mkdir welltrack_ia
cd welltrack_ia/

# Crear el entorno virtual del proyecto
python3 -m venv .venv

# Activar el entorno virtual creado
source .venv/bin/activate

# Crear el archivo de requerimientos
nano requirements.txt

# Instalar requerimientos
pip install -r requirements.txt

# Actualizando y utilizando pip
pip install --upgrade pip

# Crear Proyecto Django
django-admin startproject welltrack_ia .

# Ejecutar el proyecto
python manage.py runserver

# Crear carpeta para estructura del proyecto
mkdir apps
mkdir media
mkdir static
mkdir templates


# Crear aplicaciones del proyecto
cd apps/
django-admin startapp home
django-admin startapp employee
django-admin startapp api

# Creando la base de datos de desarrollo
python manage.py migrate

# Creando migraciones
python manage.py makemigrations
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser


# Internacionalización
python manage.py makemessages -l es

# Algoritmo a utilizar 
- DeepFace
- InsightFace

# REDIS PARA ASYNC
TERMINAL 1
$ redis-server

TERMINAL 2
(venv) $ celery -A welltrack_ia worker --loglevel=info

# APAGAR WSL2
wsl --shutdown
