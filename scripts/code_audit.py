#!/usr/bin/env python3
"""
Code quality audit for Palimpsest v0.1.0

Analyzes the codebase for complexity, potential simplifications, and code quality issues.
"""

import ast
from pathlib import Path
from typing import Dict, List, Tuple


def count_lines_of_code(file_path: Path) -> Tuple[int, int, int]:
    """Count total lines, code lines, and comment lines."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total_lines = len(lines)
    code_lines = 0
    comment_lines = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        elif stripped.startswith("#"):
            comment_lines += 1
        elif '"""' in stripped or "'''" in stripped:
            comment_lines += 1
        else:
            code_lines += 1

    return total_lines, code_lines, comment_lines


def analyze_complexity(file_path: Path) -> Dict:
    """Analyze cyclomatic complexity and other metrics."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"error": "Syntax error in file"}

    metrics = {
        "classes": 0,
        "functions": 0,
        "max_function_length": 0,
        "long_functions": [],
        "complex_functions": [],
        "imports": 0,
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            metrics["classes"] += 1
        elif isinstance(node, ast.FunctionDef):
            metrics["functions"] += 1

            # Count lines in function
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                func_length = node.end_lineno - node.lineno
                if func_length > metrics["max_function_length"]:
                    metrics["max_function_length"] = func_length

                if func_length > 30:  # Flag long functions
                    metrics["long_functions"].append((node.name, func_length))

            # Count complexity indicators
            complexity = 0
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                    complexity += 1

            if complexity > 5:  # Flag complex functions
                metrics["complex_functions"].append((node.name, complexity))

        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            metrics["imports"] += 1

    return metrics


def audit_file(file_path: Path) -> Dict:
    """Perform complete audit of a Python file."""
    if not file_path.suffix == ".py":
        return {"skip": "Not a Python file"}

    total_lines, code_lines, comment_lines = count_lines_of_code(file_path)
    complexity_metrics = analyze_complexity(file_path)

    return {
        "path": str(file_path),
        "total_lines": total_lines,
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "comment_ratio": comment_lines / total_lines if total_lines > 0 else 0,
        **complexity_metrics,
    }


def find_python_files(base_path: Path) -> List[Path]:
    """Find all Python files in the project."""
    python_files = []

    # Core package files
    palimpsest_dir = base_path / "palimpsest"
    if palimpsest_dir.exists():
        python_files.extend(palimpsest_dir.rglob("*.py"))

    # Test files
    tests_dir = base_path / "tests"
    if tests_dir.exists():
        python_files.extend(tests_dir.glob("*.py"))

    # Script files
    scripts_dir = base_path / "scripts"
    if scripts_dir.exists():
        python_files.extend(scripts_dir.glob("*.py"))

    return sorted(python_files)


def main():
    """Run code quality audit."""
    print("🔍 Palimpsest v0.1.0 Code Quality Audit")
    print("=" * 60)

    base_path = Path.cwd()
    python_files = find_python_files(base_path)

    print(f"📁 Found {len(python_files)} Python files")
    print()

    # Audit each file
    audits = []
    total_lines = 0
    total_code_lines = 0
    total_comment_lines = 0

    print("📊 File Analysis:")
    print("-" * 60)

    for file_path in python_files:
        audit = audit_file(file_path)
        if "skip" in audit:
            continue

        audits.append(audit)
        total_lines += audit["total_lines"]
        total_code_lines += audit["code_lines"]
        total_comment_lines += audit["comment_lines"]

        # Show file summary
        rel_path = file_path.relative_to(base_path)
        print(
            f"{str(rel_path):45} {audit['total_lines']:4d} lines  {audit['classes']:2d} classes  {audit['functions']:2d} funcs"
        )

    print("-" * 60)
    print(
        f"{'TOTAL':45} {total_lines:4d} lines  ({total_code_lines} code, {total_comment_lines} comments)"
    )
    print()

    # Complexity Analysis
    print("🧠 Complexity Analysis:")
    print("-" * 60)

    long_functions = []
    complex_functions = []

    for audit in audits:
        if audit.get("long_functions"):
            for func_name, length in audit["long_functions"]:
                file_name = Path(audit["path"]).name
                long_functions.append((file_name, func_name, length))

        if audit.get("complex_functions"):
            for func_name, complexity in audit["complex_functions"]:
                file_name = Path(audit["path"]).name
                complex_functions.append((file_name, func_name, complexity))

    if long_functions:
        print("⚠️  Long Functions (>30 lines):")
        for file_name, func_name, length in long_functions:
            print(f"   {file_name}::{func_name} - {length} lines")
    else:
        print("✅ No excessively long functions found")

    print()

    if complex_functions:
        print("⚠️  Complex Functions (>5 complexity points):")
        for file_name, func_name, complexity in complex_functions:
            print(f"   {file_name}::{func_name} - {complexity} complexity points")
    else:
        print("✅ No overly complex functions found")

    print()

    # Documentation Analysis
    print("📚 Documentation Analysis:")
    print("-" * 60)

    avg_comment_ratio = total_comment_lines / total_lines if total_lines > 0 else 0
    print(f"Overall comment ratio: {avg_comment_ratio:.1%}")

    poorly_documented = [
        audit
        for audit in audits
        if audit["comment_ratio"] < 0.15 and audit["total_lines"] > 20
    ]

    if poorly_documented:
        print("⚠️  Files with low documentation:")
        for audit in poorly_documented:
            file_name = Path(audit["path"]).name
            print(f"   {file_name} - {audit['comment_ratio']:.1%} comments")
    else:
        print("✅ All files have reasonable documentation")

    print()

    # Architecture Assessment
    print("🏗️  Architecture Assessment:")
    print("-" * 60)

    # Count classes and functions by module
    module_stats = {}
    for audit in audits:
        path = Path(audit["path"])
        if "palimpsest" in str(path) and "__init__" not in path.name:
            module_name = path.stem
            module_stats[module_name] = {
                "classes": audit["classes"],
                "functions": audit["functions"],
                "lines": audit["total_lines"],
            }

    print("Module breakdown:")
    for module, stats in sorted(module_stats.items()):
        print(
            f"   {module:15} - {stats['classes']} classes, {stats['functions']} functions, {stats['lines']} lines"
        )

    print()

    # Quality Recommendations
    print("💡 Quality Recommendations:")
    print("-" * 60)

    recommendations = []

    if long_functions:
        recommendations.append(
            "Consider breaking down long functions into smaller, focused functions"
        )

    if complex_functions:
        recommendations.append("Review complex functions for potential simplification")

    if avg_comment_ratio < 0.2:
        recommendations.append("Consider adding more inline documentation")

    # Check for potential over-engineering
    total_classes = sum(audit["classes"] for audit in audits)
    total_functions = sum(audit["functions"] for audit in audits)

    if total_classes > 15:
        recommendations.append(
            "Consider if all classes are necessary - might be over-engineered"
        )

    if total_lines > 2000:
        recommendations.append(
            "Codebase is getting large - consider modularization strategies"
        )

    # Migration framework complexity check
    migration_files = [
        audit for audit in audits if "migration" in audit["path"].lower()
    ]
    if migration_files:
        migration_lines = sum(audit["total_lines"] for audit in migration_files)
        if migration_lines > 300:
            recommendations.append(
                "Migration framework might be over-engineered for v0.1.0"
            )

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("✅ Code quality looks good - no major issues identified")

    print()

    # Final Assessment
    print("🎯 Final Assessment:")
    print("-" * 60)

    if total_lines < 1500:
        complexity_level = "Simple"
    elif total_lines < 3000:
        complexity_level = "Moderate"
    else:
        complexity_level = "Complex"

    print(f"Codebase complexity: {complexity_level}")
    print(f"Total lines of code: {total_lines}")
    print(f"Documentation ratio: {avg_comment_ratio:.1%}")
    print(f"Average file size: {total_lines // len(audits)} lines" if audits else "N/A")

    # Readiness assessment
    issues = len(long_functions) + len(complex_functions) + len(poorly_documented)

    if issues == 0:
        print("🟢 READY: Code quality is good for continued development")
    elif issues <= 2:
        print(
            "🟡 CAUTION: Minor issues found, but acceptable for continued development"
        )
    else:
        print(
            "🔴 STOP: Multiple quality issues found - recommend refactoring before continuing"
        )

    print()


if __name__ == "__main__":
    main()
