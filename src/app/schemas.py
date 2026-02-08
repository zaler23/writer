from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    genre: str | None = Field(default=None, max_length=100)
    premise: str | None = None


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    genre: str | None = Field(default=None, max_length=100)
    premise: str | None = None

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "ProjectUpdate":
        if self.name is None and self.genre is None and self.premise is None:
            raise ValueError("At least one field must be provided.")
        return self


class ProjectOut(BaseModel):
    id: str
    name: str
    genre: str | None = None
    premise: str | None = None
    created_at: str
    updated_at: str


class ProjectListResponse(BaseModel):
    items: list[ProjectOut]
    next_after: str | None = None


class ProjectSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    settings_json: dict[str, Any]

    @field_validator("settings_json")
    @classmethod
    def check_schema_version(cls, value: dict[str, Any]) -> dict[str, Any]:
        schema_version = value.get("schema_version")
        if schema_version is not None and schema_version != "1.2":
            raise ValueError('schema_version must be "1.2" when provided.')
        return value


class ProjectSettingsOut(BaseModel):
    id: str
    project_id: str
    settings_json: dict[str, Any]
    created_at: str
    updated_at: str


class ChapterCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    volume_no: int = Field(default=1, ge=1)
    chapter_no: int = Field(ge=1)
    title: str | None = Field(default=None, max_length=200)
    plan_json: dict[str, Any] | None = None
    traversal_profile_id: str | None = None
    style_guide_id: str | None = None

    @field_validator("plan_json")
    @classmethod
    def check_plan_schema_version(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        schema_version = value.get("schema_version")
        if schema_version is not None and schema_version != "1.2":
            raise ValueError('plan_json.schema_version must be "1.2" when provided.')
        return value


class ChapterUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=200)
    plan_json: dict[str, Any] | None = None
    traversal_profile_id: str | None = None
    style_guide_id: str | None = None

    @field_validator("plan_json")
    @classmethod
    def check_plan_schema_version(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        schema_version = value.get("schema_version")
        if schema_version is not None and schema_version != "1.2":
            raise ValueError('plan_json.schema_version must be "1.2" when provided.')
        return value

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "ChapterUpdate":
        if (
            self.title is None
            and self.plan_json is None
            and self.traversal_profile_id is None
            and self.style_guide_id is None
        ):
            raise ValueError("At least one field must be provided.")
        return self


class ChapterOut(BaseModel):
    id: str
    project_id: str
    volume_no: int
    chapter_no: int
    title: str | None = None
    status: str
    needs_review: bool
    review_reason: str | None = None
    plan_json: dict[str, Any] | None = None
    traversal_profile_id: str | None = None
    style_guide_id: str | None = None
    lock_version: int
    created_at: str
    updated_at: str


class ChapterListResponse(BaseModel):
    items: list[ChapterOut]
    next_after: str | None = None


class ChapterSegmentUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_no: int = Field(ge=1)
    title: str | None = Field(default=None, max_length=200)
    pov_node_id: str | None = None
    segment_type: str | None = Field(default=None, max_length=32)
    content_text: str | None = None
    attrs_json: dict[str, Any] | None = None


class ChapterSegmentOut(BaseModel):
    id: str
    chapter_id: str
    segment_no: int
    title: str | None = None
    pov_node_id: str | None = None
    segment_type: str | None = None
    content_text: str | None = None
    attrs_json: dict[str, Any] | None = None
    created_at: str
    updated_at: str


class ChapterSegmentListResponse(BaseModel):
    items: list[ChapterSegmentOut]


class ChapterReviewOut(BaseModel):
    id: str
    chapter_id: str
    version_id: str
    review_type: str
    report_json: dict[str, Any]
    source_run_id: str | None = None
    source_step_id: str | None = None
    created_at: str


class ChapterReviewListResponse(BaseModel):
    items: list[ChapterReviewOut]
    next_after: str | None = None


class ChapterTextVersionOut(BaseModel):
    id: str
    chapter_id: str
    version_no: int
    stage: str
    content_text: str
    source_run_id: str | None = None
    source_step_id: str | None = None
    created_at: str


class ChapterTextVersionListResponse(BaseModel):
    items: list[ChapterTextVersionOut]
    next_after: str | None = None


class SwarmRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    chapter_id: str = Field(min_length=1)
    run_type: str = Field(default="chapter_write", min_length=1, max_length=64)
    swarm_profile_id: str | None = None
    input_json: dict[str, Any] | None = None
    budget_json: dict[str, Any] | None = None
    requires_approval: bool = False
    auto_start: bool = True


class RunOut(BaseModel):
    id: str
    project_id: str
    swarm_profile_id: str | None = None
    run_type: str
    target_chapter_id: str | None = None
    status: str
    input_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    budget_json: dict[str, Any] | None = None
    started_at: str
    finished_at: str | None = None


class RunStepOut(BaseModel):
    id: str
    run_id: str
    step_no: int
    step_type: str
    role: str | None = None
    status: str
    requires_approval: bool
    approval_status: str
    override_payload_json: dict[str, Any] | None = None
    input_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None
    budget_json: dict[str, Any] | None = None
    started_at: str
    finished_at: str | None = None
    error_text: str | None = None


class RunStepListResponse(BaseModel):
    items: list[RunStepOut]


class RunStepOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_text: str = Field(min_length=1)
