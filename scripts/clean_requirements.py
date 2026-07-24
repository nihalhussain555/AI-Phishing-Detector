import os
import ast
from pathlib import Path

def get_imported_modules(root: str) -> set:
    """Recursively parse .py files to collect top‑level imported module names."""
    modules = set()
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if not filename.endswith('.py'):
                continue
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=file_path)
            except Exception:
                # Skip files that cannot be parsed
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        modules.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        modules.add(node.module.split('.')[0])
    return modules

# Mapping for imports whose package name differs from the import name
IMPORT_TO_REQ = {
    'sklearn': 'scikit-learn',
    'PIL': 'Pillow',
    'bs4': 'beautifulsoup4',
    'dotenv': 'python-dotenv',
    'whois': 'python-whois',
    'tldextract': 'tldextract',
    'lxml': 'lxml',
    'requests': 'requests',
    'flask': 'Flask',
    'werkzeug': 'Werkzeug',
    'jinja2': 'Jinja2',
    'itsdangerous': 'itsdangerous',
    'click': 'click',
    'blinker': 'blinker',
    'pymongo': 'pymongo',
    'dnspython': 'dnspython',
    'torch': 'torch',
    'transformers': 'transformers',
    'sentence_transformers': 'sentence-transformers',
    'groq': 'groq',
    'tqdm': 'tqdm',
    'typing_extensions': 'typing_extensions',
    'joblib': 'joblib',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'scipy': 'scipy',
    'threadpoolctl': 'threadpoolctl',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'html5lib': 'html5lib',
    'soupsieve': 'soupsieve',
    'Pillow': 'Pillow',
}

def map_import_to_requirement(import_name: str, req_lines: list) -> str | None:
    """Return the matching requirement line (including version) for a given import name."""
    # Direct match first
    for line in req_lines:
        pkg = line.split('>')[0].strip().lower()
        if pkg == import_name.lower():
            return line
    # Mapping lookup
    mapped = IMPORT_TO_REQ.get(import_name)
    if mapped:
        for line in req_lines:
            pkg = line.split('>')[0].strip().lower()
            if pkg == mapped.lower():
                return line
    return None

def main():
    project_root = Path(__file__).resolve().parents[1]
    req_path = project_root / "requirements.txt"
    with req_path.open('r', encoding='utf-8') as f:
        req_lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith('#')]

    imported_modules = get_imported_modules(str(project_root))

    kept_requirements = []
    for mod in imported_modules:
        line = map_import_to_requirement(mod, req_lines)
        if line:
            kept_requirements.append(line)

    # Always keep gunicorn for deployment if present
    for line in req_lines:
        if line.lower().startswith('gunicorn'):
            kept_requirements.append(line)

    # Remove duplicates and sort for reproducibility
    final_requirements = sorted(set(kept_requirements))

    out_path = project_root / "requirements_clean.txt"
    with out_path.open('w', encoding='utf-8') as f:
        for line in final_requirements:
            f.write(line + "\n")
    print(f"Cleaned requirements written to {out_path}")

if __name__ == "__main__":
    main()
