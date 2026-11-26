"""External compiler adapter; requires an existing KnoxMap terrain project."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def commands(python, project, buildings=True):
    result = []
    if buildings:
        result.append([str(python), '-m', 'knoxbuild', str(project)])
    result.extend([
        [str(python), 'tools/validate_tbx.py', str(project / 'buildings')],
        [str(python), 'tools/compile_map.py', str(project)]
    ])
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--knoxmap', type=Path, required=True)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--python', type=Path)
    p.add_argument('--reuse-buildings', action='store_true')
    p.add_argument('--execute', action='store_true', help='Run external compiler; otherwise print plan')
    args = p.parse_args()
    k, project = args.knoxmap.resolve(), args.project.resolve()
    python = args.python.resolve() if args.python else k / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    plan = commands(python, project, not args.reuse_buildings)
    print(json.dumps(plan, indent=2))
    if not args.execute:
        return
    for path in (python, k/'tools/validate_tbx.py', k/'tools/compile_map.py', project):
        if not path.exists():
            p.error(f'Missing required path: {path}')
    if not project.is_dir():
        p.error('Project must be a directory')
    if not args.reuse_buildings and (project/'buildings').exists():
        p.error('Existing buildings may contain manual edits; use --reuse-buildings or a fresh project')
    out = ROOT/'output'; out.mkdir(exist_ok=True)
    manifest = {'started': datetime.now(timezone.utc).isoformat(), 'project': str(project), 'commands': plan,
        'compiler_sha256': hashlib.sha256((k/'tools/compile_map.py').read_bytes()).hexdigest(),
        'status': 'running', 'stages': []}
    target = out/'compile-manifest.json'
    def save():
        target.write_text(json.dumps(manifest, indent=2))
    save()
    try:
        with (out/'compile.log').open('w', encoding='utf-8') as log:
            for command in plan:
                result = subprocess.run(command, cwd=k, stdout=log, stderr=subprocess.STDOUT, check=False)
                manifest['stages'].append({'command':command,'returncode':result.returncode})
                save()
                if result.returncode:
                    raise subprocess.CalledProcessError(result.returncode, command)
        manifest['status'] = 'commands_completed_unverified'
    except BaseException:
        manifest['status'] = 'failed'
        raise
    finally:
        save()

if __name__ == '__main__':
    main()
