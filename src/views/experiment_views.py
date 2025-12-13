from fastapi import APIRouter, Request, Form, Depends, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import os
from pathlib import Path
import logging
from datetime import datetime
from src.database import get_db
from src.services import auth as auth_service

logger = logging.getLogger(__name__)

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

EXPERIMENT_API_BASE = os.getenv("EXPERIMENT_API_BASE", "http://localhost:8000/api/experiments/")
SESSION_COOKIE_NAME = "session_api_key"


async def get_or_create_session_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> str:

    existing_key = request.cookies.get(SESSION_COOKIE_NAME)

    if existing_key:
        return existing_key

    new_key = await auth_service.create_api_key(db, "web_session")

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=new_key.key,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",
        samesite="lax",
        max_age=None
    )

    return new_key.key


@router.get("/experiments")
async def list_experiments(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # Get or create session token
    api_key = await get_or_create_session_token(request, response, db)

    experiments = []
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = await client.get(EXPERIMENT_API_BASE, headers=headers)
            if resp.status_code == 200 and resp.text:
                experiments = resp.json()

                for exp in experiments:
                    if exp.get("created_at"):
                        dt = datetime.fromisoformat(exp["created_at"].replace("Z", "+00:00"))
                        
                        exp["created_at_formatted"] = dt.strftime("%B %d, %Y")
            else:
                logger.warning(f"Failed to fetch experiments: status_code={resp.status_code}")
    except Exception as e:
        logger.error(f"Error fetching experiments: {str(e)}")

    return templates.TemplateResponse(
        "experiment_list.html",
        {"request": request, "experiments": experiments}
    )


@router.get("/experiment/{experiment_id}")
async def view_experiment(
    experiment_id: int,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # Get or create session token
    api_key = await get_or_create_session_token(request, response, db)

    experiment = None
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = await client.get(f"{EXPERIMENT_API_BASE}{experiment_id}", headers=headers)
            if resp.status_code == 200 and resp.text:
                experiment = resp.json()

                # Format dates
                if experiment.get("created_at"):
                    dt = datetime.fromisoformat(experiment["created_at"].replace("Z", "+00:00"))
                    experiment["created_at_formatted"] = dt.strftime("%B %d, %Y")

                if experiment.get("started_at"):
                    dt = datetime.fromisoformat(experiment["started_at"].replace("Z", "+00:00"))
                    experiment["started_at_formatted"] = dt.strftime("%B %d, %Y")

                if experiment.get("ended_at"):
                    dt = datetime.fromisoformat(experiment["ended_at"].replace("Z", "+00:00"))
                    experiment["ended_at_formatted"] = dt.strftime("%B %d, %Y")

                # Format variant dates
                for variant in experiment.get("variants", []):
                    if variant.get("created_at"):
                        dt = datetime.fromisoformat(variant["created_at"].replace("Z", "+00:00"))
                        variant["created_at_formatted"] = dt.strftime("%B %d, %Y")
            else:
                logger.warning(f"Failed to fetch experiment {experiment_id}: status_code={resp.status_code}")
    except Exception as e:
        logger.error(f"Error fetching experiment {experiment_id}: {str(e)}")

    return templates.TemplateResponse(
        "experiment_view.html",
        {"request": request, "experiment": experiment}
    )


@router.post("/experiments")
async def create_experiment(
    request: Request,
    response: Response,
    name: str = Form(...),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle experiment creation from the web UI."""
    # Get or create session token
    api_key = await get_or_create_session_token(request, response, db)

    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            body = {"name": name, "description": description}
            resp = await client.post(EXPERIMENT_API_BASE, headers=headers, json=body)

            if resp.status_code == 200:
                return RedirectResponse(url="/ui/experiments", status_code=303)
            else:
                logger.error(f"Failed to create experiment: {resp.status_code} - {resp.text}")
                # Return to list page with error (you could add error flash messaging)
                return RedirectResponse(url="/ui/experiments", status_code=303)
    except Exception as e:
        logger.error(f"Error creating experiment: {str(e)}")
        return RedirectResponse(url="/ui/experiments", status_code=303)