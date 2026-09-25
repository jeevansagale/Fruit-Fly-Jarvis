#!/usr/bin/env python3
"""FF-02C target-machine validation harness.

Diagnostics only. No uploads, no telemetry, no asset modification.
Missing dependencies degrade to BLOCKED/UNKNOWN, never crash.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

STATUSES = {"PASS", "FAIL", "PENDING", "UNKNOWN", "BLOCKED", "SKIPPED"}

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "artifacts" / "ff02c"
LOCAL_ASSETS = REPO_ROOT / "characters" / "local"
THREEJS_PROBE_DIR = REPO_ROOT / "apps" / "avatar-renderer" / "probes" / "ff02"
GODOT_PROBE_DIR = REPO_ROOT / "apps" / "avatar-renderer" / "probes" / "godot-ff02"
OVERLAY_DIR = REPO_ROOT / "apps" / "overlay-linux"

RELEVANT_EXTS = {
    ".fbx", ".obj", ".gltf", ".glb", ".vrm", ".vrma", ".blend",
    ".png", ".jpg", ".jpeg", ".webp", ".tga", ".bmp", ".dds", ".ktx2",
}
TEXTURE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tga", ".bmp", ".dds", ".ktx2"}

EYE_HINTS = ("eye", "eyel", "eyer", "eye_l", "eye_r", "l_eye", "r_eye")
HEAD_HINTS = ("head", "neck")


def check_status(value: str) -> str:
    if value not in STATUSES:
        raise ValueError(f"invalid status: {value!r}")
    return value


def _home() -> str:
    try:
        return str(Path.home())
    except Exception:
        return os.path.expanduser("~")


def _user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return ""


def _host() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return ""


SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)(['\"]?)([A-Za-z0-9_\-./+]{8,})\2"),
    re.compile(r"(?i)(secret\s*[:=]\s*)(['\"]?)([A-Za-z0-9_\-./+]{8,})\2"),
    re.compile(r"(?i)(bearer\s+)([A-Za-z0-9_\-./+=]{8,})"),
    re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
    re.compile(r"\b(ghp_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,})\b"),
    re.compile(r"(?i)(password\s*[:=]\s*)(['\"]?)([^\s'\"]{4,})\2"),
]


def sanitize_text(text: str) -> str:
    out = text
    home = _home()
    if home and home != "~" and home in out:
        out = out.replace(home, "$HOME")
    user = _user()
    if user and user not in ("", "root"):
        out = re.sub(rf"(?<![A-Za-z0-9_\-]){re.escape(user)}(?![A-Za-z0-9_\-])", "$USER", out)
    host = _host()
    if host:
        out = out.replace(host, "$HOST")
    for pat in SECRET_PATTERNS:
        out = pat.sub(lambda m: (m.group(1) if m.lastindex and m.lastindex >= 1 and "BEGIN" not in m.group(0) else "") + "[REDACTED]" if m.lastindex else "[REDACTED]", out)
    # Collapse any remaining absolute home-like paths to $HOME prefix.
    out = re.sub(r"/home/[A-Za-z0-9_\-]+", "$HOME", out)
    out = re.sub(r"/Users/[A-Za-z0-9_\-]+", "$HOME", out)
    return out


def sanitize_obj(obj):
    if isinstance(obj, str):
        return sanitize_text(obj)
    if isinstance(obj, list):
        return [sanitize_obj(v) for v in obj]
    if isinstance(obj, dict):
        return {k: sanitize_obj(v) for k, v in obj.items()}
    return obj


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(argv: list[str], timeout: int = 10) -> dict:
    """Never raise on missing commands. Returns structured unavailable result."""
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        out = (proc.stdout or "")[:4000]
        err = (proc.stderr or "")[:4000]
        return {
            "available": True,
            "argv": argv,
            "exit_code": proc.returncode,
            "stdout": sanitize_text(out.strip()),
            "stderr": sanitize_text(err.strip()),
        }
    except FileNotFoundError:
        return {"available": False, "argv": argv, "exit_code": None, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired:
        return {"available": False, "argv": argv, "exit_code": None, "stdout": "", "stderr": "timed out"}
    except Exception as exc:  # noqa: BLE001 - harness must not crash
        return {"available": False, "argv": argv, "exit_code": None, "stdout": "", "stderr": f"unavailable: {exc}"}


def collect_environment() -> dict:
    cmds = {
        "uname": ["uname", "-a"],
        "os_release": ["cat", "/etc/os-release"],
        "hyprctl": ["hyprctl", "version"],
        "nvidia_smi": ["nvidia-smi"],
        "vulkaninfo": ["vulkaninfo", "--summary"],
        "gtk4": ["pkg-config", "--modversion", "gtk4"],
        "gtk4_layer_shell": ["pkg-config", "--modversion", "gtk4-layer-shell"],
        "rustc": ["rustc", "--version"],
        "cargo": ["cargo", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "chromium": ["chromium", "--version"],
        "godot": ["godot", "--version"],
        "python3": ["python3", "--version"],
    }
    results = {k: run_cmd(v) for k, v in cmds.items()}
    # Chromium fallbacks (do not treat as separate requirements).
    if not results["chromium"]["available"]:
        for alt in (["google-chrome", "--version"], ["chromium-browser", "--version"]):
            r = run_cmd(alt)
            if r["available"]:
                results["chromium"] = r
                break
    env_vars = {}
    for key in ("WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "XDG_CURRENT_SESSION"):
        val = os.environ.get(key, "")
        env_vars[key] = sanitize_text(val) if val else "(unset)"
    return {"commands": results, "session_env": env_vars}


def collect_assets() -> dict:
    started = time.time()
    if not LOCAL_ASSETS.exists():
        return {
            "status": check_status("BLOCKED"),
            "reason": "characters/local does not exist; place licensed assets locally per runbook.",
            "asset_count": 0,
            "assets": [],
            "elapsed_s": round(time.time() - started, 3),
        }
    files = sorted(
        (p for p in LOCAL_ASSETS.rglob("*") if p.is_file() and p.suffix.lower() in RELEVANT_EXTS),
        key=lambda p: p.relative_to(LOCAL_ASSETS).as_posix(),
    )
    assets = []
    for p in files:
        try:
            rel = p.relative_to(LOCAL_ASSETS).as_posix()
            assets.append({
                "filename": p.name,
                "relative_path": sanitize_text(rel),
                "extension": p.suffix.lower(),
                "size_bytes": p.stat().st_size,
                "sha256": sha256_file(p),
            })
        except Exception as exc:  # noqa: BLE001
            assets.append({
                "filename": p.name,
                "relative_path": sanitize_text(p.relative_to(LOCAL_ASSETS).as_posix()),
                "extension": p.suffix.lower(),
                "size_bytes": -1,
                "sha256": f"UNREADABLE: {exc}",
            })
    status = "UNKNOWN" if not assets else "PASS"
    # Asset discovery PASS means "inventory ran"; it is not renderer acceptance.
    return {
        "status": check_status(status),
        "reason": "inventory ran; capability fields remain UNKNOWN until importer probes run" if assets else "no relevant assets found under characters/local",
        "asset_count": len(assets),
        "assets": assets,
        "elapsed_s": round(time.time() - started, 3),
    }


def collect_threejs(env: dict) -> dict:
    probe = THREEJS_PROBE_DIR / "probe.mjs"
    pkg = THREEJS_PROBE_DIR / "package.json"
    index = THREEJS_PROBE_DIR / "index.html"
    files_present = all(p.exists() for p in (probe, pkg, index))
    three_version = "unknown"
    uses_fbxloader = False
    if probe.exists():
        try:
            src = probe.read_text(encoding="utf-8", errors="replace")
            uses_fbxloader = "FBXLoader" in src
        except Exception:
            uses_fbxloader = False
    if pkg.exists():
        try:
            three_version = json.loads(pkg.read_text(encoding="utf-8")).get("dependencies", {}).get("three", "unknown")
        except Exception:
            three_version = "unknown"
    node_ok = env["commands"]["node"]["available"]
    chromium_ok = env["commands"]["chromium"]["available"]
    if not files_present:
        status = "BLOCKED"
        note = "Three.js probe files missing; cannot run browser import."
    elif not node_ok:
        status = "BLOCKED"
        note = "node unavailable; static probe files present but dependency check incomplete."
    else:
        # Browser file-picker step is manual; never PASS from existence alone.
        status = "PENDING"
        note = "Probe present. Manual browser import on target machine required; see runbook."
        if not chromium_ok:
            note += " Chromium not detected, browser step may be BLOCKED until a browser is available."
    return {
        "status": check_status(status),
        "probe_dir": "apps/avatar-renderer/probes/ff02",
        "files_present": files_present,
        "three_version": three_version,
        "uses_FBXLoader": uses_fbxloader,
        "node_available": node_ok,
        "chromium_available": chromium_ok,
        "exit_code": None,
        "model": None,
        "load_success": None,
        "parse_duration_s": None,
        "mesh_count": None,
        "skinned_mesh_count": None,
        "bone_count": None,
        "material_count": None,
        "texture_count": None,
        "animation_clip_count": None,
        "animation_names": [],
        "morph_info": "UNKNOWN - probe not executed in harness",
        "eye_head_candidates": "UNKNOWN - probe not executed in harness",
        "render_calls": None,
        "errors": [],
        "warnings": [note],
        "note": "Three.js FBXLoader results are importer evidence, not proof of source-file contents. 0 clips alone never means NO ANIMATION.",
    }


def collect_godot(env: dict) -> dict:
    probe = GODOT_PROBE_DIR / "probe.gd"
    project = GODOT_PROBE_DIR / "project.godot"
    files_present = probe.exists() and project.exists()
    godot_cmd = env["commands"]["godot"]
    godot_version = godot_cmd["stdout"] if godot_cmd["available"] else "unavailable"
    if not files_present:
        return {"status": check_status("BLOCKED"), "reason": "Godot probe files missing.",
                "godot_version": godot_version, "exit_code": None, "stdout": "", "stderr": "",
                "results": []}
    if not godot_cmd["available"]:
        return {"status": check_status("BLOCKED"), "reason": "godot executable unavailable; not auto-installing SDK.",
                "godot_version": godot_version, "exit_code": None, "stdout": "", "stderr": "",
                "results": []}
    local_dir = GODOT_PROBE_DIR / "local"
    staged = sorted(local_dir.glob("*.fbx")) if local_dir.exists() else []
    if not staged:
        return {"status": check_status("PENDING"),
                "reason": "Godot available but no FBX staged under ignored probes/godot-ff02/local/. Copy per runbook, then re-run.",
                "godot_version": godot_version, "exit_code": None, "stdout": "", "stderr": "", "results": []}
    # Run import once, then probe each staged FBX. Bounded timeouts; failures -> UNKNOWN, not crash.
    results = []
    import_res = run_cmd(["godot", "--headless", "--path", str(GODOT_PROBE_DIR), "--import"], timeout=120)
    for fbx in staged[:4]:
        res_name = f"res://local/{fbx.name}"
        r = run_cmd(["godot", "--headless", "--path", str(GODOT_PROBE_DIR),
                     "--script", "res://probe.gd", "--", res_name], timeout=120)
        parsed = None
        for line in (r["stdout"] or "").splitlines():
            if line.startswith("FF02_RESULT "):
                try:
                    parsed = json.loads(line[len("FF02_RESULT "):])
                except Exception:
                    parsed = {"parse_error": "FF02_RESULT was not valid JSON"}
                break
        results.append({"asset": res_name, "exit_code": r["exit_code"], "parsed": parsed,
                        "stdout_tail": (r["stdout"] or "")[-2000:], "stderr_tail": (r["stderr"] or "")[-2000:]})
    ok = any(r.get("parsed") for r in results)
    return {"status": check_status("PASS" if ok else "UNKNOWN"),
            "reason": "probe executed on staged local copies" if ok else "probe ran but produced no parseable FF02_RESULT",
            "godot_version": godot_version, "import_exit_code": import_res["exit_code"],
            "import_stderr_tail": (import_res["stderr"] or "")[-2000:],
            "exit_code": None, "stdout": "", "stderr": "", "results": results}


def _extract_texture_refs(fbx_path: Path) -> list[str]:
    try:
        data = fbx_path.read_bytes()
    except Exception:
        return []
    # Printable ASCII substrings; FBX binary embeds texture paths as text.
    parts = re.findall(rb"[\x20-\x7e]{4,}", data)
    refs: set[str] = set()
    for p in parts:
        try:
            s = p.decode("ascii")
        except Exception:
            continue
        low = s.lower()
        for ext in TEXTURE_EXTS:
            if low.endswith(ext) and len(s) < 512:
                base = s.replace("\\", "/").split("/")[-1].strip().strip("\"'")
                if base and len(base) < 256:
                    refs.add(base)
    return sorted(refs)


def collect_textures(assets: dict) -> dict:
    if assets.get("status") == "BLOCKED":
        return {"status": check_status("BLOCKED"), "reason": "asset directory unavailable", "entries": []}
    if not LOCAL_ASSETS.exists():
        return {"status": check_status("BLOCKED"), "reason": "asset directory unavailable", "entries": []}
    tex_files = [p for p in LOCAL_ASSETS.rglob("*") if p.is_file() and p.suffix.lower() in TEXTURE_EXTS]
    by_exact = {p.name for p in tex_files}
    by_lower = {}
    for p in tex_files:
        by_lower.setdefault(p.name.lower(), []).append(p.relative_to(LOCAL_ASSETS).as_posix())
    fbx_files = [p for p in LOCAL_ASSETS.rglob("*") if p.is_file() and p.suffix.lower() == ".fbx"]
    if not fbx_files:
        return {"status": check_status("UNKNOWN"), "reason": "no FBX files to extract texture references from", "entries": []}
    entries = []
    for fbx in sorted(fbx_files):
        rel = fbx.relative_to(LOCAL_ASSETS).as_posix()
        for req in _extract_texture_refs(fbx):
            exact = req in by_exact
            ci_paths = by_lower.get(req.lower(), [])
            ci = bool(ci_paths) and not exact
            missing = not exact and not ci_paths
            stem = Path(req).stem.lower()
            cands = sorted({q for low, paths in by_lower.items() for q in paths if stem and stem in low})[:8]
            entries.append({
                "source_fbx": sanitize_text(rel),
                "requested_name": req,
                "exact_match": exact,
                "case_insensitive_match": bool(ci_paths),
                "missing": missing,
                "candidate_matches": [sanitize_text(c) for c in cands],
            })
    if not entries:
        return {"status": check_status("UNKNOWN"),
                "reason": "no texture-path strings extracted from FBX binaries with this heuristic; texture state UNKNOWN, verify in importer probes",
                "entries": []}
    unresolved = sum(1 for e in entries if e["missing"])
    status = "FAIL" if unresolved else "PASS"
    return {"status": check_status(status),
            "reason": f"{unresolved} of {len(entries)} texture references unresolved by filename match; verify visually in probes",
            "entries": entries,
            "method": "binary string extraction + filename match only; not a render check"}


def _candidates(names: list[str]) -> dict:
    low = [(n, n.lower()) for n in names]
    return {
        "eye": sorted(n for n, l in low if any(h in l for h in EYE_HINTS)),
        "head": sorted(n for n, l in low if any(h in l for h in HEAD_HINTS)),
    }


def collect_animation_structure(three: dict, godot: dict) -> dict:
    clips: list[dict] = []
    bone_names: list[str] = []
    morph_names: list[str] = []
    sources = []
    for r in godot.get("results", []):
        parsed = r.get("parsed") or {}
        for c in parsed.get("imported_clips", []) or []:
            clips.append({"source": "godot", "name": c.get("name"), "duration_s": c.get("duration_s")})
        for sk in parsed.get("imported_skeletons", []) or []:
            bone_names.extend(sk.get("bone_names", []) or [])
        morph_names.extend(parsed.get("imported_morph_names", []) or [])
        if parsed:
            sources.append("godot")
    three_clips = three.get("animation_clip_count")
    if isinstance(three_clips, int) and three_clips > 0:
        clips.extend({"source": "threejs", "name": n} for n in three.get("animation_names", []))
        sources.append("threejs")
    godot_tested = bool(sources)
    three_reports_zero = three_clips == 0
    if clips:
        status, reason = "PASS", f"{len(clips)} clip(s) reported by: {', '.join(sorted(set(sources)))}"
    elif godot_tested and three_reports_zero:
        status, reason = "UNKNOWN", "probes executed but report no clips; source contents still UNKNOWN without independent asset evidence"
    elif three_reports_zero and not godot_tested:
        # Required vocabulary guard: 0 from one importer + untested other != NO ANIMATION.
        status, reason = "UNKNOWN", "Three.js reports 0 clips and Godot not tested: animation status UNKNOWN, not NO ANIMATION"
    else:
        status, reason = "UNKNOWN", "no executed probe has reported animation evidence yet"
    uniq_bones = sorted(set(bone_names))
    uniq_morphs = sorted(set(morph_names))
    return {
        "status": check_status(status),
        "reason": reason,
        "threejs_clips": three_clips,
        "godot_tested": godot_tested,
        "clips": clips,
        "skeleton_present": True if uniq_bones else None,
        "bone_count": len(uniq_bones) if uniq_bones else None,
        "bone_names": uniq_bones[:500],
        "candidates": _candidates(uniq_bones) if uniq_bones else {"eye": [], "head": []},
        "morph_target_count": len(uniq_morphs) if uniq_morphs else None,
        "blend_shape_names": uniq_morphs[:500],
        "skinned_mesh_count": None,
        "note": "Counts are importer observations only. Disagreements between importers must be recorded, never resolved by picking a winner.",
    }


def collect_performance(env: dict, asset_elapsed_s: float) -> dict:
    nvidia = env["commands"]["nvidia_smi"]
    return {
        "status": check_status("UNKNOWN"),
        "reason": "sanity snapshot only; FPS/frame-time require manual target-machine measurement",
        "asset_hash_elapsed_s": asset_elapsed_s,
        "load_time_s": None,
        "frame_time_ms": None,
        "fps": None,
        "cpu_usage": None,
        "gpu_usage": "see nvidia_smi below" if nvidia["available"] else "UNKNOWN - nvidia-smi unavailable",
        "vram_usage": "see nvidia_smi below" if nvidia["available"] else "UNKNOWN - nvidia-smi unavailable",
        "nvidia_smi_available": nvidia["available"],
        "nvidia_smi_stdout_head": (nvidia["stdout"] or "")[:2000] if nvidia["available"] else "",
        "note": "Do not make renderer decisions from this snapshot.",
    }


def collect_overlay(env: dict) -> dict:
    wayland = os.environ.get("WAYLAND_DISPLAY", "")
    session = os.environ.get("XDG_SESSION_TYPE", "")
    hypr = env["commands"]["hyprctl"]
    checks = {
        "wayland_detected": bool(wayland or session.lower() == "wayland"),
        "hyprland_detected": hypr["available"] and hypr["exit_code"] == 0,
        "gtk4_available": env["commands"]["gtk4"]["available"] and env["commands"]["gtk4"]["exit_code"] == 0,
        "gtk4_layer_shell_available": env["commands"]["gtk4_layer_shell"]["available"] and env["commands"]["gtk4_layer_shell"]["exit_code"] == 0,
        "overlay_source_present": (OVERLAY_DIR / "src" / "main.rs").exists(),
        "cargo_available": env["commands"]["cargo"]["available"],
    }
    if all([checks["wayland_detected"], checks["hyprland_detected"], checks["gtk4_available"],
            checks["gtk4_layer_shell_available"], checks["overlay_source_present"]]):
        status = "PENDING"  # automated preconditions met; visual behavior still manual
        reason = "preconditions present; visual overlay behavior still requires manual target-machine test"
    elif not checks["overlay_source_present"]:
        status, reason = "BLOCKED", "overlay source missing"
    else:
        status, reason = "BLOCKED", "Wayland/Hyprland/GTK preconditions unavailable in this session"
    return {"status": check_status(status), "reason": reason, "checks": checks,
            "versions": {k: sanitize_text(str(env["commands"][k].get("stdout", ""))[:200])
                         for k in ("gtk4", "gtk4_layer_shell", "rustc", "cargo", "hyprctl")},
            "manual_checks": ["transparent background", "correct layer", "correct positioning",
                              "mouse interaction behavior", "workspace behavior", "multi-monitor behavior",
                              "overlay remains visible as intended", "no unwanted input capture", "Ctrl+C termination"],
            "ctrl_c_note": "Ctrl+C is terminal SIGINT. Super+C is a compositor shortcut. They are NOT equivalent."}


def git_commit() -> str:
    r = run_cmd(["git", "rev-parse", "--short", "HEAD"])
    return r["stdout"].strip() if r["available"] and r["exit_code"] == 0 else "unknown"


def build_report(env, assets, three, godot, textures, anim, perf, overlay) -> str:
    auto = [assets, three, godot, textures]
    overall = "PENDING"
    if any(a.get("status") == "FAIL" for a in auto):
        overall = "FAIL"
    elif all(a.get("status") == "PASS" for a in auto):
        overall = "PASS"
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    commit = sanitize_text(git_commit())
    wayland = env["session_env"]
    L = [
        "# FF-02C Target-Machine Validation",
        "",
        f"Date: {date}",
        f"Git commit: {commit}",
        f"Machine/environment summary: {sanitize_text(env['commands']['uname'].get('stdout', 'unknown')[:200])} | "
        f"session={wayland.get('XDG_SESSION_TYPE')} display={wayland.get('WAYLAND_DISPLAY')} desktop={wayland.get('XDG_CURRENT_DESKTOP')}",
        "",
        f"Overall status: {overall}",
        "",
        "## Environment",
        f"status: {overlay['status']} (visual behavior always manual)",
        f"hyprland: {'available' if env['commands']['hyprctl']['available'] else 'unavailable'} | "
        f"nvidia-smi: {'available' if env['commands']['nvidia_smi']['available'] else 'unavailable'} | "
        f"godot: {'available' if env['commands']['godot']['available'] else 'unavailable'} | "
        f"chromium: {'available' if env['commands']['chromium']['available'] else 'unavailable'}",
        "Full detail: artifacts/ff02c/environment.txt",
        "",
        "## Asset inventory",
        f"status: {assets['status']} - {assets.get('reason', '')}",
        f"assets: {assets.get('asset_count', 0)} (characters/local only, hashed in place, never uploaded)",
        "",
        "## Three.js",
        f"status: {three['status']} - {three['warnings'][0] if three.get('warnings') else ''}",
        f"probe: {three.get('probe_dir')} three={three.get('three_version')} FBXLoader={three.get('uses_FBXLoader')}",
        "",
        "## Godot",
        f"status: {godot['status']} - {godot.get('reason', '')}",
        f"version: {sanitize_text(str(godot.get('godot_version', ''))[:200])}",
        "",
        "## Texture validation",
        f"status: {textures['status']} - {textures.get('reason', '')}",
        f"entries: {len(textures.get('entries', []))} (method: {textures.get('method', 'filename match')})",
        "",
        "## Animation validation",
        f"status: {anim['status']} - {anim['reason']}",
        f"clips observed: {len(anim.get('clips', []))}",
        "",
        "## Character structure",
        f"skeleton_present: {anim.get('skeleton_present')} bone_count: {anim.get('bone_count')} "
        f"morphs: {anim.get('morph_target_count')} skinned_meshes: {anim.get('skinned_mesh_count')}",
        f"eye candidates: {anim.get('candidates', {}).get('eye', [])[:10]}",
        f"head candidates: {anim.get('candidates', {}).get('head', [])[:10]}",
        "",
        "## Performance",
        f"status: {perf['status']} - {perf['reason']}",
        f"asset_hash_elapsed_s: {perf.get('asset_hash_elapsed_s')} fps: {perf.get('fps')} frame_time_ms: {perf.get('frame_time_ms')}",
        "",
        "## FF-01 overlay",
        f"status: {overlay['status']} - {overlay['reason']}",
        f"checks: {json.dumps(overlay['checks'])}",
        "Run: ./scripts/ff01-overlay-test.sh (shows PID, never daemonizes silently)",
        "",
        "## Ctrl+C",
        "status: PENDING - manual terminal SIGINT test required (Super+C is NOT equivalent)",
        "Steps: launch overlay, note PID, press Ctrl+C, verify exit code, prompt returns, no child remains.",
        "",
        "## Automated checks",
        "- environment collection (missing commands -> unavailable, never crash)",
        "- asset discovery + SHA-256 (characters/local only)",
        "- three.js probe presence/dependency check (manual browser import still required)",
        "- godot probe execution on staged local copies only",
        "- texture filename-match report",
        "- animation/structure aggregation (0 clips from one importer != NO ANIMATION)",
        "- performance sanity snapshot",
        "- overlay precondition check",
        "",
        "## Manual checks",
        "- three.js browser import per runbook (visual pose, clips, morphs, missing textures)",
        "- godot editor visual inspection (scene, AnimationPlayer, materials)",
        "- FF-01 overlay: transparency, layer, position, mouse, workspaces, multi-monitor, input capture",
        "- Ctrl+C SIGINT termination with PID + exit code recorded",
        "- FPS/VRAM/CPU/GPU on target NVIDIA/Hyprland session",
        "",
        "## Known limitations",
        "- Texture report is filename matching over FBX-embedded strings, not a render check.",
        "- Animation absence cannot be proven by one importer reporting zero clips.",
        "- Performance section is a sanity snapshot, not a benchmark.",
        "- Visual overlay PASS requires human observation on Wayland/Hyprland; harness never fakes it.",
        "",
        "## Unresolved issues",
        "- Renderer decision: PENDING (this task does not authorize choosing Three.js or Godot)",
        "- Columbina 33-unresolved-texture claim from FF-02B is re-evaluated deterministically above; do not assume it persists.",
        "",
        "Renderer decision:",
        "PENDING",
        "",
        "Assets stay local. No asset upload is required. No telemetry is used.",
        "",
        "Status vocabulary: PASS=ran and met condition; FAIL=ran and did not; PENDING=needs target/manual evidence; "
        "UNKNOWN=insufficient evidence; BLOCKED=dependency unavailable; SKIPPED=not applicable.",
    ]
    return sanitize_text("\n".join(L) + "\n")


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize_obj(obj), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="FF-02C target-machine validation harness")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output directory")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    env = collect_environment()
    assets = collect_assets()
    three = collect_threejs(env)
    godot = collect_godot(env)
    textures = collect_textures(assets)
    anim = collect_animation_structure(three, godot)
    perf = collect_performance(env, assets.get("elapsed_s", 0.0))
    overlay = collect_overlay(env)
    report = build_report(env, assets, three, godot, textures, anim, perf, overlay)

    env_txt = ["# FF-02C environment (sanitized)", ""]
    for k, v in sorted(env["commands"].items()):
        env_txt.append(f"[{k}] available={v['available']} exit={v['exit_code']}")
        if v["stdout"]:
            env_txt.append(v["stdout"][:2000])
        if v["stderr"] and not v["available"]:
            env_txt.append(f"stderr: {v['stderr'][:500]}")
        env_txt.append("")
    env_txt.append("## session env")
    for k, v in sorted(env["session_env"].items()):
        env_txt.append(f"{k}={v}")

    overlay_txt = ["# FF-02C overlay support (sanitized)", "",
                   f"status: {overlay['status']} - {overlay['reason']}", "",
                   json.dumps(sanitize_obj(overlay), indent=2, sort_keys=True),
                   "", "Launch with ./scripts/ff01-overlay-test.sh and record PID/exit code manually."]

    (out / "environment.txt").write_text(sanitize_text("\n".join(env_txt) + "\n"), encoding="utf-8")
    write_json(out / "assets.json", assets)
    write_json(out / "threejs.json", three)
    write_json(out / "godot.json", godot)
    write_json(out / "texture-report.json", textures)
    write_json(out / "animation-structure.json", anim)
    write_json(out / "performance.json", perf)
    (out / "overlay.txt").write_text(sanitize_text("\n".join(overlay_txt) + "\n"), encoding="utf-8")
    (out / "FF-02C-REPORT.md").write_text(report, encoding="utf-8")

    print(f"FF-02C harness complete -> {out}")
    print(f"Overall: {[l for l in report.splitlines() if l.startswith('Overall status:')][0]}")
    print("Assets stay local. No upload. See artifacts/ff02c/FF-02C-REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
