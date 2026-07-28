# Ejemplo: Ruta de catálogos con HTMX inline editing
# Archivo: app/api/catalogs.py

from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth.session import get_current_user, require_admin
from app.database.models import User
from app.catalogs.repository import CategoryRepository, AccountRepository
from app.users.repository import UserRepository

router = APIRouter(prefix="/catalogs", tags=["catalogs"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
@require_admin
async def catalogs_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "catalogs.html",
        {"request": request, "current_user": current_user, "active_tab": "categories"},
    )


# ─── Categories ───────────────────────────────────────────────────────────

@router.get("/categories", response_class=HTMLResponse)
@require_admin
async def categories_list(request: Request, current_user: User = Depends(get_current_user)):
    repo = CategoryRepository()
    categories = await repo.get_all_categories(include_inactive=True)
    return templates.TemplateResponse(
        "partials/catalogs/categories.html",
        {"request": request, "current_user": current_user, "categories": categories},
    )


@router.post("/categories", response_class=HTMLResponse)
@require_admin
async def categories_create(
    request: Request,
    code: str = Form(...),
    description: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    repo = CategoryRepository()
    # Check duplicate code
    existing = await repo.get_by_code(code)
    if existing:
        return templates.TemplateResponse(
            "partials/catalogs/categories.html",
            {"request": request, "current_user": current_user,
             "categories": await repo.get_all_categories(include_inactive=True),
             "error": f"El código '{code}' ya existe"},
            status_code=409,
        )
    await repo.create_category(code, description)
    categories = await repo.get_all_categories(include_inactive=True)
    response = templates.TemplateResponse(
        "partials/catalogs/categories.html",
        {"request": request, "current_user": current_user, "categories": categories,
         "success": f"Categoría '{code}' creada"},
    )
    response.headers["HX-Trigger"] = "catalog-updated"
    return response


@router.put("/categories/{category_id}", response_class=HTMLResponse)
@require_admin
async def categories_update(
    request: Request,
    category_id: int,
    code: str = Form(...),
    description: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    repo = CategoryRepository()
    await repo.update_category(category_id, code, description)
    categories = await repo.get_all_categories(include_inactive=True)
    response = templates.TemplateResponse(
        "partials/catalogs/categories.html",
        {"request": request, "current_user": current_user, "categories": categories,
         "success": f"Categoría '{code}' actualizada"},
    )
    response.headers["HX-Trigger"] = "catalog-updated"
    return response


@router.delete("/categories/{category_id}", response_class=HTMLResponse)
@require_admin
async def categories_deactivate(
    request: Request,
    category_id: int,
    current_user: User = Depends(get_current_user),
):
    repo = CategoryRepository()
    usage_count = await repo.is_category_in_use(category_id)
    await repo.deactivate_category(category_id)
    categories = await repo.get_all_categories(include_inactive=True)
    if usage_count > 0:
        msg = f"Categoría desactivada. Está en uso en {usage_count} registros existentes."
    else:
        msg = "Categoría desactivada correctamente."
    response = templates.TemplateResponse(
        "partials/catalogs/categories.html",
        {"request": request, "current_user": current_user, "categories": categories,
         "warning": msg},
    )
    response.headers["HX-Trigger"] = "catalog-updated"
    return response


@router.get("/categories/active", response_class=HTMLResponse)
async def categories_active(request: Request):
    """Returns <option> tags for expense form dropdown."""
    repo = CategoryRepository()
    categories = await repo.get_active_categories()
    options = "".join(
        f'<option value="{c.id}">{c.code} - {c.description}</option>'
        for c in categories
    )
    return HTMLResponse(content=options)


# ─── Accounts (same pattern) ──────────────────────────────────────────────

# GET /catalogs/accounts
# POST /catalogs/accounts
# PUT /catalogs/accounts/{id}
# DELETE /catalogs/accounts/{id}
# GET /catalogs/accounts/active


# ─── Users ─────────────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
@require_admin
async def users_list(request: Request, current_user: User = Depends(get_current_user)):
    repo = UserRepository()
    users = await repo.get_all_users()
    return templates.TemplateResponse(
        "partials/catalogs/users.html",
        {"request": request, "current_user": current_user, "users": users},
    )


@router.post("/users", response_class=HTMLResponse)
@require_admin
async def users_create(
    request: Request,
    username: str = Form(...),
    initial_password: str = Form(...),
    role: str = Form("estandar"),
    current_user: User = Depends(get_current_user),
):
    from app.auth.service import AuthService
    repo = UserRepository()
    hashed = AuthService.hash_password(initial_password)
    await repo.create_user(username, hashed, role, must_change_password=True)
    users = await repo.get_all_users()
    response = templates.TemplateResponse(
        "partials/catalogs/users.html",
        {"request": request, "current_user": current_user, "users": users,
         "success": f"Usuario '{username}' creado"},
    )
    return response


@router.post("/users/{user_id}/reset-password", response_class=HTMLResponse)
@require_admin
async def users_reset_password(
    request: Request,
    user_id: int,
    new_password: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    from app.auth.service import AuthService
    repo = UserRepository()
    hashed = AuthService.hash_password(new_password)
    await repo.update_user(user_id, password_hash=hashed, must_change_password=True)
    users = await repo.get_all_users()
    response = templates.TemplateResponse(
        "partials/catalogs/users.html",
        {"request": request, "current_user": current_user, "users": users,
         "success": "Contraseña restablecida. El usuario deberá cambiarla en su próximo inicio."},
    )
    return response


@router.post("/users/{user_id}/unlock", response_class=HTMLResponse)
@require_admin
async def users_unlock(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    repo = UserRepository()
    await repo.unlock_user(user_id)
    users = await repo.get_all_users()
    return templates.TemplateResponse(
        "partials/catalogs/users.html",
        {"request": request, "current_user": current_user, "users": users,
         "success": "Usuario desbloqueado"},
    )
