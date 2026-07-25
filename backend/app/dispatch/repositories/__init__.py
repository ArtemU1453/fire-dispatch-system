"""Dispatch repositories."""

from app.dispatch.repositories.candidate_repository import CandidateRepository
from app.dispatch.repositories.recommendation_repository import (
    RecommendationRepository,
)

__all__ = ["CandidateRepository", "RecommendationRepository"]
