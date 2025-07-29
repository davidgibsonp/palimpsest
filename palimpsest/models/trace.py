"""
Pydantic models for execution traces.

Defines the core data structures for capturing AI agent execution workflows.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ExecutionStep(BaseModel):
    """A single step in an execution trace - LLM-capturable content only."""

    step_number: int = Field(
        ..., ge=1, description="Sequential step number starting from 1"
    )
    action: Literal["analyze", "implement", "test", "debug"] = Field(
        ...,
        description="Type of action. Allowed: analyze, implement, test, debug.",
    )
    content: str = Field(..., min_length=1, description="What was done in this step")

    # Optional fields that LLM can sometimes provide
    success: bool = Field(True, description="Whether this step was successful")
    error_message: Optional[str] = Field(
        default=None, description="Error encountered if step failed"
    )

    # model_config: used by Pydantic for schema examples and docs (e.g., FastAPI)
    model_config = {
        "json_schema_extra": {
            "example": {
                "step_number": 1,
                "action": "analyze",
                "content": "Identified timeout issue in database connection pool",
                "success": True,
                "error_message": None,
            }
        }
    }


class TraceContext(BaseModel):
    """Context information for an execution trace."""

    # Always present - system generated
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When trace was created"
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique trace identifier"
    )

    # LLM-provided tags for organization
    tags: List[str] = Field(
        default_factory=list,
        description="Categorical tags (e.g., ['bug-fix', 'python', 'async'])",
    )

    # Rich context - populated by MCP/environment when available
    environment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Environment context (git, dependencies, etc.) - populated by tooling",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Ensure tags are non-empty strings and lowercase."""
        cleaned_tags = []
        for tag in v:
            if isinstance(tag, str) and tag.strip():
                cleaned_tags.append(tag.strip().lower())
        return sorted(list(set(cleaned_tags)))  # Remove duplicates

    # model_config: used by Pydantic for schema examples and docs (e.g., FastAPI)
    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2025-01-29T10:30:00Z",
                "trace_id": "123e4567-e89b-12d3-a456-426614174000",
                "tags": ["bug-fix", "python", "async"],
                "environment": {
                    "python_version": "3.11.2",
                    "git_branch": "feature/async-fix",
                    "git_commit": "abc123",
                    "dependencies": ["fastapi==0.104.1"],
                    "modified_files": ["app/main.py"],
                },
            }
        }
    }


class ExecutionTrace(BaseModel):
    """Complete execution trace capturing an AI-assisted workflow."""

    # Schema version for migration support
    schema_version: str = Field(
        default="0.1.0", description="Schema version used to create this trace"
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
        default_factory=lambda: TraceContext(), description="Contextual information"
    )
    success: bool = Field(
        True, description="Whether the overall execution was successful"
    )

    # Search and categorization
    domain: Optional[str] = Field(
        None, description="Problem domain: python, web-dev, debugging, etc."
    )
    complexity: Optional[Literal["simple", "moderate", "complex"]] = Field(
        None, description="Complexity level: simple, moderate, complex"
    )

    @classmethod
    def from_user_input(cls, data: dict) -> "ExecutionTrace":
        """
        Create an ExecutionTrace from user input, stripping system fields from context.
        """
        data = dict(data)
        if "context" in data and isinstance(data["context"], dict):
            data["context"] = dict(data["context"])
            data["context"].pop("timestamp", None)
            data["context"].pop("trace_id", None)
        return cls.model_validate(data)

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

        # Set a flag so the validator knows this is a load, not a user creation
        data = dict(data)
        # If context is a dict, propagate the flag for TraceContext
        if "context" in data and isinstance(data["context"], dict):
            data["context"] = dict(data["context"])
            data["context"]["_from_storage"] = True
        data["_from_storage"] = True
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

    # model_config: used by Pydantic for schema examples and docs (e.g., FastAPI)
    model_config = {
        "json_schema_extra": {
            "example": {
                "schema_version": "0.1.0",
                "problem_statement": "Fix async timeout in API endpoint causing 504 errors",
                "outcome": "Increased connection timeout and added retry logic, reducing 504 errors by 95%",
                "execution_steps": [
                    {
                        "step_number": 1,
                        "action": "analyze",
                        "content": "Found database queries timing out after 30 seconds under load",
                        "success": True,
                    },
                    {
                        "step_number": 2,
                        "action": "implement",
                        "content": "Increased connection timeout to 60s and added connection pooling",
                        "success": True,
                    },
                ],
                "success": True,
                "domain": "backend",
                "complexity": "moderate",
                "context": {
                    "tags": ["bug-fix", "performance", "async"],
                    "environment": {
                        "python_version": "3.11.2",
                        "git_branch": "fix/async-timeout",
                    },
                },
            }
        }
    }
