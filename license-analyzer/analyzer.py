import os
import json
import urllib.request
import urllib.error
import re
import concurrent.futures
from pathlib import Path

def get_pypi_license(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            info = data.get('info', {})
            return info.get('license') or "Unknown"
    except Exception:
        return "Unknown"

def get_npm_license(package_name):
    # Handle scoped packages
    url_name = package_name.replace("/", "%2f")
    url = f"https://registry.npmjs.org/{url_name}/latest"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            license_val = data.get('license')
            if isinstance(license_val, dict):
                return license_val.get('type', "Unknown")
            return license_val or "Unknown"
    except Exception:
        return "Unknown"

def parse_pyproject_toml(file_path):
    packages = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple regex parser for dependencies in TOML
            # This is a bit naive but should work for most cases without a TOML parser
            in_deps = False
            for line in content.splitlines():
                line = line.strip()
                if line.startswith('[') and ('dependencies' in line or 'dev-dependencies' in line):
                    in_deps = True
                elif line.startswith('[') and in_deps:
                    in_deps = False
                elif in_deps and '=' in line:
                    package = line.split('=')[0].strip().strip('"').strip("'")
                    if package and not package.startswith('#'):
                        packages.add(package)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return packages

def parse_package_json(file_path):
    packages = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            deps = data.get('dependencies', {})
            dev_deps = data.get('devDependencies', {})
            packages.update(deps.keys())
            packages.update(dev_deps.keys())
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return packages

def parse_requirements_txt(file_path):
    packages = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '-')):
                    # basic split for pkg==version, pkg>=version, etc.
                    pkg = re.split(r'[=<>!]', line)[0].strip()
                    if pkg:
                        packages.add(pkg)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return packages

def parse_uv_lock(file_path):
    packages = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # uv.lock is TOML or similar
            # look for [[package]] then name = "..."
            in_pkg = False
            for line in content.splitlines():
                line = line.strip()
                if line == '[[package]]':
                    in_pkg = True
                elif in_pkg and line.startswith('name = '):
                    pkg = line.split('=')[1].strip().strip('"').strip("'")
                    packages.add(pkg)
                    in_pkg = False
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return packages

def analyze_compatibility(main_license, dep_license):
    if not dep_license or dep_license == "Unknown":
        return "Risk"
    
    permissive = ["MIT", "Apache", "BSD", "ISC", "Unlicense", "CC0", "LiLiQ-P"]
    copyleft = ["GPL", "AGPL", "LGPL", "MPL", "EPL", "EUPL"]
    
    dep_license_upper = dep_license.upper()
    
    for p in permissive:
        if p.upper() in dep_license_upper:
            return "Compatible"
    
    for c in copyleft:
        if c.upper() in dep_license_upper:
            return "Risk" # Copyleft can be tricky with LiLiQ-P
            
    return "Untreated"

def detect_repo_license(root):
    license_files = ['LICENSE', 'LICENSE.md', 'LICENSE.txt']
    for lf in license_files:
        path = root / lf
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().strip()
                    if '# ' in first_line:
                        return first_line.replace('# ', '')
                    return first_line
            except:
                pass
    return "Unknown"

def to_yaml(data, indent=0):
    lines = []
    spacer = "  " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{spacer}{k}:")
                lines.append(to_yaml(v, indent + 1))
            else:
                lines.append(f"{spacer}{k}: {v}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{spacer}-")
                lines.append(to_yaml(item, indent + 1))
            else:
                lines.append(f"{spacer}- {item}")
    return "\n".join(lines)

def main():
    root = Path(__file__).parent.parent.resolve()
    print(f"Analyzing repository at {root}")
    
    main_license_name = detect_repo_license(root)
    print(f"Detected repository license: {main_license_name}")
    
    python_packages = set()
    node_packages = set()
    
    exclude_dirs = {'.git', 'node_modules', '.venv', 'venv', 'dist', 'build', '__pycache__', 'license-analyzer'}
    
    for path in root.rglob('*'):
        # Check if any parent of the path is in exclude_dirs
        if any(part in exclude_dirs for part in path.relative_to(root).parts):
            continue
            
        if path.name == 'pyproject.toml':
            python_packages.update(parse_pyproject_toml(path))
        elif path.name == 'package.json':
            node_packages.update(parse_package_json(path))
        elif path.name == 'requirements.txt':
            python_packages.update(parse_requirements_txt(path))
        elif path.name == 'uv.lock':
            python_packages.update(parse_uv_lock(path))

    print(f"Found {len(python_packages)} unique Python packages")
    print(f"Found {len(node_packages)} unique Node.js packages")
    
    all_data = {
        "python": {},
        "node": {}
    }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Python
        future_to_py = {executor.submit(get_pypi_license, pkg): pkg for pkg in python_packages if pkg}
        for future in concurrent.futures.as_completed(future_to_py):
            pkg = future_to_py[future]
            all_data["python"][pkg] = future.result()
            
        # Node
        future_to_node = {executor.submit(get_npm_license, pkg): pkg for pkg in node_packages if pkg}
        for future in concurrent.futures.as_completed(future_to_node):
            pkg = future_to_node[future]
            all_data["node"][pkg] = future.result()

    # Group by license
    by_license = {}
    
    for pkg, lic in all_data["python"].items():
        if not lic: lic = "Unknown"
        if lic not in by_license: by_license[lic] = []
        by_license[lic].append({"name": pkg, "type": "Python"})

    for pkg, lic in all_data["node"].items():
        if not lic: lic = "Unknown"
        if lic not in by_license: by_license[lic] = []
        by_license[lic].append({"name": pkg, "type": "Node.js"})

    # Save JSON and YAML
    with open("licenses.json", "w") as f:
        json.dump(by_license, f, indent=2)
    
    with open("licenses.yaml", "w") as f:
        f.write(to_yaml(by_license))
        
    # Generate Markdown
    with open("local_analysis.md", "w", encoding='utf-8') as f:
        f.write(f"# Local License Analysis Report\n\n")
        f.write(f"**Main Repository License:** {main_license_name}\n\n")
        f.write(f"## Summary\n\n")
        
        total_pkgs = len(python_packages) + len(node_packages)
        f.write(f"- Total Unique Packages: {total_pkgs}\n")
        f.write(f"- Python Packages: {len(python_packages)}\n")
        f.write(f"- Node.js Packages: {len(node_packages)}\n\n")
        
        f.write(f"## Compatibility Breakdown\n\n")
        f.write(f"| License | Count | Status |\n")
        f.write(f"| :--- | :--- | :--- |\n")
        
        for lic, pkgs in sorted(by_license.items()):
            status = analyze_compatibility(main_license_name, lic)
            display_lic = lic.split('\n')[0][:100]
            f.write(f"| {display_lic} | {len(pkgs)} | {status} |\n")
            
        f.write(f"\n## Detailed List by License\n\n")
        for lic, pkgs in sorted(by_license.items()):
            display_lic = lic.split('\n')[0][:100]
            f.write(f"### {display_lic}\n")
            for pkg in sorted(pkgs, key=lambda x: x['name']):
                f.write(f"- {pkg['name']} ({pkg['type']})\n")
            f.write(f"\n")

    print("Analysis complete. Results saved in licenses.json, licenses.yaml and local_analysis.md")

if __name__ == "__main__":
    main()
