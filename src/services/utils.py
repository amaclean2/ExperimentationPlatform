import hashlib
from typing import List
from src.models import Variant


def assign_variant_by_hash(user_id: str, experiment_id: int, variants: List[Variant]) -> int:
    hash_input = f"{user_id}:{experiment_id}".encode('utf-8')
    hash_digest = hashlib.sha256(hash_input).hexdigest()

    hash_bucket = int(hash_digest[:8], 16) % 100

    sorted_variants = sorted(variants, key=lambda v: v.id)

    cumulative_percent = 0.0
    for variant in sorted_variants:
        cumulative_percent += variant.percent_allocated
        if hash_bucket < cumulative_percent:
            return variant.id

    return sorted_variants[-1].id if sorted_variants else None
