# Palimpsest Schema Migration Guide

This document explains how Palimpsest handles schema evolution and backward compatibility for ExecutionTrace data.

## Overview

Palimpsest uses a versioned schema system to ensure that traces created with older versions of the software remain readable and usable as the schema evolves. This is critical for preserving your historical traces as dogfooding material.

## Schema Versioning

### Current Version: 0.1.0

Every `ExecutionTrace` includes a `schema_version` field that identifies which version of the schema was used to create it:

```python
from palimpsest.models.trace import ExecutionTrace

trace = ExecutionTrace(
    problem_statement="Example trace",
    outcome="Schema version automatically set",
    execution_steps=[...],
)

print(trace.schema_version)  # "0.1.0"
print(trace.get_version())   # "0.1.0"
```

### Legacy Support

Traces created before schema versioning (pre-0.1.0) are automatically detected and can be migrated:

```python
# Legacy trace data (no schema_version field)
legacy_data = {
    "problem_statement": "Old trace format",
    "outcome": "Will be migrated",
    "execution_steps": [...]
}

# Automatic migration during validation
trace = ExecutionTrace.model_validate_with_migration(legacy_data)
print(trace.schema_version)  # "0.1.0"
print(trace.context.metadata["migrated_from"])  # "0.0.1"
```

## Migration Framework

### Automatic Migration

The migration system automatically detects the schema version of trace data and migrates it to the current version when needed:

```python
from palimpsest.models.migrations import migrate_trace, is_migration_needed

# Check if migration is needed
if is_migration_needed(trace_data):
    migrated_data = migrate_trace(trace_data)
```

### Migration Process

1. **Version Detection**: Determines the schema version of the input data
2. **Path Finding**: Identifies the migration path from source to target version
3. **Sequential Migration**: Applies migration functions in order
4. **Validation**: Ensures the result conforms to the target schema

### Migration Functions

Palimpsest supports two types of migrations:

#### 1. Simple Dict-Based Migrations (Recommended for minor changes)

```python
from palimpsest.models.migrations import register_migration

@register_migration("0.1.0", "0.1.1")  
def migrate_0_1_0_to_0_1_1(trace_data: dict) -> dict:
    """Simple migration for minor changes."""
    migrated = trace_data.copy()
    
    # Simple transformations: rename fields, add defaults, etc.
    if "old_field" in migrated:
        migrated["new_field"] = migrated.pop("old_field")
    
    return migrated
```

#### 2. Schema-Aware Migrations (For major breaking changes)

When migrations become complex, you can register schema snapshots:

```python
# In palimpsest/models/versions/v0_1_0.py (created when needed)
class ExecutionTraceV010(BaseModel):
    # Full v0.1.0 schema definition
    pass

# Register the snapshot
from palimpsest.models.migrations import register_schema_snapshot
register_schema_snapshot("0.1.0", ExecutionTraceV010)

# Use in complex migrations
@register_migration("0.1.0", "0.2.0")
def migrate_complex_0_1_0_to_0_2_0(trace_data: dict) -> dict:
    from palimpsest.models.migrations import get_schema_snapshot
    
    # Validate with old schema first
    OldSchema = get_schema_snapshot("0.1.0")
    old_trace = OldSchema.model_validate(trace_data)
    
    # Complex transformation logic using both schemas
    # ...
    
    return migrated_data
```

## Backward Compatibility Guarantees

### What We Guarantee

- **Data Preservation**: All existing trace data will remain accessible
- **Automatic Migration**: Old traces are automatically migrated when accessed
- **Metadata Tracking**: Migration history is preserved in `context.metadata`

### What May Change

- **Schema Structure**: Field names, types, and organization may evolve
- **Validation Rules**: Stricter or different validation may be applied
- **Default Values**: New fields may have different defaults

## Schema Versioning Strategy

### When to Use Simple Dict-Based Migrations

✅ **Use for:**
- Adding optional fields with defaults
- Renaming fields
- Simple data transformations
- Minor validation changes

### When to Create Schema Snapshots

⚠️ **Use for:**
- Major structural changes
- Complex data transformations requiring validation
- Breaking changes that affect many fields
- When migration logic becomes hard to understand

### Decision Matrix

| Change Type | Approach | Example |
|-------------|----------|---------|
| Add optional field | Dict-based | `migrated["new_field"] = None` |
| Rename field | Dict-based | `migrated["new"] = migrated.pop("old")` |
| Restructure nested data | Schema-aware | Complex object transformations |
| Change required fields | Schema-aware | Type changes, validation changes |

## Best Practices for Schema Evolution

### Adding New Fields

✅ **Safe**: Add optional fields with sensible defaults

```python
class ExecutionTrace(BaseModel):
    # Existing fields...
    new_optional_field: Optional[str] = None  # Safe to add
```

### Renaming Fields

⚠️ **Requires Migration**: Use field aliases and migration functions

```python
class ExecutionTrace(BaseModel):
    new_field_name: str = Field(..., alias="old_field_name")
    
# Plus migration function to handle the rename
```

### Removing Fields

⚠️ **Requires Migration**: Preserve data in metadata or alternative fields

```python
@register_migration("0.1.0", "0.2.0")
def migrate_removed_field(trace_data: dict) -> dict:
    migrated = trace_data.copy()
    
    # Preserve removed field in metadata
    if "removed_field" in migrated:
        migrated.setdefault("context", {}).setdefault("metadata", {})
        migrated["context"]["metadata"]["legacy_removed_field"] = migrated.pop("removed_field")
    
    return migrated
```

### Changing Validation Rules

⚠️ **Use Caution**: Ensure old data can still be validated or migrated appropriately

## Migration Testing

Always test migrations with real data:

```python
def test_migration_preserves_data():
    old_data = {...}  # Real trace from previous version
    
    migrated = migrate_trace(old_data, "0.2.0")
    trace = ExecutionTrace.model_validate(migrated)
    
    # Verify critical data is preserved
    assert trace.problem_statement == old_data["problem_statement"]
    # ... other assertions
```

## Version History

### v0.1.0 (Current)

- Added `schema_version` field
- Implemented migration framework
- Added backward compatibility for pre-versioned traces

### v0.0.1 (Legacy)

- Initial schema without versioning
- Basic ExecutionTrace, ExecutionStep, TraceContext models
- No migration support

## Future Considerations

- **Multi-step Migrations**: Complex migration paths across multiple versions
- **Data Validation**: Pre-migration data integrity checks  
- **Performance**: Lazy migration for large datasets
- **User Control**: Options to disable automatic migration
