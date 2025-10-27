"""Installation Template Router"""
import os
import secrets
import shutil
import sys

import fastapi
from cachetools import TTLCache
from dotenv import set_key
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import exists, insert, MetaData, select, Table
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from core.models import (
    Base, Board, Config, DB_TABLE_PREFIX, Content, FaqMaster, Group, Member,
    QaConfig
)
from core.database import DBConnect
from core.exception import AlertException
from core.formclass import InstallFrom
from core.plugin import read_plugin_state, write_plugin_state
from core.settings import ENV_PATH, settings
from install.default_values import (
    default_board_data, default_boards, default_cache_directory, default_config,
    default_contents, default_data_directory, default_faq_master, default_gr_id,
    default_group, default_member, default_qa_config, default_version
)
from lib.common import dynamic_create_write_table, read_license
from lib.dependency.dependencies import validate_install, validate_token
from lib.pbkdf2 import create_hash


INSTALL_TEMPLATES = "install/templates"

router = APIRouter(prefix="/install",
                   tags=["install"],
                   include_in_schema=False)
templates = Jinja2Templates(directory=INSTALL_TEMPLATES)
templates.env.globals["default_version"] = default_version

form_cache = TTLCache(maxsize=1, ttl=60)


@router.get("/",
            name="install_main",
            dependencies=[Depends(validate_install)])
async def main(request: Request):
    """Installation main page"""
    # Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    # FastAPI version
    fastapi_version = f"{fastapi.__version__}"
    context = {
        "request": request,
        "python_version": python_version,
        "fastapi_version": fastapi_version,
    }
    return templates.TemplateResponse("main.html", context)


@router.get("/license",
            name="install_license",
            dependencies=[Depends(validate_install)])
async def install_license(request: Request):
    """License agreement page"""
    context = {
        "request": request,
        "license": read_license(),
    }
    return templates.TemplateResponse("license.html", context)


@router.get("/form",
            dependencies=[Depends(validate_install)])
async def redirect_licence(request: Request):
    """Redirect to license agreement page"""
    return RedirectResponse(url=request.url_for("install_license"))


@router.post("/form",
             name="install_form",
             dependencies=[Depends(validate_install)])
async def install_form(request: Request, agree: str = Form(None)):
    """Installation form page"""
    if agree != "동의함":
        raise AlertException("You must agree to the license to proceed with installation.", 400)
    context = {
        "request": request,
    }
    return templates.TemplateResponse("form.html", context)


@router.post("/",
             name="install",
             dependencies=[Depends(validate_token),
                           Depends(validate_install)])
async def install(
    request: Request,
    form_data: InstallFrom = Depends(),
):
    """Database connection and initialization before installation starts"""
    try:
        # Copy example.env to .env if it exists
        if os.path.exists("example.env"):
            shutil.copyfile("example.env", ENV_PATH)

        # Add database information to .env file
        set_key(ENV_PATH, "DB_ENGINE", form_data.db_engine)
        set_key(ENV_PATH, "DB_HOST", form_data.db_host)
        set_key(ENV_PATH, "DB_PORT", form_data.db_port, quote_mode="never")
        set_key(ENV_PATH, "DB_USER", form_data.db_user)
        set_key(ENV_PATH, "DB_PASSWORD", form_data.db_password)
        set_key(ENV_PATH, "DB_NAME", form_data.db_name)
        set_key(ENV_PATH, "DB_TABLE_PREFIX", form_data.db_table_prefix)
        # Set session secret key in .env
        session_secret_key = secrets.token_urlsafe(50)
        set_key(ENV_PATH, "SESSION_SECRET_KEY", session_secret_key)

        # Apply .env file settings to Settings class
        settings.DB_ENGINE = form_data.db_engine
        settings.DB_HOST = form_data.db_host
        settings.DB_PORT = form_data.db_port
        settings.DB_USER = form_data.db_user
        settings.DB_PASSWORD = form_data.db_password
        settings.DB_NAME = form_data.db_name
        settings.DB_TABLE_PREFIX = form_data.db_table_prefix
        settings.SESSION_SECRET_KEY = session_secret_key

        # Set up database connection
        db = DBConnect()
        db.set_connect_infomation()
        db.create_url()
        if not db.supported_engines.get(form_data.db_engine.lower()):
            raise Exception("Please select a supported database engine.")

        # Create and test new database connection
        db.create_engine()
        connect = db.engine.connect()
        connect.close()

        # Initialize plugin activation
        plugin_list = read_plugin_state()
        for plugin in plugin_list:
            plugin.is_enable = False
        write_plugin_state(plugin_list)

        form_cache.update({"form": form_data})

        # Clear session
        request.session.clear()

        return templates.TemplateResponse("result.html", {"request": request})

    except OperationalError as e:
        os.remove(ENV_PATH)
        message = e._message().replace('"', r'\"').strip()
        raise AlertException(f"Installation failed. Database connection failed.\\n{message}") from e

    except Exception as e:
        os.remove(ENV_PATH)
        raise AlertException(f"Installation failed.\\n{e}") from e


@router.get("/process",
            dependencies=[Depends(validate_token)])
async def install_process():
    """
    Installation progress event stream
    """
    async def install_event():
        db_connect = DBConnect()
        engine = db_connect.engine
        yield "Database connection completed"

        try:
            form_data: InstallFrom = form_cache.get("form")

            # Change table names & update metadata
            tables = Base.metadata.tables.values()
            for table in tables:
                new_table_name = table.name.replace("g6_", form_data.db_table_prefix)
                table.name = new_table_name

            if form_data.reinstall:
                Base.metadata.drop_all(bind=engine)
                # Delete all prefix + 'write_' board tables
                metadata = MetaData()
                metadata.reflect(bind=engine)
                table_names = metadata.tables.keys()
                for name in table_names:
                    if name.startswith(f"{DB_TABLE_PREFIX}write_"):
                        Table(name, metadata, autoload=True).drop(bind=engine)

                yield "Existing database tables deleted"

            Base.metadata.create_all(bind=engine)
            yield "Database tables created"

            with db_connect.sessionLocal() as db:
                config_setup(db, form_data.admin_id, form_data.admin_email)
                if not form_data.is_skip_admin:
                    admin_member_setup(db, form_data.admin_id, form_data.admin_name,
                                    form_data.admin_password, form_data.admin_email)
                content_setup(db)
                qa_setup(db)
                faq_master_setup(db)
                board_group_setup(db)
                board_setup(db)
                db.commit()
                yield "Default configuration data inserted"

            for board in default_boards:
                dynamic_create_write_table(board['bo_table'], create_table=True)
            yield "Board tables created"

            setup_data_directory()
            yield "Data directory created"

            yield f"[success] Congratulations. {default_version} installation completed."

        except Exception as e:
            os.remove(ENV_PATH)
            yield f"[error] Installation failed. {e}"
            raise

    # Execute installation progress event stream
    return EventSourceResponse(install_event())


def config_setup(db: Session, admin_id, admin_email):
    """Register default configuration values"""
    exists_config = db.scalar(
        exists(Config)
        .where(Config.cf_id == 1).select()
    )
    if not exists_config:
        db.execute(
            insert(Config).values(
                cf_admin=admin_id,
                cf_admin_email=admin_email,
                **default_config
            )
        )


def admin_member_setup(db: Session, admin_id: str, admin_name : str,
                       admin_password: str, admin_email: str):
    """Register super admin"""
    admin_member = db.scalar(
        select(Member).where(Member.mb_id == admin_id)
    )
    if admin_member:
        admin_member.mb_password = create_hash(admin_password)
        admin_member.mb_name = admin_name
        admin_member.mb_email = admin_email
    else:
        db.execute(
            insert(Member).values(
                mb_id=admin_id,
                mb_password=create_hash(admin_password),
                mb_name=admin_name,
                mb_nick=admin_name,
                mb_email=admin_email,
                **default_member
            )
        )


def content_setup(db: Session):
    """Register default content values"""
    for content in default_contents:
        exists_content = db.scalar(
            exists(Content)
            .where(Content.co_id == content['co_id']).select()
        )
        if not exists_content:
            db.execute(insert(Content).values(**content))


def qa_setup(db: Session):
    """Register Q&A default values"""

    exists_qa = db.scalar(
        exists(QaConfig).select()
    )
    if not exists_qa:
        db.execute(insert(QaConfig).values(**default_qa_config))


def faq_master_setup(db: Session):
    """Register FAQ Master default values"""
    exists_faq_master = db.scalar(
        exists(FaqMaster)
        .where(FaqMaster.fm_id == 1).select()
    )
    if not exists_faq_master:
        db.execute(insert(FaqMaster).values(**default_faq_master))


def board_group_setup(db: Session):
    """Create default board group values"""
    exists_board_group = db.scalar(
        exists(Group)
        .where(Group.gr_id == default_gr_id).select()
    )
    if not exists_board_group:
        db.execute(insert(Group).values(**default_group))


def board_setup(db: Session):
    """Create default board values and tables"""
    for board in default_boards:
        exists_board = db.scalar(
            exists(Board)
            .where(Board.bo_table == board['bo_table']).select()
        )
        if not exists_board:
            query = insert(Board).values(**board, **default_board_data)
            db.execute(query)


def setup_data_directory():
    """Initialize data directory"""
    # Create data directory
    os.makedirs(default_data_directory, exist_ok=True)
    # Clear cache directory
    if os.path.exists(default_cache_directory):
        shutil.rmtree(default_cache_directory)
    # Create cache directory
    os.makedirs(default_cache_directory)
