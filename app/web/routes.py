from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.domain.models import AccountStatus
from app.web.dependencies import get_container

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("landing.html", {"request": request, "analysis": None, "error": None})


@router.post("/demo/analyze", response_class=HTMLResponse)
def demo_analyze(request: Request, source_url: str = Form(...), container=Depends(get_container)) -> HTMLResponse:
    try:
        analysis = container["analysis_service"].analyze_demo_url(source_url)
    except ValueError as exc:
        return templates.TemplateResponse(
            "landing.html",
            {"request": request, "analysis": None, "error": str(exc)},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return templates.TemplateResponse("landing.html", {"request": request, "analysis": analysis, "error": None})


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request, source_url: str = "") -> HTMLResponse:
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "source_url": source_url, "error": None},
    )


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
    source_url: str = Form(...),
    container=Depends(get_container),
) -> RedirectResponse | HTMLResponse:
    try:
        user = container["onboarding_service"].register_user_with_trial(email=email, full_name=full_name, source_url=source_url)
    except ValueError as exc:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "source_url": source_url, "error": str(exc)},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse(url=f"/dashboard/{user.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard/{user_id}", response_class=HTMLResponse)
def dashboard(request: Request, user_id: str, container=Depends(get_container)) -> HTMLResponse:
    user = container["users_repo"].get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    locations = container["locations_repo"].list_for_user(user_id)
    reviews = container["reviews_repo"].list_for_user(locations)
    subscription = container["subscriptions_repo"].get_by_user(user_id)
    max_locations = subscription.locations_limit() if subscription else 1
    location_count = len(locations)
    trial_left_days = max((user.trial_ends_at - datetime.now(timezone.utc)).days, 0)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "locations": locations,
            "reviews": reviews[-30:],
            "location_count": location_count,
            "max_locations": max_locations,
            "trial_left_days": trial_left_days,
            "limit": max_locations,
        },
    )


@router.post("/dashboard/{user_id}/locations")
def add_location(user_id: str, source_url: str = Form(...), container=Depends(get_container)) -> RedirectResponse:
    try:
        container["onboarding_service"].add_location(user_id=user_id, source_url=source_url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RedirectResponse(url=f"/dashboard/{user_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/dashboard/{user_id}/monitor")
def run_monitoring(user_id: str, container=Depends(get_container)) -> RedirectResponse:
    try:
        container["monitoring_service"].run_for_user(user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RedirectResponse(url=f"/dashboard/{user_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/dashboard/{user_id}/trial-report", response_class=HTMLResponse)
def report(request: Request, user_id: str, container=Depends(get_container)) -> HTMLResponse:
    user = container["users_repo"].get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    locations = container["locations_repo"].list_for_user(user_id)
    reviews = container["reviews_repo"].list_for_user(locations)
    report_data = container["reporting_service"].build_trial_report(user, reviews)
    return templates.TemplateResponse("report.html", {"request": request, "user": user, "report": report_data})


@router.post("/dashboard/{user_id}/subscribe")
def upgrade_subscription(user_id: str, container=Depends(get_container)) -> RedirectResponse:
    try:
        container["onboarding_service"].activate_subscription(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RedirectResponse(url=f"/dashboard/{user_id}", status_code=status.HTTP_303_SEE_OTHER)
