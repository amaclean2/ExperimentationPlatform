from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from src.models import Experiment, Variant, Event
from src.schemas.statistics import VariantResult, ConfidenceInterval, ExperimentStatisticsResponse, Winner
from typing import Dict, List
import math
from scipy import stats


def calculate_confidence_interval(
    conversions: int,
    total: int,
    confidence_level: float = 0.95
) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)

    p = conversions / total
    z_score = stats.norm.ppf((1 + confidence_level) / 2)

    standard_error = math.sqrt(p * (1 - p) / total)
    margin_of_error = z_score * standard_error

    lower = max(0.0, p - margin_of_error)
    upper = min(1.0, p + margin_of_error)

    return (lower, upper)


def calculate_two_proportion_z_test(
    conversions_control: int,
    total_control: int,
    conversions_variant: int,
    total_variant: int
) -> tuple[float, float]:
    if total_control == 0 or total_variant == 0:
        return (0.0, 1.0)

    p1 = conversions_control / total_control
    p2 = conversions_variant / total_variant

    p_pooled = (conversions_control + conversions_variant) / (total_control + total_variant)

    if p_pooled == 0 or p_pooled == 1:
        return (0.0, 1.0)

    standard_error = math.sqrt(
        p_pooled * (1 - p_pooled) * (1 / total_control + 1 / total_variant)
    )

    if standard_error == 0:
        return (0.0, 1.0)

    z_score = (p2 - p1) / standard_error

    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    return (z_score, p_value)


def calculate_relative_uplift(control_rate: float, variant_rate: float) -> float:
    if control_rate == 0:
        return 0.0
    return ((variant_rate - control_rate) / control_rate) * 100


async def get_experiment_statistics(
    db: AsyncSession,
    experiment_id: int,
    conversion_event_type: str = "conversion",
    confidence_level: float = 0.95,
    significance_threshold: float = 0.05
) -> ExperimentStatisticsResponse:
    result = await db.execute(
        select(Experiment).filter(Experiment.id == experiment_id)
    )
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    result = await db.execute(
        select(Variant).filter(Variant.experiment_id == experiment_id)
    )
    variants = result.scalars().all()

    if not variants:
        raise HTTPException(status_code=400, detail="No variants found for this experiment")

    # Temporary storage for raw variant data
    variant_data: Dict[int, Dict] = {}

    control_variant_data = None
    for variant in variants:
        total_users_result = await db.execute(
            select(func.count(func.distinct(Event.user_id)))
            .filter(Event.variant_id == variant.id)
        )
        total_users = total_users_result.scalar() or 0

        conversions_result = await db.execute(
            select(func.count(func.distinct(Event.user_id)))
            .filter(
                Event.variant_id == variant.id,
                Event.type == conversion_event_type
            )
        )
        conversions = conversions_result.scalar() or 0

        conversion_rate = (conversions / total_users * 100) if total_users > 0 else 0.0

        is_control = variant.name.lower() == "control"

        data = {
            "variant_id": variant.id,
            "variant_name": variant.name,
            "total_users": total_users,
            "conversions": conversions,
            "conversion_rate": conversion_rate,
            "is_control": is_control
        }

        variant_data[variant.id] = data

        if is_control:
            control_variant_data = data

    if not control_variant_data:
        control_variant_data = list(variant_data.values())[0]
        control_variant_data["is_control"] = True

    results: List[VariantResult] = []

    for variant in variants:
        data = variant_data[variant.id]

        if data["variant_id"] == control_variant_data["variant_id"]:
            ci_lower, ci_upper = calculate_confidence_interval(
                data["conversions"],
                data["total_users"],
                confidence_level
            )

            result = VariantResult(
                variant_id=data["variant_id"],
                variant_name=data["variant_name"],
                conversions=data["conversions"],
                total_users=data["total_users"],
                conversion_rate=round(data["conversion_rate"], 2),
                confidence_interval=ConfidenceInterval(
                    lower=round(ci_lower * 100, 2),
                    upper=round(ci_upper * 100, 2)
                ),
                is_control=True
            )
            results.append(result)
        else:
            z_score, p_value = calculate_two_proportion_z_test(
                control_variant_data["conversions"],
                control_variant_data["total_users"],
                data["conversions"],
                data["total_users"]
            )

            ci_lower, ci_upper = calculate_confidence_interval(
                data["conversions"],
                data["total_users"],
                confidence_level
            )

            is_significant = p_value < significance_threshold

            relative_uplift = calculate_relative_uplift(
                control_variant_data["conversion_rate"],
                data["conversion_rate"]
            )

            result = VariantResult(
                variant_id=data["variant_id"],
                variant_name=data["variant_name"],
                conversions=data["conversions"],
                total_users=data["total_users"],
                conversion_rate=round(data["conversion_rate"], 2),
                confidence_interval=ConfidenceInterval(
                    lower=round(ci_lower * 100, 2),
                    upper=round(ci_upper * 100, 2)
                ),
                p_value=round(p_value, 4),
                is_significant=is_significant,
                relative_uplift=round(relative_uplift, 2),
                is_control=False
            )
            results.append(result)

    winner = None
    for result in results:
        if not result.is_control and result.is_significant and result.relative_uplift and result.relative_uplift > 0:
            if winner is None or (result.relative_uplift > winner.relative_uplift):
                winner = Winner(
                    variant_id=result.variant_id,
                    variant_name=result.variant_name,
                    relative_uplift=result.relative_uplift
                )

    return ExperimentStatisticsResponse(
        experiment_id=experiment_id,
        experiment_name=experiment.name,
        conversion_event_type=conversion_event_type,
        confidence_level=confidence_level,
        significance_threshold=significance_threshold,
        variants=results,
        winner=winner
    )
