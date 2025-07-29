"""
Versioned schema snapshots for complex migrations.

This directory contains full schema definitions for major versions when 
dict-based migrations become too complex. Schemas are added selectively
only when breaking changes require them.

Usage:
    # Only created when needed for complex migrations
    from palimpsest.models.versions.v0_1_0 import ExecutionTrace as ExecutionTraceV010
    
Current approach: Simple dict-based migrations in migrations.py
Future approach: Add versioned schemas here for major breaking changes
"""