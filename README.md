# Sistema ERP - Panadería "La Colorada"

## Descripción General
Este proyecto es un sistema ERP (Enterprise Resource Planning) desarrollado en Django, diseñado específicamente para la administración de las operaciones diarias de la panadería "La Colorada". El sistema centraliza y automatiza el flujo de información en áreas como la producción, inventarios, entregas y ventas de los productos de panadería.

## Características Principales
- **Gestión de Producción y Ventas**: Control y registro en tiempo real de la producción en la panadería matriz y dependencias.
- **Control de Inventarios**: Implementación de conteos de inventario diario en dos etapas (apertura y cierre).
- **Gestión de Pan Frío y Entregas Externas**: Automatización e integración del pan devuelto y la creación flexible de bolsas de productos combinados para el manejo del "Pan Frío".
- **Diseño Responsivo**: Interfaces amigables diseñadas bajo principios modernos, asegurando operaciones ágiles accesibles desde dispositivos móviles.
- **Seguridad**: Autenticación segura para las distintas operaciones por parte del personal de la panadería.

## Tecnologías Utilizadas
- **Backend:** Python + Django
- **Frontend:** HTML, CSS, JavaScript (Renderizado utilizando Django Templates).
- **Base de Datos:** SQLite (configurable a otros gestores mediante variables de entorno).
- **Servidor de Archivos Estáticos:** Whitenoise para compresión y despliegue de contenido estático (assets).
- **Gestión de Entorno:** Integración de configuraciones utilizando `django-environ`.

## Requisitos Previos

Las dependencias principales se encuentran en `requirements.txt`:
- Python 3.8 o superior.
- `Django`
- `django-environ`
- `whitenoise`

## Instalación y Configuración
1. **Clonar este repositorio** en su entorno local (si no lo ha hecho).
2. **Crear y activar un entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux / Mac
   # o
   venv\Scripts\activate  # En Windows
   ```
3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configurar las variables de entorno**: 
   Cree un archivo `.env` en el directorio principal (donde se encuentra `manage.py`) para establecer el acceso a la base de datos, `SECRET_KEY`, y demás configuraciones locales (guíese por la configuración en `core/settings.py`).
5. **Realizar las migraciones de la base de datos**:
   ```bash
   python manage.py migrate
   ```
6. **Crear un super-usuario** para el acceso administrativo inicial:
   ```bash
   python manage.py createsuperuser
   ```
7. **Levantar el entorno de desarrollo**:
   ```bash
   python manage.py runserver
   ```

A partir de este paso, abra en su navegador local [http://127.0.0.1:8000](http://127.0.0.1:8000) para acceder al sistema y validar su funcionamiento.