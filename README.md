# GNUBOARD6 is Python CMS with fastapi
<p align="center">
   <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/fastapi?logo=python&color=%233776AB">
   <a href='https://g6.demo.sir.kr/' target='_blank'>
      <img alt="Static Badge" src="https://img.shields.io/badge/G6%20Demo-%234d0585">
   </a>
</p>

## Demo Site
- [https://g6.demo.sir.kr/](https://g6.demo.sir.kr/)

## Community
### GNUBOARD6 Community
- [https://sir.kr/main/g6](https://sir.kr/main/g6)

### GNUBOARD YouTube Channel
- [https://www.youtube.com/@gnuboard-official](https://www.youtube.com/@gnuboard-official)

## Getting Started
### 1. Installation
- We recommend installing via Git.
- If there is no `.env` file in the project root, the installer will run automatically.

#### Installation Steps
```bash
# Clone GNUBOARD6 from GitHub
git clone https://github.com/gnuboard/g6.git
```

```bash
# Move into the g6 directory
cd g6
```

```bash
# Create a virtual environment (optional)
python -m venv venv
# or
python3 -m venv venv

# Linux
source venv/bin/activate

# Windows
source venv\Scripts\activate
# or
source venv/Scripts/activate
```

```bash
# Install Python packages required to run the app.
pip install -r requirements.txt
# or
pip3 install -r requirements.txt
```

```bash
# Run GNUBOARD6 with uvicorn.
# Uses port 8000 by default.

# Linux
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Windows
uvicorn main:app --reload
```

#### GNUBOARD6 Database Setup
1. Open your browser and visit **http://127.0.0.1:8000**.
   - Windows: visit http://127.0.0.1:8000 or http://localhost:8000
   - Linux: visit http://<server-ip>:8000
      - Example: if your server IP is 49.247.14.5, visit http://49.247.14.5:8000

2. You'll be redirected to the installer with a message like `.env file not found. Please proceed with installation.`

3. On the installer page, review the GNUBOARD version, Python version, FastAPI version, and notes.

4. Review and accept the GNUBOARD6 license.

5. Configure the database.
   - Choose one of **MySQL, PostgreSQL, SQLite**.
      - MySQL, PostgreSQL: enter connection details.
      - SQLite: no connection info needed; a `sqlite3.db` database file will be created in the project root.
   - Set a table prefix.
      - Must be in the `{letters+numbers}_` format.
      - Default is `g6_` (e.g., gnuboard6_)
   - Optionally enable reinstall.
      > **Warning**  
      > Reinstall drops and recreates tables. Existing data may be lost.

6. Enter admin info to create the admin account.

7. Start installation. When complete, a success message will appear.

8. You can now use GNUBOARD6.

### 2. Directory Structure
#### admin
Contains admin-related files.  
Includes router, template files, and JSON files for admin menu configuration.

#### bbs
User-facing routers handling various requests.

#### core
Project core code: database connections, middleware, template engine setup, etc.
```
core
├─ database.py  # Database connection and session management
├─ exception.py  # Exception handling classes & functions
├─ formclass.py  # Form classes using @dataclass
├─ middleware.py  # Middleware configuration
├─ models.py  # Database models
├─ plugin.py  # Plugin utilities
└─ template.py  # Template engine configuration
```

#### data
Stores uploaded images and files.  
Not present initially; created during installation.

#### install
Contains installer-related files.

#### lib
Helpers and modules used across the project.
```
lib
├─ captcha  # Captcha utilities and templates (Google reCAPTCHA v2, v2 invisible)
├─ editor  # Editor utilities and templates (CKEditor 4)
├─ social  # Social login utilities (Naver, Kakao, Google, Facebook, Twitter)
├─ board_lib.py  # Board-related helpers
├─ common.py  # Common helpers
├─ dependencies.py  # Dependencies
├─ member_lib.py  # Member/user utilities
├─ pbkdf2.py  # Encryption library (PBKDF2)
├─ point.py  # Point system helpers
├─ template_filters.py  # Template filter functions
├─ template_functions.py  # Template rendering helpers
└─ token.py  # Token utilities
```
#### plugin
Directory for user-created plugins.
1. Creating a plugin
   - Add a plugin directory under `/plugin`.
   - Use a unique name to avoid conflicts.
   - Follow the structure below and see `plugin/demo_plugin` as reference.
```
plugin
├─ {plugin1}
   └─ admin  # Admin router & menu config
      ├─ __init__.py 
      └─ admin_router.py
   ├─ static  # Static assets (css, js, images)
   ├─ templates  # Template files
   ├─ user  # User router
   ├─ __init__.py  # Plugin initializer
   ├─ models.py  # Database models
   ├─ plugin_config.py  # Plugin config
   ├─ readme.txt  # Plugin details
   ├─ screenshot.png or .webp  # Thumbnail/preview image
├─ {plugin2}
...
└─ plugin_states.json  # Global plugin state
```
2. Register admin menu URLs
   - Add entries to the `admin_menu` dict in `plugin_config.py`.
      - Menus are registered via `admin/__init__.py > register_admin_menu()`.

#### static
Directory for static assets such as css, js, images.

#### templates
Directory for templates.  
Supports multiple templates; switch via **Admin > Template Management**.
```
templates
├─ {template1}
   └─ ...
├─ {template2}
   └─ ...
...
```
- Responsive/Adaptive
   - The `IS_RESPONSIVE` setting in `.env` controls responsive vs adaptive. For adaptive only, create `templates/{template}/moblile` to provide a separate mobile UI. 
   - If no mobile template exists, the responsive (PC) template will be used.

#### .env (.example.env)
Configuration file. `.example.env` is copied to create `.env` automatically.
     - Keep `.example.env` as a template for generating `.env`.

#### main.py
Entry point of the project. Runs the server using `uvicorn`.
```bash
# Linux
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Windows
uvicorn main:app --reload
```

#### requirements.txt
Lists project dependencies. Install with:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Edit the generated `.env` to change settings.
- True/False values must be strings.
- See `.env.example` for all options.
> **Note**  
> Restart the server after changing settings.

#### Database Settings
```bash
# For SQLite, connection fields are ignored.
# (DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

# Table name prefix
DB_TABLE_PREFIX = "g6_"
# mysql, postgresql, sqlite
DB_ENGINE = ""
DB_USER = "username"
DB_PASSWORD = ""
DB_HOST = ""
DB_PORT = ""
DB_NAME = ""
DB_CHARSET = "utf8"
```
#### Email Settings
```bash
SMTP_SERVER="localhost"
SMTP_PORT=25
# For tests, set the sender name and email.
SMTP_USERNAME="account@your-domain.com"
SMTP_PASSWORD=""

# Example: Naver Mail
# SMTP_SERVER="smtp.naver.com"
# SMTP_PORT=465 # requires SSL
# SMTP_USERNAME="Naver login ID"
# SMTP_PASSWORD="Naver login password"
```

#### Admin Theme
```bash
# Admin theme
# Themes live at /admin/templates/{theme}
# If empty, the default theme (basic) is used.
ADMIN_THEME = "basic"
```

#### Image Settings
```bash
# Whether to resize images
UPLOAD_IMAGE_RESIZE = "False"
# Max image upload size in MB (default 20MB)
UPLOAD_IMAGE_SIZE_LIMIT = 20
# JPG quality (0~100), default 80
UPLOAD_IMAGE_QUALITY = 80

# If UPLOAD_IMAGE_RESIZE is True and images exceed the threshold, they will be resized.
# Resize width (px)
UPLOAD_IMAGE_RESIZE_WIDTH = 1200
# Resize height (px)
UPLOAD_IMAGE_RESIZE_HEIGHT = 2800
```

#### Other Settings
```bash
# Debug mode (True/False)
APP_IS_DEBUG = "False"

# Website display mode (True/False)
# "True" (default): Responsive website (note: only responsive templates are provided)
# "False": Adaptive website
IS_RESPONSIVE = "True"

# www.gnuboard.com and gnuboard.com are treated as different domains.
# To share cookies, set a leading dot like .gnuboard.com.
# If left empty, www and non-www will not share cookies,
# which may cause logins to reset.
COOKIE_DOMAIN = ""
