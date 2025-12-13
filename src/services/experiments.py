from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from src.models import Experiment, Variant, ExperimentSegment, User, UserSegment
from src.schemas.experiments import (
    ExperimentCreate, VariantCreate, VariantUpdate,
    EligibilityCheckRequest, ExperimentVariantInfo
)
from .utils import assign_variant_by_hash
from src.cache import cached, experiment_cache, invalidate_experiment_cache
from typing import List, Dict


async def create_experiment(db: AsyncSession, experiment_data: ExperimentCreate) -> Experiment:
    db_experiment = Experiment(
        name=experiment_data.name,
        description=experiment_data.description
    )
    db.add(db_experiment)
    await db.flush()

    control_variant = Variant(
        experiment_id=db_experiment.id,
        name="control",
        percent_allocated=100.0
    )
    db.add(control_variant)

    await db.commit()
    await db.refresh(db_experiment)
    return db_experiment


@cached(experiment_cache)
async def get_experiments(db: AsyncSession) -> List[Experiment]:
    result = await db.execute(select(Experiment))
    experiments = result.scalars().all()
    return experiments


@cached(experiment_cache)
async def get_experiment_by_id(db: AsyncSession, experiment_id: int) -> Experiment:
    result = await db.execute(
        select(Experiment)
        .options(selectinload(Experiment.variants))
        .options(selectinload(Experiment.segment_assignments).selectinload(ExperimentSegment.segment))
        .filter(Experiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    experiment.segments = [assignment.segment for assignment in experiment.segment_assignments]

    return experiment


async def create_variant(
    db: AsyncSession,
    experiment_id: int,
    variant_data: VariantCreate
) -> Variant:
    result = await db.execute(select(Experiment).filter(Experiment.id == experiment_id))
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    result = await db.execute(select(Variant).filter(Variant.experiment_id == experiment_id))
    existing_variants = result.scalars().all()
    total_allocated = sum(v.percent_allocated for v in existing_variants)

    if total_allocated + variant_data.percent_allocated > 100.0:
        raise HTTPException(
            status_code=400,
            detail=f"Total allocation would exceed 100%. Current: {total_allocated}%, Attempting to add: {variant_data.percent_allocated}%"
        )

    db_variant = Variant(
        experiment_id=experiment_id,
        name=variant_data.name,
        percent_allocated=variant_data.percent_allocated
    )
    db.add(db_variant)
    await db.commit()
    await db.refresh(db_variant)

    invalidate_experiment_cache(experiment_id)

    return db_variant


async def update_variant(
    db: AsyncSession,
    experiment_id: int,
    variant_id: int,
    variant_update: VariantUpdate
) -> Variant:
    result = await db.execute(
        select(Variant).filter(
            Variant.id == variant_id,
            Variant.experiment_id == experiment_id
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    if variant_update.name is not None:
        result = await db.execute(
            select(Variant).filter(
                Variant.experiment_id == experiment_id,
                Variant.name == variant_update.name,
                Variant.id != variant_id
            )
        )
        existing_variant = result.scalar_one_or_none()
        if existing_variant:
            raise HTTPException(
                status_code=400,
                detail=f"A variant with name '{variant_update.name}' already exists in this experiment"
            )
        variant.name = variant_update.name

    if variant_update.percent_allocated is not None:
        result = await db.execute(
            select(Variant).filter(
                Variant.experiment_id == experiment_id,
                Variant.id != variant_id
            )
        )
        other_variants = result.scalars().all()
        total_allocated = sum(v.percent_allocated for v in other_variants)

        if total_allocated + variant_update.percent_allocated > 100.0:
            raise HTTPException(
                status_code=400,
                detail=f"Total allocation would exceed 100%. Current allocation from other variants: {total_allocated}%, Attempting to set: {variant_update.percent_allocated}%"
            )
        variant.percent_allocated = variant_update.percent_allocated

    await db.commit()
    await db.refresh(variant)

    invalidate_experiment_cache(experiment_id)

    return variant


async def check_user_eligibility(
    db: AsyncSession,
    request: EligibilityCheckRequest
) -> Dict[int, ExperimentVariantInfo]:
    result = await db.execute(select(User).filter(User.id == request.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(UserSegment).filter(UserSegment.user_id == request.user_id)
    )
    user_segment_ids = {us.segment_id for us in result.scalars().all()}

    eligible_experiments = {}

    for experiment_id in request.experiment_ids:
        result = await db.execute(
            select(Experiment)
            .options(selectinload(Experiment.variants))
            .filter(Experiment.id == experiment_id)
        )
        experiment = result.scalar_one_or_none()
        if not experiment:
            continue

        result = await db.execute(
            select(ExperimentSegment)
            .options(selectinload(ExperimentSegment.segment))
            .filter(ExperimentSegment.experiment_id == experiment_id)
        )
        experiment_segments = result.scalars().all()

        if not experiment_segments:
            variant_id = assign_variant_by_hash(request.user_id, experiment_id, experiment.variants)
            if variant_id:
                eligible_experiments[experiment_id] = ExperimentVariantInfo(variant_id=variant_id)
            continue

        is_eligible = False
        for exp_segment in experiment_segments:
            segment = exp_segment.segment

            if segment.id in user_segment_ids:
                is_eligible = True
                break

            if segment.rules:
                matches_rules = True
                for rule_key, rule_value in segment.rules.items():
                    user_value = getattr(user, rule_key, None)

                    if user_value != rule_value:
                        matches_rules = False
                        break

                if matches_rules:
                    is_eligible = True
                    break

        if is_eligible:
            variant_id = assign_variant_by_hash(request.user_id, experiment_id, experiment.variants)
            if variant_id:
                eligible_experiments[experiment_id] = ExperimentVariantInfo(variant_id=variant_id)

    return eligible_experiments
