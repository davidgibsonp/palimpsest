"""
Pydantic models for execution traces.

Defines the core data structures for capturing AI agent execution workflows.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ExecutionStep(BaseModel):
    """A single step in an execution trace."""

    step_number: int = Field(
        ..., ge=1, description="Sequential step number starting from 1"
    )
    action: str = Field(
        ..., min_length=1, description="Type of action: command, code, analysis, etc."
    )
    content: str = Field(
        ..., min_length=1, description="The actual content of the step"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When this step was executed"
    )
    duration_ms: Optional[int] = Field(
        None, ge=0, description="Duration in milliseconds"
    )
    success: bool = Field(True, description="Whether this step completed successfully")
    error_message: Optional[str] = Field(
        None, description="Error message if step failed"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "step_number": 1,
                "action": "command",
                "content": "uv add pydantic",
                "timestamp": "2025-01-29T10:30:00Z",
                "duration_ms": 1250,
                "success": True,
                "error_message": None,
            }
        }
    }


class TraceContext(BaseModel):
    """Context information for an execution trace."""

    # Core context (always present)
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When trace was created"
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique trace identifier"
    )

    # Development context (when available)
    git_branch: Optional[str] = Field(None, description="Git branch name")
    git_commit: Optional[str] = Field(None, description="Git commit hash")
    working_directory: Optional[str] = Field(None, description="Working directory path")
    environment: Optional[Dict[str, Any]] = Field(
        None, description="Environment variables and settings"
    )

    # AI agent context
    model_name: Optional[str] = Field(
        None, description="AI model used (e.g., claude-3-sonnet)"
    )
    agent_version: Optional[str] = Field(None, description="Agent/tool version")

    # Flexible additional context
    tags: List[str] = Field(
        default_factory=list, description="Categorical tags for organization"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional flexible metadata"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Ensure tags are non-empty strings and lowercase."""
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                cleaned_tags.append(tag.strip().lower())
        return list(set(cleaned_tags))  # Remove duplicates

    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2025-01-29T10:30:00Z",
                "trace_id": "123e4567-e89b-12d3-a456-426614174000",
                "git_branch": "feature/pydantic-models",
                "git_commit": "abc123def456",
                "working_directory": "/home/user/project",
                "model_name": "claude-3-sonnet",
                "tags": ["python", "setup", "dependencies"],
                "metadata": {
                    "session_id": "sess_123",
                    "user_intent": "add_dependencies",
                },
            }
        }
    }


class ExecutionTrace(BaseModel):
    """Complete execution trace capturing an AI-assisted workflow."""

    # Schema version for migration support
    schema_version: str = Field(
        "0.1.0", description="Schema version used to create this trace"
    )

    # Required core fields
    problem_statement: str = Field(
        ..., min_length=10, description="Clear description of the problem being solved"
    )
    outcome: str = Field(
        ..., min_length=5, description="Description of the final outcome or result"
    )
    execution_steps: List[ExecutionStep] = Field(
        ..., min_length=1, description="Sequential steps taken to solve the problem"
    )

    # Context and metadata
    context: TraceContext = Field(
        default_factory=TraceContext, description="Contextual information"
    )
    success: bool = Field(
        True, description="Whether the overall execution was successful"
    )

    # Search and categorization
    domain: Optional[str] = Field(
        None, description="Problem domain: python, web-dev, debugging, etc."
    )
    complexity: Optional[str] = Field(
        None, description="Complexity level: simple, moderate, complex"
    )

    @field_validator("execution_steps")
    @classmethod
    def validate_execution_steps(cls, v: List[ExecutionStep]) -> List[ExecutionStep]:
        """Ensure step numbers are sequential starting from 1."""
        if not v:
            raise ValueError("At least one execution step is required")

        for i, step in enumerate(v):
            expected_step_number = i + 1
            if step.step_number != expected_step_number:
                raise ValueError(
                    f"Step numbers must be sequential starting from 1. "
                    f"Expected step {expected_step_number}, got {step.step_number} at position {i}"
                )
        return v

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: Optional[str]) -> Optional[str]:
        """Ensure domain is lowercase if provided."""
        if v is not None:
            return v.strip().lower() if v.strip() else None
        return v

    @field_validator("complexity")
    @classmethod
    def validate_complexity(cls, v: Optional[str]) -> Optional[str]:
        """Ensure complexity is one of allowed values."""
        if v is not None:
            allowed_values = {"simple", "moderate", "complex"}
            normalized = v.strip().lower()
            if normalized not in allowed_values:
                raise ValueError(
                    f"Complexity must be one of {allowed_values}, got '{v}'"
                )
            return normalized
        return v

    @classmethod
    def model_validate_with_migration(cls, data: Dict[str, Any]) -> "ExecutionTrace":
        """
        Validate model data with automatic migration from older schema versions.

        Args:
            data: Raw trace data dictionary

        Returns:
            ExecutionTrace instance with migrated data
        """
        from .migrations import is_migration_needed, migrate_trace

        # Migrate if needed
        if is_migration_needed(data):
            data = migrate_trace(data)

        return cls.model_validate(data)

    def to_searchable_text(self) -> str:
        """Extract all searchable text content for indexing."""
        text_parts = [
            self.problem_statement,
            self.outcome,
            self.domain or "",
            " ".join(self.context.tags),
        ]

        # Add execution step content
        for step in self.execution_steps:
            text_parts.extend([step.action, step.content])
            if step.error_message:
                text_parts.append(step.error_message)

        return " ".join(filter(None, text_parts))

    def get_version(self) -> str:
        """Get the schema version of this trace."""
        return self.schema_version

    model_config = {
        "json_schema_extra": {
            "example": {
                "schema_version": "0.1.0",
                "problem_statement": "Add Pydantic dependencies to the palimpsest project for data validation",
                "outcome": "Successfully added pydantic, pydantic-settings, and loguru dependencies via uv",
                "execution_steps": [
                    {
                        "step_number": 1,
                        "action": "command",
                        "content": "cd /path/to/project && uv add pydantic pydantic-settings loguru",
                        "timestamp": "2025-01-29T10:30:00Z",
                        "duration_ms": 1250,
                        "success": True,
                    }
                ],
                "success": True,
                "domain": "python",
                "complexity": "simple",
                "context": {
                    "git_branch": "feature/dependencies",
                    "tags": ["setup", "dependencies", "python"],
                },
            }
        }
    }
