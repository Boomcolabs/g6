import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Path, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import ProgrammingError
from starlette.staticfiles import StaticFiles

from core import models
from core.database import DBConnect
from core.exception import AlertException, regist_core_exception_handler, template_response
from core.middleware import regist_core_middleware, should_run_middleware
from core.plugin import (
    cache_plugin_menu, cache_plugin_state, get_plugin_state_change_time,
    import_plugin_by_states, read_plugin_state, register_plugin,
    register_plugin_admin_menu, register_statics,
)
from core.routers import router as template_router
from core.settings import ENV_PATH, settings
from core.template import register_theme_statics
from lib.common import (
    get_client_ip, is_intercept_ip, is_possible_ip, session_member_key
)
from lib.dependency.dependencies import check_use_template
from lib.member import is_super_admin
from lib.scheduler import scheduler
from lib.token import create_session_token
from service.member_service import MemberService
from service.point_service import PointService
from service.visit_service import VisitService

from admin.admin import router as admin_router
from install.router import router as install_router
from bbs.login import router as login_router

from api.v1.routers import router as api_router

# Load environment variables from .env file.
# This function is used to load key-value pairs from the file as environment variables.
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Defines code to run at app startup and shutdown.
    - Code before yield: executed when the server starts
    - Code after yield: executed when the server shuts down
    """
    yield
    scheduler.remove_flag()

app = FastAPI(
    debug=settings.APP_IS_DEBUG,  # Debug mode activation setting
    lifespan=lifespan,
    title="Gnuboard6",
    description=""
)

# Create data directory if it doesn't exist (e.g., when cloned via git)
if not os.path.exists("data"):
    os.mkdir("data")

# Register files in each path as static files.
register_theme_statics(app)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

# Register plugin routers first
plugin_states = read_plugin_state()
import_plugin_by_states(plugin_states)
register_plugin(plugin_states)
register_statics(app, plugin_states)

cache_plugin_state.__setitem__('info', plugin_states)
cache_plugin_state.__setitem__('change_time', get_plugin_state_change_time())
cache_plugin_menu.__setitem__('admin_menus', register_plugin_admin_menu(plugin_states))

app.include_router(admin_router)
app.include_router(api_router)
app.include_router(template_router)
app.include_router(install_router)
app.include_router(login_router)


@app.middleware("http")
async def main_middleware(request: Request, call_next):
    """Middleware that runs on every request"""

    if not await should_run_middleware(request):
        return await call_next(request)

    # Check if database is installed
    with DBConnect().sessionLocal() as db:
        url_path = request.url.path
        config = None

        try:
            if not url_path.startswith("/install"):
                # Disabled auto-redirect to installer when .env is missing
                # if not os.path.exists(ENV_PATH):
                #     raise AlertException(".env file not found. Please proceed with installation.", 400, "/install")
                # Query basic configuration table
                config = db.scalar(select(models.Config))
            else:
                return await call_next(request)

        except AlertException as e:
            context = {"request": request, "errors": e.detail, "url": e.url}
            return template_response("alert.html", context, e.status_code)

        except ProgrammingError as e:
            context = {
                "request": request,
                "errors": "DB table or configuration information does not exist. Please proceed with the installation again.",
                "url": "/install"
            }
            return template_response("alert.html", context, 400)

        # Query and set basic configuration
        request.state.config = config
        request.state.title = config.cf_title

        # Editor global variables
        request.state.editor = config.cf_editor
        request.state.use_editor = True if config.cf_editor else False

        # Cookie domain global variable
        request.state.cookie_domain = cookie_domain = settings.COOKIE_DOMAIN

        member = None
        is_autologin = False
        ss_mb_key = None
        session_mb_id = request.session.get("ss_mb_id", "")
        cookie_mb_id = request.cookies.get("ck_mb_id", "")
        current_ip = get_client_ip(request)

        try:
            member_service = MemberService(request, db)
            # If login session is active
            if session_mb_id:
                member = member_service.get_member(session_mb_id)
                # Clear session if member info doesn't exist or member is deactivated
                if not member_service.is_activated(member)[0]:
                    request.session.clear()
                    member = None

            # If auto-login cookie exists
            elif cookie_mb_id:
                mb_id = re.sub("[^a-zA-Z0-9_]", "", cookie_mb_id)[:20]
                member = member_service.get_member(session_mb_id)

                # Super admin does not use auto-login feature for security reasons.
                if (not is_super_admin(request, mb_id)
                        and member_service.is_member_email_certified(member)[0]
                        and member_service.is_activated(member)[0]):
                    # Check if the key stored in cookie matches the key generated by server
                    ss_mb_key = session_member_key(request, member)
                    if request.cookies.get("ck_auto") == ss_mb_key:
                        request.session["ss_mb_id"] = cookie_mb_id
                        is_autologin = True
        except AlertException as e:
            context = {"request": request, "errors": e.detail, "url": "/"}
            response = template_response("alert.html", context, e.status_code)
            response.delete_cookie("ck_auto")
            response.delete_cookie("ck_mb_id")
            request.session.clear()
            return response

        if member:
            # If first login today, award points and update login information
            ymd_str = datetime.now().strftime("%Y-%m-%d")
            if member.mb_today_login.strftime("%Y-%m-%d") != ymd_str:
                point_service = PointService(request, db, member_service)
                point_service.save_point(
                    member.mb_id, config.cf_login_point, ymd_str + " First login",
                    "@login", member.mb_id, ymd_str)

                member.mb_today_login = datetime.now()
                member.mb_login_ip = request.client.host
                db.commit()

        # Logged-in member information
        request.state.login_member = member
        # Super admin status
        request.state.is_super_admin = is_super_admin(request, getattr(member, "mb_id", None))

        # Check allowed/blocked IP
        # - Executed after login code because IP check feature verifies is_super_admin status
        if not is_possible_ip(request, current_ip):
            return HTMLResponse("<meta charset=utf-8>Access is not allowed from this IP.")
        if is_intercept_ip(request, current_ip):
            return HTMLResponse("<meta charset=utf-8>Access is blocked from this IP.")

    # Set response object
    response: Response = await call_next(request)

    with DBConnect().sessionLocal() as db:
        age_1day = 60 * 60 * 24

        # Reset auto-login cookie
        # Check is_autologin and session to prevent cookie reset after logout
        if is_autologin and request.session.get("ss_mb_id"):
            response.set_cookie(key="ck_mb_id", value=cookie_mb_id,
                                max_age=age_1day * 30, domain=cookie_domain)
            response.set_cookie(key="ck_auto", value=ss_mb_key,
                                max_age=age_1day * 30, domain=cookie_domain)
        # Record visitor history
        ck_visit_ip = request.cookies.get('ck_visit_ip', None)
        if ck_visit_ip != current_ip:
            response.set_cookie(key="ck_visit_ip", value=current_ip,
                                max_age=age_1day, domain=cookie_domain)
            visit_service = VisitService(request, db)
            visit_service.create_visit_record()

    return response

# Function to add default middleware
# This function must be located below the main_middleware function.
# Otherwise, you may encounter the following error:
# AssertionError: SessionMiddleware must be installed to access request.session
regist_core_middleware(app)

# Function to register default exception handlers
regist_core_exception_handler(app)


# Register and run scheduler
scheduler.run_scheduler()


@app.post("/generate_token",
          include_in_schema=False)
async def generate_token(request: Request) -> JSONResponse:
    """Generate and return session token

    Args:
        request (Request): FastAPI Request object

    Returns:
        JSONResponse: JSON response containing success status and token
    """
    token = create_session_token(request)

    return JSONResponse(content={"success": True, "token": token})


@app.get("/device/change/{device}",
         dependencies=[Depends(check_use_template)],
         include_in_schema=False)
async def device_change(
    request: Request,
    device: str = Path(...)
) -> RedirectResponse:
    """Change access environment (device)
    - Forcefully change between PC/mobile version.

    Args:
        request (Request): FastAPI Request object
        device (str, optional): Device to change to. Defaults to Path(...).

    Returns:
        RedirectResponse: Redirect to previous page
    """
    if (device in ["pc", "mobile"]
            and not settings.IS_RESPONSIVE):
        if device == "pc":
            request.session["is_mobile"] = False
        else:
            request.session["is_mobile"] = True

    referer = request.headers.get("Referer", "/")
    return RedirectResponse(referer, status_code=303)
