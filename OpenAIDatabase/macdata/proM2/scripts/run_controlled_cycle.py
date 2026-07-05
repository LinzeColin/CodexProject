#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macdata controlled Codex Automation tool.

This script is intentionally NOT self-scheduling. It is only a deterministic tool
that Codex Automation or the user may call after explicit approval. It never
installs launchd/cron jobs. After a verified GitHub upload it may run the
owner-confirmed cleanup policy for Docker, Homebrew, system cache best-effort
purge, project cache whitelist paths, and its own macdata cache. It writes
records inside its own macdata device directory and uses a short-lived temporary
clone to upload daily records to a device-specific GitHub archive branch.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_PATH = Path(__file__).resolve()
DEVICE_ROOT = SCRIPT_PATH.parents[1]
CONFIG_PATH = DEVICE_ROOT / 'config' / 'device_config.json'
OWNER_CONFIRMATIONS_PATH = DEVICE_ROOT / 'config' / 'owner_confirmations.json'

HIGH_RISK_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|bearer[_-]?token|password|passwd|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{12,}"),
]


def now_local_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec='seconds')


def date_dir() -> str:
    return _dt.datetime.now().astimezone().strftime('%Y-%m-%d')


def run_id(device_key: str) -> str:
    return f"{device_key}-{_dt.datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')}"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def cmd(args: List[str], cwd: Optional[Path] = None, timeout: int = 30, allow_fail: bool = True) -> Dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(args, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout)
        return {
            'ok': proc.returncode == 0,
            'returncode': proc.returncode,
            'stdout': sanitize_text(proc.stdout.strip()),
            'stderr': sanitize_text(proc.stderr.strip()),
            'seconds': round(time.time() - started, 3),
            'args0': args[0] if args else '',
        }
    except FileNotFoundError as e:
        if not allow_fail:
            raise
        return {'ok': False, 'returncode': 127, 'stdout': '', 'stderr': str(e), 'seconds': round(time.time() - started, 3), 'args0': args[0] if args else ''}
    except subprocess.TimeoutExpired as e:
        if not allow_fail:
            raise
        return {'ok': False, 'returncode': 124, 'stdout': sanitize_text((e.stdout or '').strip() if isinstance(e.stdout, str) else ''), 'stderr': f'命令超时：{timeout}s', 'seconds': round(time.time() - started, 3), 'args0': args[0] if args else ''}


def sanitize_text(text: str) -> str:
    out = text or ''
    for pat in HIGH_RISK_SECRET_PATTERNS:
        out = pat.sub('[已移除凭证类敏感值]', out)
    return out


def scan_for_secrets(paths: List[Path]) -> Tuple[bool, List[str]]:
    findings: List[str] = []
    for path in paths:
        if not path.exists() or path.is_dir():
            continue
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:  # pragma: no cover
            findings.append(f'{path}: 无法读取用于凭证扫描：{e}')
            continue
        for pat in HIGH_RISK_SECRET_PATTERNS:
            if pat.search(text):
                findings.append(f'{path}: 命中凭证类高风险模式 {pat.pattern[:60]}...')
    return (len(findings) == 0, findings)


def parse_gb_from_bytes(value: int) -> float:
    return round(value / (1024 ** 3), 2)


def disk_usage_root() -> Dict[str, Any]:
    usage = shutil.disk_usage('/')
    used = usage.total - usage.free
    return {
        'root_total_gb': parse_gb_from_bytes(usage.total),
        'root_used_gb': parse_gb_from_bytes(used),
        'root_free_gb': parse_gb_from_bytes(usage.free),
        'root_percent_used': round(used / usage.total * 100, 1) if usage.total else None,
    }


def parse_system_profiler_json(stdout: str) -> Dict[str, Any]:
    if not stdout:
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {}


def find_value_recursive(obj: Any, keys: List[str]) -> Optional[Any]:
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] not in ('', None):
                return obj[k]
        for v in obj.values():
            found = find_value_recursive(v, keys)
            if found not in ('', None):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_value_recursive(item, keys)
            if found not in ('', None):
                return found
    return None


def hardware_from_system_profiler() -> Dict[str, Any]:
    sp = cmd(['system_profiler', 'SPHardwareDataType', 'SPPowerDataType', 'SPSoftwareDataType', '-json'], timeout=60)
    parsed = parse_system_profiler_json(sp.get('stdout', '')) if sp['ok'] else {}
    hardware = {
        'system_profiler_ok': sp['ok'],
        'system_profiler_error': sp.get('stderr', '') if not sp['ok'] else '',
        'model_name': find_value_recursive(parsed, ['machine_name', '_name', 'model_name']),
        'model_identifier': find_value_recursive(parsed, ['machine_model', 'model_identifier']),
        'chip_type': find_value_recursive(parsed, ['chip_type', 'cpu_type', 'processor_name']),
        'physical_memory_text': find_value_recursive(parsed, ['physical_memory', 'current_memory']),
        'serial_number': find_value_recursive(parsed, ['serial_number', 'serial_number_system']),
        'battery_cycle_count': find_value_recursive(parsed, ['sppower_battery_cycle_count', 'cycle_count']),
        'battery_maximum_capacity_percent': find_value_recursive(parsed, ['sppower_battery_health_maximum_capacity', 'maximum_capacity']),
        'battery_condition': find_value_recursive(parsed, ['sppower_battery_health', 'condition']),
        'software_version': find_value_recursive(parsed, ['os_version', 'system_version']),
        'raw_available': bool(parsed),
    }
    return hardware


def parse_memory_gb_from_text(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    m = re.search(r'(\d+(?:\.\d+)?)\s*GB', str(text), re.I)
    if m:
        return float(m.group(1))
    return None


def memory_metrics() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    sysctl_mem = cmd(['sysctl', '-n', 'hw.memsize'], timeout=10)
    if sysctl_mem['ok']:
        try:
            out['physical_memory_gb'] = parse_gb_from_bytes(int(sysctl_mem['stdout'].strip()))
        except Exception:
            out['physical_memory_gb'] = None
    else:
        out['physical_memory_gb'] = None
    swap = cmd(['sysctl', 'vm.swapusage'], timeout=10)
    out['swapusage_raw'] = swap['stdout'] if swap['ok'] else swap.get('stderr', '')
    out['swap_used_gb'] = parse_swap_used_gb(out['swapusage_raw'])
    vmstat = cmd(['vm_stat'], timeout=10)
    out['vm_stat_summary'] = first_lines(vmstat['stdout'], 18) if vmstat['ok'] else vmstat.get('stderr', '')
    return out


def parse_swap_used_gb(text: str) -> Optional[float]:
    # macOS example: vm.swapusage: total = 2048.00M  used = 0.00M  free = 2048.00M  (encrypted)
    m = re.search(r'used\s*=\s*([0-9.]+)\s*([KMG])', text or '', re.I)
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2).upper()
    if unit == 'K':
        return round(value / (1024 * 1024), 2)
    if unit == 'M':
        return round(value / 1024, 2)
    return round(value, 2)


def first_lines(text: str, n: int) -> str:
    return '\n'.join((text or '').splitlines()[:n])


def pmset_battery() -> Dict[str, Any]:
    batt = cmd(['pmset', '-g', 'batt'], timeout=10)
    out = {'pmset_batt_raw': batt['stdout'] if batt['ok'] else batt.get('stderr', ''), 'current_charge_percent': None, 'charging_state': None, 'power_source': None}
    text = out['pmset_batt_raw']
    m = re.search(r'(\d+)%', text or '')
    if m:
        out['current_charge_percent'] = int(m.group(1))
    if 'AC Power' in (text or ''):
        out['power_source'] = '电源适配器'
    elif 'Battery Power' in (text or ''):
        out['power_source'] = '电池'
    if 'charging' in (text or '').lower():
        out['charging_state'] = '正在充电'
    elif 'discharging' in (text or '').lower():
        out['charging_state'] = '正在放电'
    elif 'charged' in (text or '').lower():
        out['charging_state'] = '已充满或接近满电'
    return out


def top_processes() -> Dict[str, Any]:
    # command field is process name on macOS top; avoid command line arguments.
    cpu = cmd(['top', '-l', '1', '-o', 'cpu', '-stats', 'pid,command,cpu,mem', '-n', '8'], timeout=15)
    mem = cmd(['top', '-l', '1', '-o', 'mem', '-stats', 'pid,command,cpu,mem', '-n', '8'], timeout=15)
    return {
        'top_cpu_raw': first_lines(cpu['stdout'], 16) if cpu['ok'] else cpu.get('stderr', ''),
        'top_memory_raw': first_lines(mem['stdout'], 16) if mem['ok'] else mem.get('stderr', ''),
    }


def du_k(path: Path, timeout: int = 20) -> Dict[str, Any]:
    if not path.exists():
        return {'path': str(path), 'exists': False, 'size_gb': None, 'error': '路径不存在'}
    res = cmd(['du', '-sk', str(path)], timeout=timeout)
    if not res['ok']:
        return {'path': str(path), 'exists': True, 'size_gb': None, 'error': res.get('stderr', '') or 'du 失败'}
    try:
        kb = int(res['stdout'].split()[0])
        return {'path': str(path), 'exists': True, 'size_gb': round(kb / (1024 ** 2), 2), 'error': ''}
    except Exception as e:
        return {'path': str(path), 'exists': True, 'size_gb': None, 'error': str(e)}


def git_metrics(repo_root: Path, device_rel_dir: str) -> Dict[str, Any]:
    latest = cmd(['git', '-C', str(repo_root), 'log', '-1', '--pretty=format:%H %s'], timeout=10)
    branch = cmd(['git', '-C', str(repo_root), 'rev-parse', '--abbrev-ref', 'HEAD'], timeout=10)
    dirty = cmd(['git', '-C', str(repo_root), 'status', '--porcelain=v1', '-uno'], timeout=20)
    device_dirty = cmd(['git', '-C', str(repo_root), 'status', '--porcelain=v1', '--', device_rel_dir], timeout=20)
    untracked = cmd(['git', '-C', str(repo_root), 'ls-files', '--others', '--exclude-standard', '--', device_rel_dir], timeout=20)
    return {
        'repo_root': str(repo_root),
        'branch': branch['stdout'] if branch['ok'] else '未采集',
        'latest_commit': latest['stdout'] if latest['ok'] else '未采集',
        'tracked_dirty_count_repo': len([l for l in dirty.get('stdout', '').splitlines() if l.strip()]) if dirty['ok'] else None,
        'device_dirty_count': len([l for l in device_dirty.get('stdout', '').splitlines() if l.strip()]) if device_dirty['ok'] else None,
        'device_untracked_count': len([l for l in untracked.get('stdout', '').splitlines() if l.strip()]) if untracked['ok'] else None,
    }


def docker_metrics() -> Dict[str, Any]:
    version = cmd(['docker', '--version'], timeout=10)
    if not version['ok']:
        return {'docker_installed': False, 'docker_version': '未安装或不可用', 'docker_system_df': '未采集'}
    df = cmd(['docker', 'system', 'df'], timeout=20)
    return {'docker_installed': True, 'docker_version': version['stdout'], 'docker_system_df': df['stdout'] if df['ok'] else df.get('stderr', '')}


def brew_metrics() -> Dict[str, Any]:
    version = cmd(['brew', '--version'], timeout=10)
    if not version['ok']:
        return {'brew_available': False, 'brew_version': '未安装或不可用', 'brew_formula_count': None, 'brew_cask_count': None}
    formula = cmd(['bash', '-lc', 'brew list --formula 2>/dev/null | wc -l'], timeout=15)
    cask = cmd(['bash', '-lc', 'brew list --cask 2>/dev/null | wc -l'], timeout=15)
    def parse_count(res: Dict[str, Any]) -> Optional[int]:
        try:
            return int((res.get('stdout') or '').strip())
        except Exception:
            return None
    return {'brew_available': True, 'brew_version': first_lines(version['stdout'], 1), 'brew_formula_count': parse_count(formula), 'brew_cask_count': parse_count(cask)}


def air_remote_readiness() -> Dict[str, Any]:
    home = Path.home()
    ssh_config = home / '.ssh' / 'config'
    vscode = cmd(['bash', '-lc', 'command -v code >/dev/null 2>&1 && code --version | head -1 || true'], timeout=10)
    gh = cmd(['bash', '-lc', 'command -v gh >/dev/null 2>&1 && gh --version | head -1 || true'], timeout=10)
    return {
        'ssh_config_exists': ssh_config.exists(),
        'vscode_cli_available': bool(vscode.get('stdout', '').strip()),
        'vscode_cli_version': vscode.get('stdout', '').strip() or '未发现 code 命令',
        'github_cli_available': bool(gh.get('stdout', '').strip()),
        'github_cli_version': gh.get('stdout', '').strip() or '未发现 gh 命令',
        'codespaces_cli_check': '仅检查 gh 是否存在；不自动访问 Codespaces，避免额外网络/权限动作。',
    }


def collect_metrics(repo_root: Path, config: Dict[str, Any], run_id_value: str) -> Dict[str, Any]:
    device_rel_dir = config['local_relative_dir']
    hardware = hardware_from_system_profiler()
    pmset = pmset_battery()
    storage = disk_usage_root()
    memory = memory_metrics()
    top = top_processes()
    repo = git_metrics(repo_root, device_rel_dir)
    home = Path.home()
    sizes: Dict[str, Any] = {
        'device_root_size': du_k(DEVICE_ROOT, timeout=20),
        'downloads_size': du_k(home / 'Downloads', timeout=20),
        'desktop_size': du_k(home / 'Desktop', timeout=20),
        'documents_size': du_k(home / 'Documents', timeout=20),
    }
    if config.get('collect_development_load'):
        sizes['repo_root_size'] = du_k(repo_root, timeout=int(config.get('du_repo_timeout_seconds', 30)))
        sizes['repo_openai_database_size'] = du_k(repo_root / 'OpenAIDatabase', timeout=25)
    metrics: Dict[str, Any] = {
        'schema_version': 'macdata-record-v1',
        'device_key': config['device_key'],
        'device_label_cn': config['device_label_cn'],
        'device_role_cn': config['device_role_cn'],
        'run_id': run_id_value,
        'collected_at_local': now_local_iso(),
        'timezone_expected': config['timezone'],
        'repo_root': str(repo_root),
        'hardware': hardware,
        'pmset': pmset,
        'storage': storage,
        'memory': memory,
        'top_processes': top,
        'git': repo,
        'sizes': sizes,
        'docker': docker_metrics() if config.get('collect_docker') else {'docker_installed': '未采集'},
        'brew': brew_metrics() if config.get('collect_brew') else {'brew_available': '未采集'},
        'air_remote_readiness': air_remote_readiness() if config.get('collect_air_ladder_status') else {'status': 'Pro 设备不采集 Air 远程入口状态'},
        'collector_notes': [
            '本记录不采集 Time Machine。',
            '本记录不使用 iCloud。',
            '本记录不采集 API key、token、password、cookie、session、Keychain、shell history、完整环境变量。',
            '远程上传验证成功后，脚本会按 owner 确认的白名单策略清理 Docker、Homebrew、系统缓存和项目缓存。',
        ],
    }
    metrics['risk'] = evaluate_risk(metrics, config)
    return metrics


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)', str(value))
    return float(m.group(1)) if m else None


def evaluate_risk(metrics: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    storage = metrics.get('storage', {})
    free_gb = to_float(storage.get('root_free_gb'))
    storage_level = '未采集'
    if free_gb is not None:
        if free_gb < config['storage_red_free_gb']:
            storage_level = '红色'
        elif free_gb < config['storage_yellow_free_gb']:
            storage_level = '黄色'
        else:
            storage_level = '绿色'
    swap_gb = to_float(metrics.get('memory', {}).get('swap_used_gb'))
    swap_level = '未采集'
    if swap_gb is not None:
        if swap_gb >= config['swap_red_gb']:
            swap_level = '红色'
        elif swap_gb >= config['swap_yellow_gb']:
            swap_level = '黄色'
        else:
            swap_level = '绿色'
    cap = to_float(metrics.get('hardware', {}).get('battery_maximum_capacity_percent'))
    batt_level = '未采集'
    if cap is not None:
        if cap < 80:
            batt_level = '红色'
        elif cap < 85:
            batt_level = '黄色'
        else:
            batt_level = '绿色'
    return {
        'storage_level': storage_level,
        'swap_level': swap_level,
        'battery_capacity_level': batt_level,
        'overall_level': worst_level([storage_level, swap_level, batt_level]),
    }


def worst_level(levels: List[str]) -> str:
    order = {'红色': 3, '黄色': 2, '绿色': 1, '未采集': 0}
    return max(levels, key=lambda x: order.get(x, 0)) if levels else '未采集'


def preflight_device(config: Dict[str, Any], owner: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str], Dict[str, Any]]:
    hardware = hardware_from_system_profiler()
    messages: List[str] = []
    ok = True
    if platform.system() != 'Darwin':
        ok = False
        messages.append('当前系统不是 macOS。此任务只允许在目标 Mac 本机运行。')
    model_text = ' '.join(str(hardware.get(k) or '') for k in ['model_name', 'model_identifier'])
    for keyword in config.get('expected_model_keywords', []):
        if keyword and keyword not in model_text:
            ok = False
            messages.append(f'设备型号未命中预期关键词：{keyword}；实际：{model_text or "未采集"}')
    chip_text = str(hardware.get('chip_type') or '')
    expected_chip_keywords = config.get('expected_chip_keywords', [])
    if expected_chip_keywords and chip_text:
        if not any(keyword in chip_text for keyword in expected_chip_keywords):
            ok = False
            messages.append(f'芯片未命中预期关键词：{expected_chip_keywords}；实际：{chip_text}')
    elif expected_chip_keywords and not chip_text:
        messages.append('芯片字段未采集到；需要 Codex 在运行前向用户确认。')
        ok = False
    mem_text = hardware.get('physical_memory_text')
    mem_gb = parse_memory_gb_from_text(str(mem_text or ''))
    expected_min = config.get('expected_memory_gb_min')
    if expected_min and mem_gb is not None and mem_gb < float(expected_min):
        ok = False
        messages.append(f'内存低于预期：预期至少 {expected_min}GB，实际 {mem_gb}GB。')
    if owner:
        expected_device_key = owner.get('confirmed_device_key')
        if expected_device_key != config['device_key']:
            ok = False
            messages.append(f'owner_confirmations.json 设备键不匹配：{expected_device_key} != {config["device_key"]}')
    if ok:
        messages.append('设备预检通过。')
    return ok, messages, hardware


def require_owner_confirmations(config: Dict[str, Any]) -> Dict[str, Any]:
    if not OWNER_CONFIRMATIONS_PATH.exists():
        raise SystemExit(
            '缺少 config/owner_confirmations.json。\n'
            'Codex 必须先向用户提问并得到明确答复，然后根据 config/owner_confirmations.example.json 创建该文件；未确认前禁止执行采集、上传和清理。'
        )
    owner = load_json(OWNER_CONFIRMATIONS_PATH)
    required_true = [
        'run_full_cycle_confirmed',
        'allow_plaintext_device_metrics_to_github',
        'allow_github_upload',
        'allow_delete_local_macdata_older_than_3_days_after_verified_upload',
        'allow_development_cache_cleanup_after_verified_upload',
        'understand_no_timemachine_no_icloud',
        'understand_scripts_do_not_auto_schedule',
    ]
    missing = [k for k in required_true if owner.get(k) is not True]
    if missing:
        raise SystemExit(f'owner_confirmations.json 未确认必要项：{missing}')
    if owner.get('confirmed_device_key') != config['device_key']:
        raise SystemExit(f'owner_confirmations.json 设备键不匹配：{owner.get("confirmed_device_key")} != {config["device_key"]}')
    return owner


def retention_cutoff(retention_days: int) -> _dt.date:
    return _dt.datetime.now().astimezone().date() - _dt.timedelta(days=retention_days - 1)


def cleanup_retention(base_dirs: List[Path], retention_days: int, dry_run: bool = False) -> Dict[str, Any]:
    cutoff = retention_cutoff(retention_days)
    deleted_files = 0
    deleted_dirs = 0
    freed_bytes = 0
    deleted_paths: List[str] = []
    for base in base_dirs:
        if not base.exists():
            continue
        for child in sorted(base.iterdir()):
            # Date folders are YYYY-MM-DD. Non-date cache folders are removed by caller only when under cache.
            delete = False
            try:
                child_date = _dt.date.fromisoformat(child.name)
                delete = child_date < cutoff
            except ValueError:
                continue
            if delete:
                size = path_size_bytes(child)
                if not dry_run:
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                        deleted_dirs += 1
                    else:
                        child.unlink(missing_ok=True)
                        deleted_files += 1
                freed_bytes += size
                deleted_paths.append(str(child))
    return {
        'retention_days': retention_days,
        'cutoff_date_kept_from': cutoff.isoformat(),
        'deleted_files': deleted_files,
        'deleted_dirs': deleted_dirs,
        'freed_mb': round(freed_bytes / (1024 ** 2), 2),
        'deleted_paths': deleted_paths[:200],
        'dry_run': dry_run,
    }


def path_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for root, dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except FileNotFoundError:
                pass
    return total


def cleanup_cache() -> Dict[str, Any]:
    cache = DEVICE_ROOT / 'data' / 'cache'
    archive_cache = cache / 'archive_push'
    size = path_size_bytes(archive_cache)
    if archive_cache.exists():
        shutil.rmtree(archive_cache, ignore_errors=True)
    archive_cache.mkdir(parents=True, exist_ok=True)
    keep = archive_cache / '.gitkeep'
    keep.write_text('', encoding='utf-8')
    return {'cache_path': str(archive_cache), 'freed_mb': round(size / (1024 ** 2), 2), 'status': '已清理 macdata 临时上传缓存'}


def _cleanup_cmd_summary(label: str, command: List[str], result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'target': label,
        'ok': result.get('ok'),
        'returncode': result.get('returncode'),
        'command': ' '.join(command),
        'stdout': first_lines(result.get('stdout', ''), 20),
        'stderr': first_lines(result.get('stderr', ''), 20),
        'seconds': result.get('seconds'),
    }


def cleanup_docker(policy: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    docker_policy = policy.get('docker', {})
    if not docker_policy.get('enabled'):
        return {'status': '未启用', 'target': 'docker'}
    version = cmd(['docker', '--version'], timeout=10)
    if not version.get('ok'):
        return {'status': '已跳过', 'target': 'docker', 'reason': 'docker 命令不可用', 'stderr': version.get('stderr', '')}
    command = ['docker', 'system', 'prune', '-f']
    if docker_policy.get('prune_all_images'):
        command.append('-a')
    if docker_policy.get('prune_volumes'):
        command.append('--volumes')
    if dry_run:
        return {'status': 'dry_run', 'target': 'docker', 'command': ' '.join(command)}
    result = cmd(command, timeout=240)
    summary = _cleanup_cmd_summary('docker', command, result)
    summary['status'] = '已执行' if result.get('ok') else '执行失败'
    summary['safety'] = '不使用 -a，不清理 volumes，除非配置显式打开。'
    return summary


def cleanup_homebrew(policy: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    brew_policy = policy.get('homebrew', {})
    if not brew_policy.get('enabled'):
        return {'status': '未启用', 'target': 'homebrew'}
    version = cmd(['brew', '--version'], timeout=10)
    if not version.get('ok'):
        return {'status': '已跳过', 'target': 'homebrew', 'reason': 'brew 命令不可用', 'stderr': version.get('stderr', '')}
    command = ['brew', 'cleanup']
    if dry_run:
        return {'status': 'dry_run', 'target': 'homebrew', 'command': ' '.join(command)}
    result = cmd(command, timeout=240)
    summary = _cleanup_cmd_summary('homebrew', command, result)
    summary['status'] = '已执行' if result.get('ok') else '执行失败'
    return summary


def cleanup_system_cache(policy: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    system_policy = policy.get('system_cache', {})
    if not system_policy.get('enabled'):
        return {'status': '未启用', 'target': 'system_cache'}
    command = ['purge']
    if dry_run:
        return {'status': 'dry_run', 'target': 'system_cache', 'command': ' '.join(command), 'mode': system_policy.get('mode')}
    result = cmd(command, timeout=120)
    summary = _cleanup_cmd_summary('system_cache', command, result)
    summary['status'] = '已执行' if result.get('ok') else '执行失败或权限不足'
    summary['mode'] = system_policy.get('mode', 'purge_best_effort')
    return summary


def _is_project_cache_candidate(path: Path, repo_root: Path, project_policy: Dict[str, Any]) -> bool:
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    if not rel or rel == '.':
        return False
    parts = rel.split('/')
    skip_names = set(project_policy.get('skip_dir_names', []))
    if any(part in skip_names for part in parts):
        return False
    whitelist_names = set(project_policy.get('whitelist_dir_names', []))
    whitelist_suffixes = tuple(project_policy.get('whitelist_relative_suffixes', []))
    return path.name in whitelist_names or rel.endswith(whitelist_suffixes)


def cleanup_project_cache(repo_root: Path, config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    policy = config.get('post_upload_cleanup_policy', {})
    project_policy = policy.get('project_cache', {})
    if not policy.get('enabled') or not project_policy.get('enabled'):
        return {'status': '未启用', 'target': 'project_cache', 'dry_run': dry_run}
    candidates: List[Path] = []
    skip_names = set(project_policy.get('skip_dir_names', []))
    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)
        rel_parts = set(root_path.relative_to(repo_root).parts) if root_path != repo_root else set()
        if rel_parts.intersection(skip_names):
            dirs[:] = []
            continue
        for dirname in list(dirs):
            candidate = root_path / dirname
            if _is_project_cache_candidate(candidate, repo_root, project_policy):
                candidates.append(candidate)
                dirs.remove(dirname)
            elif dirname in skip_names:
                dirs.remove(dirname)
            elif dirname == 'node_modules':
                node_cache = candidate / '.cache'
                if node_cache.exists() and _is_project_cache_candidate(node_cache, repo_root, project_policy):
                    candidates.append(node_cache)
                dirs.remove(dirname)
    deleted_dirs = 0
    deleted_files = 0
    freed_bytes = 0
    deleted_paths: List[str] = []
    candidate_paths = [str(path.relative_to(repo_root)) for path in candidates]
    for path in candidates:
        size = path_size_bytes(path)
        freed_bytes += size
        if dry_run:
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path, ignore_errors=True)
            deleted_dirs += 1
        elif path.exists():
            path.unlink(missing_ok=True)
            deleted_files += 1
        deleted_paths.append(str(path.relative_to(repo_root)))
    return {
        'status': 'dry_run' if dry_run else '已执行',
        'target': 'project_cache',
        'candidate_count': len(candidates),
        'candidate_paths': candidate_paths[:200],
        'deleted_dirs': deleted_dirs,
        'deleted_files': deleted_files,
        'deleted_paths': deleted_paths[:200],
        'freed_mb': round(freed_bytes / (1024 ** 2), 2),
        'dry_run': dry_run,
    }


def cleanup_development_environment(repo_root: Path, config: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    policy = config.get('post_upload_cleanup_policy', {})
    if not policy.get('enabled'):
        return {'status': '未启用', 'dry_run': dry_run}
    docker = cleanup_docker(policy, dry_run=dry_run)
    homebrew = cleanup_homebrew(policy, dry_run=dry_run)
    system_cache = cleanup_system_cache(policy, dry_run=dry_run)
    project_cache = cleanup_project_cache(repo_root, config, dry_run=dry_run)
    return {
        'status': '已执行受控开发环境清理' if not dry_run else 'dry_run',
        'dry_run': dry_run,
        'docker': docker,
        'homebrew': homebrew,
        'system_cache': system_cache,
        'project_cache': project_cache,
    }


def render_cn_report(metrics: Dict[str, Any], config: Dict[str, Any], upload_status: Optional[Dict[str, Any]] = None, cleanup_status: Optional[Dict[str, Any]] = None) -> str:
    upload_status = upload_status or {'status': '待上传', 'message': '本报告生成时尚未完成 GitHub 上传验证。'}
    cleanup_status = cleanup_status or {'status': '待清理', 'message': '上传验证完成后才允许清理本机旧数据。'}
    hw = metrics.get('hardware', {})
    st = metrics.get('storage', {})
    mem = metrics.get('memory', {})
    pm = metrics.get('pmset', {})
    risk = metrics.get('risk', {})
    git = metrics.get('git', {})
    sizes = metrics.get('sizes', {})
    docker = metrics.get('docker', {})
    brew = metrics.get('brew', {})
    development_cleanup = cleanup_status.get('development_cleanup', {}) if isinstance(cleanup_status, dict) else {}
    project_cleanup = development_cleanup.get('project_cache', {}) if isinstance(development_cleanup, dict) else {}
    docker_cleanup = development_cleanup.get('docker', {}) if isinstance(development_cleanup, dict) else {}
    homebrew_cleanup = development_cleanup.get('homebrew', {}) if isinstance(development_cleanup, dict) else {}
    system_cleanup = development_cleanup.get('system_cache', {}) if isinstance(development_cleanup, dict) else {}
    is_air = config['device_key'].lower().startswith('air')
    device_title = f"{config['device_key']} 每日明文健康报告"

    def val(v: Any) -> str:
        if v is None or v == '':
            return '未采集'
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return str(v)

    roi_lines = roi_text(metrics, config)
    swot_rows = swot_rows_for(config, metrics)
    remote_block = ''
    if is_air:
        ar = metrics.get('air_remote_readiness', {})
        remote_block = f"""
七、Air 逐级使用与远程入口状态

| 指标 | 明文值 |
|---|---|
| SSH 配置文件是否存在 | {val(ar.get('ssh_config_exists'))} |
| VS Code code 命令是否可用 | {val(ar.get('vscode_cli_available'))} |
| VS Code 版本摘要 | {val(ar.get('vscode_cli_version'))} |
| GitHub CLI 是否可用 | {val(ar.get('github_cli_available'))} |
| GitHub CLI 版本摘要 | {val(ar.get('github_cli_version'))} |
| Codespaces 检查说明 | {val(ar.get('codespaces_cli_check'))} |

Air 明文使用边界：Air 作为工作前台、移动终端和云端入口；不建议承担 Docker、本地大构建、本地大模型、多服务开发。若 swap 持续升高或剩余空间低于黄色线，应优先转到 Pro 或 Codespaces。
"""
    else:
        remote_block = f"""
七、Pro 开发负载与膨胀风险

| 指标 | 明文值 |
|---|---|
| Docker 是否可用 | {val(docker.get('docker_installed'))} |
| Docker 版本 | {val(docker.get('docker_version'))} |
| Docker 占用摘要 | {val(docker.get('docker_system_df'))} |
| Homebrew 是否可用 | {val(brew.get('brew_available'))} |
| Homebrew 版本 | {val(brew.get('brew_version'))} |
| Homebrew formula 数量 | {val(brew.get('brew_formula_count'))} |
| Homebrew cask 数量 | {val(brew.get('brew_cask_count'))} |
| CodexProject 目录体积 | {val(sizes.get('repo_root_size', {}).get('size_gb'))} GB |
| OpenAIDatabase 目录体积 | {val(sizes.get('repo_openai_database_size', {}).get('size_gb'))} GB |

Pro 膨胀明文判断：本任务观察 Docker、Homebrew、仓库体积、macdata 体积和常见用户目录；远程上传验证成功后，按 owner 确认策略清理 Docker/Homebrew/系统缓存/项目缓存。
"""

    report = f"""# {device_title}

报告日期：{date_dir()}
采集时间：{val(metrics.get('collected_at_local'))}
设备角色：{config['device_role_cn']}
运行来源：Codex Automation 调用受控脚本
Codex 模型：{config['codex_model']}
推理强度：{config['reasoning_effort']}
报告语言：全中文
Time Machine：本任务不采集
iCloud：本任务不使用
本机保留策略：仅保留最近 {config['retention_days']} 天数据、报告、运行记录和 macdata 临时缓存

一、运行状态

| 项目 | 明文值 |
|---|---|
| 采集编号 | {val(metrics.get('run_id'))} |
| 本机任务目录 | {config['local_relative_dir']} |
| 运行状态 | {val(upload_status.get('status'))} |
| 上传说明 | {val(upload_status.get('message'))} |
| 归档分支 | {val(upload_status.get('archive_branch', config['default_archive_branch']))} |
| 数据提交哈希 | {val(upload_status.get('data_commit_hash'))} |
| 报告提交哈希 | {val(upload_status.get('report_commit_hash'))} |
| 远程验证 | {val(upload_status.get('remote_verified'))} |
| 清理状态 | {val(cleanup_status.get('status'))} |

二、设备基础信息

| 指标 | 明文值 |
|---|---|
| 设备名称 | {val(platform.node())} |
| 设备型号 | {val(hw.get('model_name'))} |
| 型号标识 | {val(hw.get('model_identifier'))} |
| 芯片 | {val(hw.get('chip_type'))} |
| 统一内存 | {val(hw.get('physical_memory_text'))} |
| 序列号 | {val(hw.get('serial_number'))} |
| 本机用户名 | {val(os.environ.get('USER') or os.environ.get('LOGNAME'))} |
| macOS 版本 | {val(hw.get('software_version'))} |
| 当前电源状态 | {val(pm.get('power_source'))} |

三、电池健康

| 指标 | 明文值 |
|---|---|
| 当前电量 | {val(pm.get('current_charge_percent'))}% |
| 是否正在充电 | {val(pm.get('charging_state'))} |
| 电源来源 | {val(pm.get('power_source'))} |
| 电池循环次数 | {val(hw.get('battery_cycle_count'))} |
| 最大容量 | {val(hw.get('battery_maximum_capacity_percent'))} |
| 电池状态 | {val(hw.get('battery_condition'))} |
| 电池风险等级 | {val(risk.get('battery_capacity_level'))} |
| pmset 原文摘要 | {val(pm.get('pmset_batt_raw'))} |

电池明文判断：若最大容量低于 80% 或系统显示建议维修，优先评估换电池；若长期插电且系统支持充电上限，建议使用 80% 或 85%；如果系统没有显示充电上限，则报告只写“未采集/系统未显示”，不猜测。

四、存储健康

| 指标 | 明文值 |
|---|---|
| 根目录总容量 | {val(st.get('root_total_gb'))} GB |
| 根目录已用容量 | {val(st.get('root_used_gb'))} GB |
| 根目录剩余容量 | {val(st.get('root_free_gb'))} GB |
| 根目录使用率 | {val(st.get('root_percent_used'))}% |
| 黄色预警线 | 剩余空间 < {config['storage_yellow_free_gb']} GB |
| 红色预警线 | 剩余空间 < {config['storage_red_free_gb']} GB |
| 当前存储风险等级 | {val(risk.get('storage_level'))} |
| macdata 本机目录体积 | {val(sizes.get('device_root_size', {}).get('size_gb'))} GB |
| 下载目录体积 | {val(sizes.get('downloads_size', {}).get('size_gb'))} GB |
| 桌面目录体积 | {val(sizes.get('desktop_size', {}).get('size_gb'))} GB |
| 文档目录体积 | {val(sizes.get('documents_size', {}).get('size_gb'))} GB |

五、内存与 swap

| 指标 | 明文值 |
|---|---|
| 物理内存 | {val(mem.get('physical_memory_gb'))} GB |
| 当前 swap 使用量 | {val(mem.get('swap_used_gb'))} GB |
| 黄色预警线 | swap ≥ {config['swap_yellow_gb']} GB |
| 红色预警线 | swap ≥ {config['swap_red_gb']} GB |
| 当前内存风险等级 | {val(risk.get('swap_level'))} |
| vm_stat 摘要 | {val(mem.get('vm_stat_summary'))} |

六、进程负载摘要

Top CPU 进程原文摘要，尽量只包含进程名称，不采集命令行参数：

```text
{val(metrics.get('top_processes', {}).get('top_cpu_raw'))}
```

Top 内存进程原文摘要，尽量只包含进程名称，不采集命令行参数：

```text
{val(metrics.get('top_processes', {}).get('top_memory_raw'))}
```
{remote_block}
八、Git 与仓库状态

| 指标 | 明文值 |
|---|---|
| 仓库根目录 | {val(git.get('repo_root'))} |
| 当前分支 | {val(git.get('branch'))} |
| 最新提交 | {val(git.get('latest_commit'))} |
| 仓库已跟踪 dirty 数量 | {val(git.get('tracked_dirty_count_repo'))} |
| 本设备 macdata dirty 数量 | {val(git.get('device_dirty_count'))} |
| 本设备 macdata 未跟踪数量 | {val(git.get('device_untracked_count'))} |

九、收益与 ROI 明文分析

{roi_lines}

十、优势、劣势、机会、威胁

| 类型 | 内容 | 对收益的影响 | 风险 |
|---|---|---|---|
{swot_rows}

十一、本机三天保留与清理结果

| 项目 | 明文值 |
|---|---|
| 保留天数 | {val(cleanup_status.get('retention_days'))} |
| 保留起始日期 | {val(cleanup_status.get('cutoff_date_kept_from'))} |
| 删除旧目录数量 | {val(cleanup_status.get('deleted_dirs'))} |
| 删除旧文件数量 | {val(cleanup_status.get('deleted_files'))} |
| 释放空间 | {val(cleanup_status.get('freed_mb'))} MB |
| 清理说明 | {val(cleanup_status.get('message', cleanup_status.get('status')))} |
| Docker 清理状态 | {val(docker_cleanup.get('status'))} |
| Docker 清理命令 | {val(docker_cleanup.get('command'))} |
| Homebrew 清理状态 | {val(homebrew_cleanup.get('status'))} |
| Homebrew 清理命令 | {val(homebrew_cleanup.get('command'))} |
| 系统缓存清理状态 | {val(system_cleanup.get('status'))} |
| 系统缓存清理命令 | {val(system_cleanup.get('command'))} |
| 项目缓存候选数量 | {val(project_cleanup.get('candidate_count'))} |
| 项目缓存释放空间 | {val(project_cleanup.get('freed_mb'))} MB |

十二、缺失项与失败项

| 字段 | 状态 | 原因 |
|---|---|---|
| Time Machine | 未采集 | 用户明确要求暂不采集 |
| iCloud | 未采集 | 用户明确不要 iCloud |
| API key / token / password | 未采集 | 凭证类数据禁止进入 GitHub |
| Docker/Homebrew/系统缓存/项目缓存 | {val(development_cleanup.get('status', '待清理'))} | 仅在远程上传验证成功后执行；Docker 不清 volumes、不使用 -a，除非配置显式打开 |

十三、下一次检查重点

- 观察存储剩余空间是否越过黄色或红色预警线。
- 观察 swap 是否持续升高。
- 观察电池最大容量和循环次数变化。
- 观察 GitHub 上传验证是否连续成功。
- 观察本机是否严格只保留最近三天 macdata 数据和记录。
"""
    return report


def roi_text(metrics: Dict[str, Any], config: Dict[str, Any]) -> str:
    risk = metrics.get('risk', {})
    storage = risk.get('storage_level')
    swap = risk.get('swap_level')
    battery = risk.get('battery_capacity_level')
    if config['device_key'].lower().startswith('pro'):
        return f"""| 判断项 | 结论 | 明文依据 |
|---|---|---|
| 是否继续做主开发机 | {'是' if storage != '红色' and swap != '红色' else '需要降载或处理'} | 存储风险：{storage}；内存风险：{swap}；电池风险：{battery} |
| 是否需要马上换机 | 否，除非连续出现红色风险或明显开发等待损耗 | 本报告优先触发清理、上云或换电池，不以新机发布作为换机依据 |
| 是否需要换电池 | {'是或尽快评估' if battery == '红色' else '暂不需要，继续观察'} | 电池最大容量风险等级：{battery} |
| 是否需要清理存储 | {'是' if storage in ('黄色','红色') else '暂不需要'} | Pro 黄色线 {config['storage_yellow_free_gb']}GB，红色线 {config['storage_red_free_gb']}GB |
| 是否需要把任务转到 Codespaces | {'建议考虑' if swap in ('黄色','红色') or storage in ('黄色','红色') else '暂不需要'} | 当本地 swap 或存储压力升高时，云端算力可保护 Pro 寿命和体验 |
| 本日 ROI 状态 | {'高' if risk.get('overall_level') == '绿色' else '中/需处理'} | 设备仍作为生产资产；风险等级越高，维护优先级越高 |"""
    return f"""| 判断项 | 结论 | 明文依据 |
|---|---|---|
| 是否继续做工作前台 | {'是' if storage != '红色' and swap != '红色' else '需要降载或清理'} | 存储风险：{storage}；内存风险：{swap}；电池风险：{battery} |
| 是否适合本地开发 | 否，仅轻量任务 | Air M2 8GB/256GB 应定位为工作前台、移动终端和云端入口 |
| 是否需要马上换 Air | 否，除非连续红色风险或工作体验明显受损 | 优先降负载、清理、远程 Pro 或 Codespaces |
| 是否需要换电池 | {'是或尽快评估' if battery == '红色' else '暂不需要，继续观察'} | 电池最大容量风险等级：{battery} |
| 是否需要清理存储 | {'是' if storage in ('黄色','红色') else '暂不需要'} | Air 黄色线 {config['storage_yellow_free_gb']}GB，红色线 {config['storage_red_free_gb']}GB |
| 是否需要更多使用 Pro/Codespaces | {'是' if swap in ('黄色','红色') or storage in ('黄色','红色') else '按需使用'} | Air 的 ROI 来自移动入口，不来自本地重负载 |
| 本日 ROI 状态 | {'高' if risk.get('overall_level') == '绿色' else '中/需处理'} | 轻量化越彻底，Air 使用寿命和移动收益越高 |"""


def swot_rows_for(config: Dict[str, Any], metrics: Dict[str, Any]) -> str:
    if config['device_key'].lower().startswith('pro'):
        rows = [
            ('优势', 'Pro M2 具备较强 CPU/GPU、32GB 内存和接近 1TB 存储，适合主开发。', '能承担 Codex、测试、构建、交付和项目沉淀。', '如果 Docker、依赖和构建产物膨胀，会侵蚀优势。'),
            ('劣势', '主开发机最容易积累缓存、依赖、日志和构建产物。', '维护成本会上升。', '长期不处理会导致等待时间增加和 ROI 下降。'),
            ('机会', '每日明文指标可让 agent 判断清理、换电池、上云、换机时机。', '减少主观焦虑和过早换机。', '指标字段不足会让判断偏保守。'),
            ('威胁', '电池老化、存储压力、swap 和开发膨胀同时出现。', '可能影响开发连续性。', '必须依赖上传验证和受控清理机制兜底。'),
        ]
    else:
        rows = [
            ('优势', 'Air M2 轻便、低功耗、适合移动办公和远程入口。', '提升会议、资料整理、Notion、远程连接效率。', '如果误用为主开发机会迅速降低体验。'),
            ('劣势', '8GB 内存和 256GB 存储限制明显。', '多任务、浏览器和会议软件容易导致 swap。', '存储低于黄色线后体验会明显下降。'),
            ('机会', '把 Air 固定为 Pro/Codespaces 入口。', '延长 Air 寿命，减少换机支出。', '需要先建立远程工作流。'),
            ('威胁', '本地缓存、下载目录、浏览器标签和会议软件膨胀。', '可能让 Air 提前进入低体验状态。', '需要每日监控和三天保留约束。'),
        ]
    return '\n'.join(f'| {a} | {b} | {c} | {d} |' for a, b, c, d in rows)


def copytree_contents(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def archive_to_github(repo_root: Path, config: Dict[str, Any], stage: str, message_suffix: str, files_for_secret_scan: List[Path]) -> Dict[str, Any]:
    ok, findings = scan_for_secrets(files_for_secret_scan)
    if not ok:
        return {'ok': False, 'status': '凭证扫描失败', 'message': '检测到疑似 API key/token/password/secret，已停止上传。', 'findings': findings}

    branch = config['default_archive_branch']
    remote = config['default_remote']
    device_rel = config['local_relative_dir']
    origin = cmd(['git', '-C', str(repo_root), 'remote', 'get-url', remote], timeout=10)
    if not origin['ok'] or not origin['stdout']:
        return {'ok': False, 'status': '上传失败', 'message': f'无法读取 git remote {remote}: {origin.get("stderr") or origin.get("stdout")}' }
    origin_url = origin['stdout']
    tmp_parent = DEVICE_ROOT / 'data' / 'cache' / 'archive_push'
    tmp_parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f'{config["device_key"]}-{stage}-', dir=str(tmp_parent)))
    work = tmp / 'repo'
    try:
        branch_exists = cmd(['git', 'ls-remote', '--exit-code', '--heads', origin_url, branch], timeout=30)
        if branch_exists['ok']:
            clone = cmd(['git', 'clone', '--depth', '1', '--single-branch', '--branch', branch, origin_url, str(work)], timeout=120)
            if not clone['ok']:
                return {'ok': False, 'status': '上传失败', 'message': f'临时浅克隆失败：{clone.get("stderr") or clone.get("stdout")}' }
        else:
            work.mkdir(parents=True, exist_ok=True)
            init = cmd(['git', 'init'], cwd=work, timeout=20)
            checkout = cmd(['git', 'checkout', '-B', branch], cwd=work, timeout=20)
            remote_add = cmd(['git', 'remote', 'add', 'origin', origin_url], cwd=work, timeout=20)
            if not (init['ok'] and checkout['ok'] and remote_add['ok']):
                return {'ok': False, 'status': '上传失败', 'message': '初始化临时归档分支失败'}

        dest_device_root = work / device_rel
        dest_device_root.mkdir(parents=True, exist_ok=True)
        # Copy only live data/report/latest directories, not scripts/docs, to keep archive branch lightweight.
        copy_items = [
            ('data/current_3days', 'data/current_3days'),
            ('data/latest', 'data/latest'),
            ('reports/current_3days', 'reports/current_3days'),
            ('reports/latest', 'reports/latest'),
        ]
        for src_rel, dst_rel in copy_items:
            src = DEVICE_ROOT / src_rel
            dst = dest_device_root / dst_rel
            if dst.exists():
                shutil.rmtree(dst)
            if src.exists():
                shutil.copytree(src, dst)
        # Apply retention to archive branch current tree. Older data remains available through GitHub history.
        cleanup_retention([
            dest_device_root / 'data' / 'current_3days' / 'raw',
            dest_device_root / 'reports' / 'current_3days',
        ], int(config['retention_days']), dry_run=False)
        receipt_dir = dest_device_root / 'reports' / 'current_3days' / date_dir()
        receipt_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = receipt_dir / f'{stage}_archive_receipt_{_dt.datetime.now().strftime("%H%M%S")}.json'
        write_json(receipt_path, {
            'device_key': config['device_key'],
            'stage': stage,
            'created_at_local': now_local_iso(),
            'message_suffix': message_suffix,
            'retention_note': '归档分支当前树只保留最近三天；更早数据通过 GitHub 提交历史保留。',
        })
        scan_ok, scan_findings = scan_for_secrets([p for p in dest_device_root.rglob('*') if p.is_file()])
        if not scan_ok:
            return {'ok': False, 'status': '凭证扫描失败', 'message': '归档工作区命中凭证类高风险模式，停止提交。', 'findings': scan_findings}
        add = cmd(['git', 'add', device_rel], cwd=work, timeout=60)
        if not add['ok']:
            return {'ok': False, 'status': '上传失败', 'message': f'git add 失败：{add.get("stderr")}' }
        status = cmd(['git', 'status', '--porcelain=v1'], cwd=work, timeout=20)
        if not status['stdout'].strip():
            # Force a heartbeat to satisfy every-run commit requirement.
            heartbeat = dest_device_root / 'reports' / 'latest' / f'{stage}_heartbeat.txt'
            write_text(heartbeat, f'{now_local_iso()} {stage} heartbeat\n')
            cmd(['git', 'add', device_rel], cwd=work, timeout=20)
        commit_message = f'data(macdata-{config["device_key"]}): {date_dir()} {stage} {message_suffix}'
        commit = cmd(['git', 'commit', '-m', commit_message], cwd=work, timeout=60)
        if not commit['ok']:
            return {'ok': False, 'status': '上传失败', 'message': f'git commit 失败：{commit.get("stderr") or commit.get("stdout")}' }
        local_hash = cmd(['git', 'rev-parse', 'HEAD'], cwd=work, timeout=10)
        push = cmd(['git', 'push', 'origin', f'HEAD:{branch}'], cwd=work, timeout=120)
        if not push['ok']:
            return {'ok': False, 'status': '上传失败', 'message': f'git push 失败：{push.get("stderr") or push.get("stdout")}', 'local_commit_hash': local_hash.get('stdout')}
        remote_hash_res = cmd(['git', 'ls-remote', origin_url, f'refs/heads/{branch}'], timeout=30)
        remote_hash = (remote_hash_res.get('stdout') or '').split('\t')[0] if remote_hash_res.get('stdout') else ''
        verified = bool(local_hash.get('stdout')) and remote_hash == local_hash.get('stdout')
        return {
            'ok': verified,
            'status': '上传成功并已验证' if verified else '上传后验证失败',
            'message': '远程分支提交哈希与本地提交哈希一致。' if verified else '远程分支提交哈希与本地提交哈希不一致。',
            'archive_branch': branch,
            'local_commit_hash': local_hash.get('stdout'),
            'remote_commit_hash': remote_hash,
            'remote_verified': verified,
            'commit_message': commit_message,
        }
    finally:
        # Always remove temporary clone to keep the local machine light.
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass


def build_run_status(
    config: Dict[str, Any],
    rid: str,
    raw_data_path: str,
    final_report_path: str,
    data_archive: Dict[str, Any],
    cleanup_status: Dict[str, Any],
    report_archive: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    raw_verified = bool(data_archive.get('remote_verified'))
    report_verified = bool(report_archive.get('remote_verified')) if report_archive is not None else None
    ok = (raw_verified and report_verified) if report_archive is not None else None
    return {
        'ok': ok,
        'device_key': config['device_key'],
        'run_id': rid,
        'archive_branch': data_archive.get('archive_branch') or config['default_archive_branch'],
        'remote_verified': ok,
        'raw_data_path': raw_data_path,
        'final_report_path': final_report_path,
        'raw_archive': data_archive,
        'report_archive': report_archive,
        'cleanup': cleanup_status,
        'development_cleanup': cleanup_status.get('development_cleanup'),
        'created_at_local': now_local_iso(),
    }


def controlled_cycle(repo_root: Path, execute: bool) -> int:
    config = load_json(CONFIG_PATH)
    if not execute:
        print('未传入 --execute，本脚本不会执行采集、上传或清理。')
        print('这是设计要求：脚本只作为 Codex Automation 的受控工具，不允许自动运行。')
        return 0
    owner = require_owner_confirmations(config)
    pre_ok, pre_messages, pre_hw = preflight_device(config, owner)
    if not pre_ok:
        print('设备预检失败。Codex 必须把以下问题明确问用户，得到确认后才可继续：')
        for m in pre_messages:
            print(f'- {m}')
        return 20
    rid = run_id(config['device_key'])
    metrics = collect_metrics(repo_root, config, rid)
    metrics['preflight_messages'] = pre_messages
    metrics['owner_confirmations_summary'] = {
        'confirmed_device_key': owner.get('confirmed_device_key'),
        'confirmed_at': owner.get('confirmed_at'),
        'allow_plaintext_device_metrics_to_github': owner.get('allow_plaintext_device_metrics_to_github'),
        'allow_github_upload': owner.get('allow_github_upload'),
    }
    current_date = date_dir()
    raw_path = DEVICE_ROOT / 'data' / 'current_3days' / 'raw' / current_date / f'{rid}.json'
    latest_raw = DEVICE_ROOT / 'data' / 'latest' / 'latest_metrics.json'
    draft_report_path = DEVICE_ROOT / 'reports' / 'current_3days' / current_date / f'{rid}_draft.md'
    latest_report = DEVICE_ROOT / 'reports' / 'latest' / 'latest_report.md'
    write_json(raw_path, metrics)
    write_json(latest_raw, metrics)
    draft_report = render_cn_report(metrics, config)
    write_text(draft_report_path, draft_report)
    write_text(latest_report, draft_report)
    scan_ok, scan_findings = scan_for_secrets([raw_path, latest_raw, draft_report_path, latest_report])
    if not scan_ok:
        print('凭证扫描失败，已停止上传。')
        for f in scan_findings:
            print(f'- {f}')
        return 30

    data_archive = archive_to_github(repo_root, config, 'raw', rid, [raw_path, latest_raw, draft_report_path, latest_report])
    if not data_archive.get('ok'):
        failure_report = render_cn_report(metrics, config, upload_status={
            'status': data_archive.get('status', '上传失败'),
            'message': data_archive.get('message', '未知失败'),
            'archive_branch': config['default_archive_branch'],
            'remote_verified': False,
        }, cleanup_status={'status': '未清理', 'message': '由于上传未验证成功，本机旧数据未删除。'})
        write_text(latest_report, failure_report)
        print(failure_report)
        return 40

    cleanup_status = cleanup_retention([
        DEVICE_ROOT / 'data' / 'current_3days' / 'raw',
        DEVICE_ROOT / 'reports' / 'current_3days',
        DEVICE_ROOT / 'data' / 'run_logs',
    ], int(config['retention_days']), dry_run=False)
    cleanup_cache_status = cleanup_cache()
    cleanup_status['cache_cleanup'] = cleanup_cache_status
    cleanup_status['development_cleanup'] = cleanup_development_environment(repo_root, config, dry_run=False)
    cleanup_status['status'] = '已在 raw 数据上传验证成功后清理本机旧数据、macdata 临时缓存和受控开发环境缓存'

    final_upload = {
        'status': data_archive.get('status'),
        'message': data_archive.get('message'),
        'archive_branch': data_archive.get('archive_branch'),
        'data_commit_hash': data_archive.get('local_commit_hash'),
        'remote_verified': data_archive.get('remote_verified'),
    }
    final_report = render_cn_report(metrics, config, upload_status=final_upload, cleanup_status=cleanup_status)
    final_report_path = DEVICE_ROOT / 'reports' / 'current_3days' / current_date / f'{rid}_final.md'
    write_text(final_report_path, final_report)
    write_text(latest_report, final_report)
    final_status_path = DEVICE_ROOT / 'data' / 'latest' / 'last_run_status.json'
    raw_rel = str(raw_path.relative_to(DEVICE_ROOT))
    final_report_rel = str(final_report_path.relative_to(DEVICE_ROOT))
    write_json(final_status_path, build_run_status(config, rid, raw_rel, final_report_rel, data_archive, cleanup_status))
    report_archive = archive_to_github(repo_root, config, 'report', rid, [final_report_path, latest_report, final_status_path])
    write_json(final_status_path, build_run_status(config, rid, raw_rel, final_report_rel, data_archive, cleanup_status, report_archive))
    console_upload = dict(final_upload)
    console_upload['report_commit_hash'] = report_archive.get('local_commit_hash')
    console_upload['remote_verified'] = bool(data_archive.get('remote_verified')) and bool(report_archive.get('remote_verified'))
    console_upload['status'] = '全部上传成功并已验证' if console_upload['remote_verified'] else '报告上传验证失败'
    console_upload['message'] = report_archive.get('message', '')
    console_report = render_cn_report(metrics, config, upload_status=console_upload, cleanup_status=cleanup_status)
    print(console_report)
    if not report_archive.get('ok'):
        print('报告归档失败：', report_archive)
        return 50
    return 0


def write_owner_template_if_requested() -> None:
    config = load_json(CONFIG_PATH)
    out = DEVICE_ROOT / 'config' / 'owner_confirmations.example.generated.json'
    write_json(out, {
        'confirmed_device_key': config['device_key'],
        'confirmed_at': '<由 Codex 根据用户答复填写 ISO 时间>',
        'run_full_cycle_confirmed': True,
        'allow_plaintext_device_metrics_to_github': True,
        'allow_github_upload': True,
        'allow_delete_local_macdata_older_than_3_days_after_verified_upload': True,
        'allow_development_cache_cleanup_after_verified_upload': True,
        'understand_no_timemachine_no_icloud': True,
        'understand_scripts_do_not_auto_schedule': True,
        'repo_remote_name': config['default_remote'],
        'archive_branch': config['default_archive_branch'],
        'notes_cn': '该文件不是凭证。不要在这里填写 API key、token、password。'
    })
    print(f'已生成：{out}')


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='macdata controlled Codex Automation script')
    parser.add_argument('--repo-root', default='.', help='CodexProject 仓库根目录')
    parser.add_argument('--execute', action='store_true', help='明确执行完整采集、上传、验证、清理流程；不传则只输出说明')
    parser.add_argument('--preflight-only', action='store_true', help='只做设备预检，不写数据、不上传、不清理')
    parser.add_argument('--write-owner-template', action='store_true', help='生成 owner_confirmations 示例，不执行采集')
    args = parser.parse_args(argv)
    config = load_json(CONFIG_PATH)
    repo_root = Path(args.repo_root).expanduser().resolve()
    if args.write_owner_template:
        write_owner_template_if_requested()
        return 0
    if args.preflight_only:
        owner = load_json(OWNER_CONFIRMATIONS_PATH) if OWNER_CONFIRMATIONS_PATH.exists() else None
        ok, messages, hardware = preflight_device(config, owner)
        print(json.dumps({'ok': ok, 'messages': messages, 'hardware': hardware}, ensure_ascii=False, indent=2))
        return 0 if ok else 20
    return controlled_cycle(repo_root, args.execute)


if __name__ == '__main__':
    raise SystemExit(main())
