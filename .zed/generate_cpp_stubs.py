#!/usr/bin/env python3
"""
Generate C++ implementation stubs from header file declarations.
Usage: python generate_cpp_stubs.py <header_file.hpp>
"""

import sys
import re
from pathlib import Path


def extract_class_name(content):
    """Extract the main class name from header content."""
    match = re.search(r'class\s+(\w+)', content)
    return match.group(1) if match else None


def extract_namespace(content):
    """Extract namespace if present."""
    match = re.search(r'namespace\s+(\w+)', content)
    return match.group(1) if match else None


def extract_method_declarations(content, class_name):
    """Extract method declarations from a class."""
    methods = []

    # Find class body
    class_pattern = rf'class\s+{class_name}\s*{{(.*?)}};'
    class_match = re.search(class_pattern, content, re.DOTALL)

    if not class_match:
        print(f"Debug: Could not find class body for '{class_name}'")
        return methods

    class_body = class_match.group(1)
    print(f"Debug: Found class body, length = {len(class_body)}")

    # Match constructors first (ClassName(...);)
    constructor_pattern = rf'^\s*{class_name}\s*\(([^)]*)\)\s*;'
    for match in re.finditer(constructor_pattern, class_body, re.MULTILINE):
        params = match.group(1).strip()
        print(f"Debug: Constructor found - {class_name}({params})")
        methods.append({
            'return_type': '',  # Constructors have no return type
            'name': class_name,
            'params': params,
            'qualifiers': ''
        })

    # Match method declarations (ignoring destructors, inline implementations)
    # Pattern: [attributes] [virtual] return_type method_name(params) qualifiers;
    method_pattern = r'^\s*(?:\[\[[\w\s]+\]\]\s*)*(?:virtual\s+)?(\w+(?:\s*<[^>]+>)?(?:\s*\*|\s*&)?)\s+(\w+)\s*\(([^)]*)\)\s*((?:const|noexcept|override)*)\s*;'

    matches = list(re.finditer(method_pattern, class_body, re.MULTILINE))
    print(f"Debug: Found {len(matches)} method matches")

    for match in matches:
        return_type = match.group(1).strip()
        method_name = match.group(2)
        params = match.group(3).strip()
        qualifiers = match.group(4).strip()

        print(f"Debug: Method found - {return_type} {method_name}({params})")

        # Skip if method name matches class name (constructor - already handled)
        if method_name == class_name:
            print(f"Debug: Skipping constructor {method_name} (already added)")
            continue

        methods.append({
            'return_type': return_type,
            'name': method_name,
            'params': params,
            'qualifiers': qualifiers
        })

    return methods


def generate_cpp_content(header_file, class_name, namespace, methods):
    """Generate the .cpp file content."""
    header_name = Path(header_file).name

    lines = [
        f'#include "{header_name}"',
        '',
    ]

    if namespace:
        lines.append(f'namespace {namespace} {{')
        lines.append('')

    for method in methods:
        # Build method signature
        if method['return_type']:
            # Regular method with return type
            signature = f"{method['return_type']} {class_name}::{method['name']}({method['params']})"
        else:
            # Constructor (no return type)
            signature = f"{class_name}::{method['name']}({method['params']})"

        if method['qualifiers']:
            signature += f" {method['qualifiers']}"

        lines.append(f'{signature} {{')
        lines.append('    // TODO: Implement')
        lines.append('}')
        lines.append('')

    if namespace:
        lines.append(f'}} // namespace {namespace}')

    return '\n'.join(lines)


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_cpp_stubs.py <header_file.hpp>")
        sys.exit(1)

    header_file = sys.argv[1]
    # Convert Windows backslashes to forward slashes
    header_file = header_file.replace('\\', '/')
    header_path = Path(header_file)

    if not header_path.exists():
        print(f"Error: File '{header_file}' not found")
        sys.exit(1)

    # Read header file
    content = header_path.read_text(encoding='utf-8')

    # Extract information
    class_name = extract_class_name(content)
    if not class_name:
        print("Error: No class found in header file")
        sys.exit(1)

    namespace = extract_namespace(content)
    methods = extract_method_declarations(content, class_name)

    if not methods:
        print(f"No methods found in class {class_name}")
        sys.exit(0)

    # Generate .cpp content
    cpp_content = generate_cpp_content(header_file, class_name, namespace, methods)

    # Determine output path (include/ -> src/)
    if 'include' in header_path.parts:
        # Replace 'include' with 'src' in path
        parts = list(header_path.parts)
        if 'include' in parts:
            include_idx = parts.index('include')
            parts[include_idx] = 'src'

        # Change extension to .cpp
        parts[-1] = header_path.stem + '.cpp'
        cpp_path = Path(*parts)
    else:
        # Just put it in src/ with same name
        cpp_path = Path('src') / (header_path.stem + '.cpp')

    # Create directory if needed
    cpp_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if file exists
    if cpp_path.exists():
        response = input(f"{cpp_path} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    # Write file
    cpp_path.write_text(cpp_content, encoding='utf-8')
    print(f"Generated: {cpp_path}")
    print(f"Found {len(methods)} methods in class {class_name}")


if __name__ == '__main__':
    main()
