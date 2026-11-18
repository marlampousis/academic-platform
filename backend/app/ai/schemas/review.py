
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class ReviewDecision(str, Enum):
    ACCEPT = "ACCEPT"
    EDIT = "EDIT"
    REJECT = "REJECT"


class ReviewCollection(str, Enum):
    DEGREES = "degrees"
    PUBLICATIONS = "publications"
    RESEARCH_PROJECTS = "research_projects"
    TEACHING_EXPERIENCE = "teaching_experience"


class RecordReview(BaseModel):
    collection: ReviewCollection
    record_index: int = Field(ge=0)
    decision: ReviewDecision
    corrected_data: dict | None = None
    comment: str | None = Field(
        default=None,
        max_length=2000,
    )

    @model_validator(mode="after")
    def validate_decision(self):
        if self.decision == ReviewDecision.EDIT:
            if not self.corrected_data:
                raise ValueError(
                    "EDIT requires corrected_data"
                )
        elif self.corrected_data is not None:
            raise ValueError(
                "corrected_data is allowed only for EDIT"
            )

        return self


class ExtractionReviewRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reviews: list[RecordReview] = Field(
        min_length=1,
        max_length=100,
    )

    @model_validator(mode="after")
    def validate_unique_records(self):
        keys = [
            (review.collection, review.record_index)
            for review in self.reviews
        ]

        if len(keys) != len(set(keys)):
            raise ValueError(
                "Duplicate review decisions for one record"
            )

        return self
