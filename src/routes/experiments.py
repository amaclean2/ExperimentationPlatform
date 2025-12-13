from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas.experiments import (
    ExperimentCreate, ExperimentResponse, ExperimentDetailResponse,
    VariantCreate, VariantUpdate, VariantResponse,
    EligibilityCheckRequest, EligibilityCheckResponse
)
from src.schemas.statistics import ExperimentStatisticsResponse, StatisticsRequest
from src.services import experiments as experiment_service
from src.services.statistics import get_experiment_statistics
from .utils import verify_api_key
from typing import List

router = APIRouter(prefix="/api/experiments", tags=["experiments"], dependencies=[Depends(verify_api_key)])


@router.post("/", response_model=ExperimentResponse)
async def create_experiment(experiment: ExperimentCreate, db: AsyncSession = Depends(get_db)):
    return await experiment_service.create_experiment(db, experiment)


@router.get("/", response_model=List[ExperimentResponse])
async def get_experiments(db: AsyncSession = Depends(get_db)):
    return await experiment_service.get_experiments(db)


@router.get("/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(experiment_id: int, db: AsyncSession = Depends(get_db)):
    return await experiment_service.get_experiment_by_id(db, experiment_id)


@router.post("/{experiment_id}/variants", response_model=VariantResponse)
async def create_variant(
    experiment_id: int,
    variant: VariantCreate,
    db: AsyncSession = Depends(get_db)
):
    return await experiment_service.create_variant(db, experiment_id, variant)


@router.put("/{experiment_id}/variants/{variant_id}", response_model=VariantResponse)
async def update_variant(
    experiment_id: int,
    variant_id: int,
    variant_update: VariantUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await experiment_service.update_variant(db, experiment_id, variant_id, variant_update)


@router.post("/check-eligibility", response_model=EligibilityCheckResponse)
async def check_user_eligibility(
    request: EligibilityCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    eligible_experiments = await experiment_service.check_user_eligibility(db, request)
    return EligibilityCheckResponse(eligible_experiment_ids=eligible_experiments)


@router.post("/{experiment_id}/results", response_model=ExperimentStatisticsResponse)
async def get_experiment_results(
    experiment_id: int,
    request: StatisticsRequest = StatisticsRequest(),
    db: AsyncSession = Depends(get_db)
):
    return await get_experiment_statistics(
        db,
        experiment_id,
        request.conversion_event_type,
        request.confidence_level,
        request.significance_threshold
    )
