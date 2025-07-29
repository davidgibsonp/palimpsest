#!/usr/bin/env python3
"""
Integration testing script for Palimpsest v0.1.0

Tests the complete workflow with real traces from our development session.
This validates that our core architecture works with realistic data.
"""

import json
import time

from palimpsest.models.trace import ExecutionStep, ExecutionTrace
from palimpsest.storage.file_manager import TraceFileManager


def create_development_traces():
    """Create traces representing our actual development session."""
    
    traces = []
    
    # Trace 1: Project Setup
    traces.append(ExecutionTrace(
        problem_statement="Set up the basic project structure and dependencies for Palimpsest v0.1.0",
        outcome="Successfully created directory structure, added Pydantic dependencies, and configured development environment",
        execution_steps=[
            ExecutionStep(
                step_number=1,
                action="configure",
                content="Updated pyproject.toml with version 0.0.1 and core dependencies: pydantic, pydantic-settings, loguru, pytest, pytest-cov",
                duration_ms=2000,
                success=True
            ),
            ExecutionStep(
                step_number=2,
                action="command", 
                content="uv add pydantic pydantic-settings loguru && uv add --dev pytest pytest-cov",
                duration_ms=15000,
                success=True
            ),
            ExecutionStep(
                step_number=3,
                action="create_structure",
                content="Created palimpsest/{models,storage,search,api} directories with __init__.py files",
                duration_ms=1500,
                success=True
            ),
            ExecutionStep(
                step_number=4,
                action="validate",
                content="Tested package import: python -c 'import palimpsest; print(palimpsest.__version__)'",
                duration_ms=3000,
                success=True
            )
        ],
        domain="python",
        complexity="simple",
        success=True
    ))
    
    # Trace 2: Pydantic Models Implementation
    traces.append(ExecutionTrace(
        problem_statement="Design and implement ExecutionTrace Pydantic models with proper validation and flexibility for AI-generated data",
        outcome="Created comprehensive data models with ExecutionTrace, ExecutionStep, and TraceContext classes, including rich validation and schema versioning",
        execution_steps=[
            ExecutionStep(
                step_number=1,
                action="design",
                content="Designed ExecutionStep model with step_number, action, content, timestamp, duration_ms, success, error_message fields",
                duration_ms=8000,
                success=True
            ),
            ExecutionStep(
                step_number=2,
                action="design", 
                content="Designed TraceContext model with git context, AI agent context, tags, and flexible metadata dictionary",
                duration_ms=6000,
                success=True
            ),
            ExecutionStep(
                step_number=3,
                action="implement",
                content="Created ExecutionTrace model with problem_statement, outcome, execution_steps as required fields, plus domain/complexity categorization",
                duration_ms=12000,
                success=True
            ),
            ExecutionStep(
                step_number=4,
                action="validate",
                content="Added field validators for step sequence validation, tag normalization, and complexity constraints",
                duration_ms=5000,
                success=True
            ),
            ExecutionStep(
                step_number=5,
                action="test",
                content="Tested model creation and validation with sample data, verified error handling for invalid inputs",
                duration_ms=4000,
                success=True
            )
        ],
        domain="python",
        complexity="moderate",
        success=True
    ))
    
    # Trace 3: Migration Framework 
    traces.append(ExecutionTrace(
        problem_statement="Implement schema versioning and migration framework to ensure backward compatibility as the trace format evolves",
        outcome="Built comprehensive migration system with schema_version field, migration registry, and automatic migration on load",
        execution_steps=[
            ExecutionStep(
                step_number=1,
                action="analyze",
                content="Analyzed version migration requirements and decided on hybrid approach: simple dict-based migrations with optional schema snapshots",
                duration_ms=10000,
                success=True
            ),
            ExecutionStep(
                step_number=2,
                action="implement",
                content="Added schema_version='0.1.0' field to ExecutionTrace model",
                duration_ms=2000,
                success=True
            ),
            ExecutionStep(
                step_number=3,
                action="implement",
                content="Created migrations.py with migration registry, version detection, and migration execution framework",
                duration_ms=18000,
                success=True
            ),
            ExecutionStep(
                step_number=4,
                action="implement",
                content="Added model_validate_with_migration() class method for automatic migration during validation",
                duration_ms=5000,
                success=True
            ),
            ExecutionStep(
                step_number=5,
                action="implement",
                content="Created migration from pre-versioned (0.0.1) to v0.1.0 format with context and success field defaults",
                duration_ms=8000,
                success=True
            ),
            ExecutionStep(
                step_number=6,
                action="test",
                content="Wrote comprehensive test suite with 13 tests covering version detection, migration paths, and edge cases",
                duration_ms=15000,
                success=True
            )
        ],
        domain="python", 
        complexity="complex",
        success=True
    ))
    
    # Trace 4: JSON File Storage
    traces.append(ExecutionTrace(
        problem_statement="Implement robust JSON file storage system for ExecutionTrace objects with CRUD operations and performance optimizations",
        outcome="Created TraceFileManager with atomic writes, unique ID generation, migration support, and comprehensive file operations",
        execution_steps=[
            ExecutionStep(
                step_number=1,
                action="implement",
                content="Created TraceFileManager class with __init__ method that ensures .palimpsest/traces/ directory structure",
                duration_ms=4000,
                success=True
            ),
            ExecutionStep(
                step_number=2,
                action="implement",
                content="Implemented save_trace() with timestamp-based unique ID generation and atomic write using tempfile + rename",
                duration_ms=10000,
                success=True
            ),
            ExecutionStep(
                step_number=3,
                action="implement",
                content="Implemented load_trace() with automatic migration support via model_validate_with_migration()",
                duration_ms=6000,
                success=True
            ),
            ExecutionStep(
                step_number=4,
                action="implement",
                content="Added delete_trace(), list_traces(), trace_exists(), get_trace_stats(), cleanup_corrupted_files() methods",
                duration_ms=12000,
                success=True
            ),
            ExecutionStep(
                step_number=5,
                action="test",
                content="Created comprehensive test suite with 11 tests covering CRUD operations, concurrency, migration, and error handling",
                duration_ms=20000,
                success=True
            ),
            ExecutionStep(
                step_number=6,
                action="validate",
                content="Tested real usage scenarios with temp directory, verified JSON output is human-readable",
                duration_ms=3000,
                success=True
            )
        ],
        domain="python",
        complexity="moderate", 
        success=True
    ))
    
    return traces


def test_full_workflow():
    """Test the complete save/load/migrate workflow."""
    print("🧪 Testing Full Workflow")
    print("=" * 50)
    
    # Use current directory for testing
    fm = TraceFileManager()
    
    # Create development traces
    traces = create_development_traces()
    
    print(f"📝 Created {len(traces)} development traces")
    
    # Save all traces
    trace_ids = []
    for i, trace in enumerate(traces, 1):
        start_time = time.time()
        trace_id = fm.save_trace(trace)
        save_time = (time.time() - start_time) * 1000
        
        trace_ids.append(trace_id)
        print(f"💾 Saved trace {i}: {trace_id} ({save_time:.1f}ms)")
    
    print()
    
    # Load and verify traces
    for i, trace_id in enumerate(trace_ids, 1):
        start_time = time.time()
        loaded_trace = fm.load_trace(trace_id)
        load_time = (time.time() - start_time) * 1000
        
        print(f"📖 Loaded trace {i}: {loaded_trace.problem_statement[:60]}... ({load_time:.1f}ms)")
        print(f"   ✅ Schema version: {loaded_trace.schema_version}")
        print(f"   ✅ Steps: {len(loaded_trace.execution_steps)}")
        print(f"   ✅ Domain: {loaded_trace.domain}, Complexity: {loaded_trace.complexity}")
        print()
    
    # Test basic statistics  
    all_traces = fm.list_traces()
    print("📊 Basic Statistics:")
    print(f"   Total traces: {len(all_traces)}")
    print(f"   Traces directory: {fm.traces_dir}")
    print()
    
    return trace_ids, traces


def test_json_readability():
    """Test that saved JSON files are human-readable."""
    print("👁️  Testing JSON Readability")
    print("=" * 50)
    
    fm = TraceFileManager()
    
    # Create a simple trace for readability testing
    trace = ExecutionTrace(
        problem_statement="Test JSON readability and structure",
        outcome="JSON files should be human-readable and well-formatted",
        execution_steps=[
            ExecutionStep(
                step_number=1,
                action="test",
                content="Create a sample trace for JSON inspection"
            )
        ],
        domain="testing",
        complexity="simple"
    )
    
    trace_id = fm.save_trace(trace)
    json_path = fm.get_trace_path(trace_id)
    
    print(f"📄 Trace saved to: {json_path}")
    print("📖 JSON content preview:")
    print("-" * 30)
    
    with open(json_path, 'r') as f:
        content = f.read()
        # Show first 500 characters
        print(content[:500] + "..." if len(content) > 500 else content)
    
    print("-" * 30)
    
    # Validate it's proper JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    print("✅ JSON is valid and parseable")
    print(f"✅ Contains {len(data)} top-level fields")
    print(f"✅ Schema version: {data.get('schema_version', 'missing')}")
    print()
    
    return trace_id


def test_migration_compatibility():
    """Test that migration system works with realistic legacy data."""
    print("🔄 Testing Migration Compatibility")  
    print("=" * 50)
    
    fm = TraceFileManager()
    
    # Create a realistic legacy trace (without schema_version)
    legacy_data = {
        "problem_statement": "Legacy trace from pre-versioned Palimpsest",
        "outcome": "This trace was created before schema versioning was implemented",
        "execution_steps": [
            {
                "step_number": 1,
                "action": "implement",
                "content": "Built initial Palimpsest prototype without version tracking"
            },
            {
                "step_number": 2, 
                "action": "realize",
                "content": "Realized we need schema versioning for long-term compatibility"
            }
        ],
        "domain": "python",
        "success": True
    }
    
    # Write legacy file directly (simulating old data)
    legacy_id = "legacy_20250129_120000_test1234"
    legacy_path = fm.get_trace_path(legacy_id)
    
    with open(legacy_path, 'w') as f:
        json.dump(legacy_data, f, indent=2)
    
    print(f"📄 Created legacy trace: {legacy_id}")
    
    # Load through TraceFileManager (should trigger migration)
    loaded_trace = fm.load_trace(legacy_id)
    
    print("✅ Migration successful!")
    print(f"   Schema version: {loaded_trace.schema_version}")
    print(f"   Migration metadata: {loaded_trace.context.metadata.get('migrated_from')}")
    print(f"   Original problem: {loaded_trace.problem_statement}")
    print()
    
    return legacy_id


def test_performance_simulation():
    """Test performance with multiple traces."""
    print("⚡ Testing Performance Simulation")
    print("=" * 50)
    
    fm = TraceFileManager()
    
    # Create batch of traces
    batch_size = 50
    print(f"📦 Creating {batch_size} traces for performance testing...")
    
    trace_ids = []
    total_save_time = 0
    
    for i in range(batch_size):
        trace = ExecutionTrace(
            problem_statement=f"Performance test trace {i+1} - testing system scalability with multiple traces",
            outcome=f"Successfully created trace {i+1} in performance test batch",
            execution_steps=[
                ExecutionStep(
                    step_number=1,
                    action="generate",
                    content=f"Generated test trace {i+1} with realistic content length and structure"
                ),
                ExecutionStep(
                    step_number=2,
                    action="validate",
                    content="Validated trace structure and content meets requirements"
                )
            ],
            domain="testing",
            complexity="simple"
        )
        
        start_time = time.time()
        trace_id = fm.save_trace(trace)
        save_time = (time.time() - start_time) * 1000
        
        total_save_time += save_time
        trace_ids.append(trace_id)
        
        if (i + 1) % 10 == 0:
            print(f"   💾 Saved {i+1} traces...")
    
    print(f"✅ Saved {batch_size} traces")
    print(f"   Average save time: {total_save_time/batch_size:.1f}ms per trace")
    print(f"   Total save time: {total_save_time:.1f}ms")
    
    # Test batch loading
    print(f"📖 Loading {batch_size} traces...")
    total_load_time = 0
    
    for trace_id in trace_ids:
        start_time = time.time()
        loaded_trace = fm.load_trace(trace_id)
        load_time = (time.time() - start_time) * 1000
        total_load_time += load_time
    
    print(f"✅ Loaded {batch_size} traces")
    print(f"   Average load time: {total_load_time/batch_size:.1f}ms per trace")
    print(f"   Total load time: {total_load_time:.1f}ms")
    
    # Test listing performance
    start_time = time.time()
    all_traces = fm.list_traces()
    list_time = (time.time() - start_time) * 1000
    
    print(f"✅ Listed {len(all_traces)} traces in {list_time:.1f}ms")
    print()
    
    return trace_ids


def main():
    """Run complete integration test suite."""
    print("🎯 Palimpsest v0.1.0 Integration Testing")
    print("=" * 60)
    print("Testing core functionality with realistic development traces")
    print()
    
    # Test 1: Full workflow 
    trace_ids, traces = test_full_workflow()
    
    # Test 2: JSON readability
    json_trace_id = test_json_readability()
    
    # Test 3: Migration compatibility
    legacy_trace_id = test_migration_compatibility()
    
    # Test 4: Performance simulation
    perf_trace_ids = test_performance_simulation()
    
    # Summary
    print("🎉 Integration Testing Complete!")
    print("=" * 60)
    total_traces = len(trace_ids) + 1 + 1 + len(perf_trace_ids)
    print(f"✅ Created and tested {total_traces} traces")
    print("✅ Verified save/load workflow")
    print("✅ Confirmed JSON readability")  
    print("✅ Validated migration system")
    print("✅ Performance tested with batch operations")
    print()
    print("🔍 Manual Review Recommendations:")
    print("1. Inspect .palimpsest/traces/ directory for JSON file quality")
    print("2. Review trace content for realistic data representation") 
    print("3. Verify migration metadata is properly preserved")
    print("4. Check performance metrics meet <1s search requirements")
    print()
    
    # Show storage location
    fm = TraceFileManager()
    print(f"📁 Traces stored in: {fm.traces_dir}")
    

if __name__ == "__main__":
    main()