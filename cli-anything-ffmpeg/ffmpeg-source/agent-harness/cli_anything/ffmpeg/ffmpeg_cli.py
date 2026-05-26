"""FFmpeg CLI — main entry point using Click."""

import sys
import click
import json
from pathlib import Path

from .core.project import Session, get_default_presets
from .core.preset import get_preset, list_presets, save_preset, get_builtin_presets
from .core.probe import FFProbe
from .core.transcode import FFmpegRunner
from .core.job import JobQueue, JobResult, JobStatus
from .utils.output import OutputFormatter
from .utils.validation import (
    validate_input_path, validate_output_path, validate_preset_name,
    validate_resolution, validate_crf, validate_time, build_validation_report,
)
from .utils.install import check_installation, ensure_ffmpeg, get_codecs, get_filters


@click.group()
@click.option("--json", "json_output", is_flag=True, help="Output machine-readable JSON")
@click.option("--ffmpeg-bin", default="ffmpeg", help="Path to ffmpeg binary")
@click.option("--ffprobe-bin", default="ffprobe", help="Path to ffprobe binary")
@click.pass_context
def cli(ctx, json_output, ffmpeg_bin, ffprobe_bin):
    """FFmpeg CLI harness — AI-friendly wrapper for ffmpeg/ffprobe."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_output
    ctx.obj["ffmpeg_bin"] = ffmpeg_bin
    ctx.obj["ffprobe_bin"] = ffprobe_bin
    ctx.obj["formatter"] = OutputFormatter(json_mode=json_output)
    ctx.obj["probe"] = FFProbe(binary=ffprobe_bin)
    ctx.obj["runner"] = FFmpegRunner(binary=ffmpeg_bin)


# ── INFO GROUP ──────────────────────────────────────────────────────────────

@cli.group("info")
def info_group():
    """Build information and diagnostics."""
    pass


@info_group.command("status")
@click.pass_context
def info_status(ctx):
    """Show ffmpeg/ffprobe installation status."""
    info = check_installation()
    if ctx.obj["json"]:
        click.echo(json.dumps(info, indent=2))
        return
    ffmpeg = info["ffmpeg"]
    if ffmpeg["found"]:
        click.echo(f"[OK] ffmpeg {ffmpeg['version']} at {ffmpeg['path']}")
    else:
        click.echo("[FAIL] ffmpeg not found in PATH")
    ffprobe = info["ffprobe"]
    if ffprobe["found"]:
        click.echo(f"[OK] ffprobe {ffprobe['version']} at {ffprobe['path']}")
    else:
        click.echo("[FAIL] ffprobe not found in PATH")


@info_group.command("codecs")
@click.pass_context
def info_codecs(ctx):
    """List available encoders/decoders."""
    ok, msg = ensure_ffmpeg()
    if not ok:
        click.echo(ctx.obj["formatter"].format({"status": "error", "error": msg}), err=True)
        sys.exit(1)
    codecs = get_codecs(ctx.obj["ffmpeg_bin"])
    if ctx.obj["json"]:
        click.echo(json.dumps(codecs, indent=2))
        return
    click.echo("=== Encoders ===")
    for e in codecs.get("encoders", []):
        click.echo(f"  {e['codec']:20s} {e['name']}")
    click.echo("\n=== Decoders ===")
    for d in codecs.get("decoders", []):
        click.echo(f"  {d['codec']:20s} {d['name']}")


@info_group.command("filters")
@click.pass_context
def info_filters(ctx):
    """List available video/audio filters."""
    ok, msg = ensure_ffmpeg()
    if not ok:
        click.echo(ctx.obj["formatter"].format({"status": "error", "error": msg}), err=True)
        sys.exit(1)
    filters = get_filters(ctx.obj["ffmpeg_bin"])
    if ctx.obj["json"]:
        click.echo(json.dumps({"filters": filters}, indent=2))
        return
    click.echo("=== Available Filters ===")
    for f in sorted(filters):
        click.echo(f"  {f}")


# ── TRANSCODE GROUP ─────────────────────────────────────────────────────────

@cli.group("transcode")
def transcode_group():
    """Transcode / convert media files."""
    pass


@transcode_group.command("run")
@click.argument("input", type=click.Path(exists=True))
@click.argument("output")
@click.option("--preset", "-p", default="default", help="Encoding preset name")
@click.option("--crf", type=int, help="Override CRF (quality 0-51)")
@click.option("--codec-video", "-c:v", help="Video codec (e.g. libx264, copy)")
@click.option("--codec-audio", "-c:a", help="Audio codec (e.g. aac, copy)")
@click.option("--bitrate-video", "-b:v", help="Video bitrate (e.g. 2M)")
@click.option("--bitrate-audio", "-b:a", help="Audio bitrate (e.g. 192k)")
@click.option("--vf", help="Video filter chain (e.g. scale=1280:720)")
@click.option("--af", help="Audio filter chain")
@click.option("--resolution", "-s", help="Output resolution (e.g. 1920x1080)")
@click.option("--fps", "-r", help="Output frame rate")
@click.option("--start", "-ss", help="Start time (HH:MM:SS or seconds)")
@click.option("--duration", "-t", help="Duration (seconds)")
@click.option("--preset-extra", multiple=True, help="Extra ffmpeg arguments")
@click.option("--y", "overwrite", is_flag=True, help="Overwrite output without asking")
@click.option("--dry-run", is_flag=True, help="Show command without executing")
@click.pass_context
def transcode_run(ctx, input, output, preset, crf, codec_video, codec_audio,
                  bitrate_video, bitrate_audio, vf, af, resolution, fps,
                  start, duration, preset_extra, overwrite, dry_run):
    """Run a single transcode job."""
    errors = []

    # Validate inputs
    ok, err = validate_input_path(input)
    if not ok:
        errors.append(err)

    ok, err = validate_output_path(output, overwrite)
    if not ok:
        errors.append(err)

    # Validate preset
    p = get_preset(preset)
    if not p:
        errors.append(f"Unknown preset: {preset}")

    if crf is not None:
        ok, err = validate_crf(crf)
        if not ok:
            errors.append(err)

    if resolution:
        ok, err = validate_resolution(resolution)
        if not ok:
            errors.append(err)

    if start:
        ok, err = validate_time(start)
        if not ok:
            errors.append(err)

    if errors:
        click.echo(build_validation_report(errors), err=True)
        sys.exit(1)

    # Build extra args
    extra = list(preset_extra)
    if vf:
        extra.extend(["-vf", vf])
    if af:
        extra.extend(["-af", af])
    if resolution:
        extra.extend(["-vf", f"scale={resolution.replace('x', ':')}"])
    if fps:
        extra.extend(["-r", str(fps)])
    if start:
        extra.extend(["-ss", start])
    if duration:
        extra.extend(["-t", str(duration)])
    if crf:
        # Override preset CRF
        pass  # handled in runner

    runner = ctx.obj["runner"]
    formatter = ctx.obj["formatter"]

    if dry_run:
        # Show the command that would be run
        from .core.preset import to_ffmpeg_args
        p_data = get_preset(preset)
        args_list = to_ffmpeg_args(p_data) if p_data else []
        cmd = f"{ctx.obj['ffmpeg_bin']} -y -i {input} " + " ".join(args_list) + " " + " ".join(extra) + f" {output}"
        if ctx.obj["json"]:
            click.echo(json.dumps({"dry_run": True, "command": cmd}))
        else:
            click.echo(f"[ffmpeg] Dry run:\n  {cmd}")
        return

    # Run transcode
    result = runner.probe_and_transcode(
        input_path=input,
        output_path=output,
        preset_name=preset,
        extra_args=extra,
        overwrite=overwrite,
    )

    if result["status"] == "failed":
        if ctx.obj["json"]:
            click.echo(json.dumps(result))
        else:
            click.echo(f"[ffmpeg] ERROR: {result.get('stderr', 'unknown error')}", err=True)
        sys.exit(1)

    click.echo(formatter.format(result))


@transcode_group.command("batch")
@click.argument("input_pattern", type=str)
@click.argument("output_dir", type=click.Path())
@click.option("--preset", "-p", default="default", help="Encoding preset")
@click.option("--suffix", default="_converted", help="Suffix for output files")
@click.option("--overwrite", "-y", is_flag=True)
@click.pass_context
def transcode_batch(ctx, input_pattern, output_dir, preset, suffix, overwrite):
    """Batch transcode multiple files."""
    from pathlib import Path
    import glob

    # Resolve pattern
    pattern = Path(input_pattern).expanduser()
    if pattern.exists() and pattern.is_file():
        files = [pattern]
    else:
        files = list(Path(".").glob(str(pattern)))

    if not files:
        click.echo(f"[ffmpeg] No files matched: {input_pattern}", err=True)
        sys.exit(1)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    runner = ctx.obj["runner"]
    results = []
    for f in files:
        out_name = f.stem + suffix + f.suffix
        out_path = str(Path(output_dir) / out_name)
        result = runner.probe_and_transcode(
            input_path=str(f),
            output_path=out_path,
            preset_name=preset,
            overwrite=overwrite,
        )
        results.append({"input": str(f), "output": out_path, "status": result["status"]})

    if ctx.obj["json"]:
        click.echo(json.dumps(results, indent=2))
    else:
        for r in results:
            status = "OK" if r["status"] == "complete" else "FAIL"
            click.echo(f"[{status}] {r['input']} -> {r['output']}")


# ── PROBE GROUP ─────────────────────────────────────────────────────────────

@cli.group("probe")
def probe_group():
    """Inspect media files with ffprobe."""
    pass


@probe_group.command("info")
@click.argument("input", type=click.Path(exists=True))
@click.option("--full", is_flag=True, help="Full probe with chapters")
@click.pass_context
def probe_info(ctx, input, full):
    """Get detailed info about a media file."""
    from .core.probe import FFProbe
    probe = FFProbe(binary=ctx.obj["ffprobe_bin"])
    data = probe.summary(input)
    formatter = ctx.obj["formatter"]

    if data.get("error"):
        click.echo(formatter.format({"status": "error", "error": data["error"]}), err=True)
        sys.exit(1)

    click.echo(formatter.format({"status": "probe", **data}))


@probe_group.command("streams")
@click.argument("input", type=click.Path(exists=True))
@click.pass_context
def probe_streams(ctx, input):
    """List all streams in a media file."""
    probe = FFProbe(binary=ctx.obj["ffprobe_bin"])
    data = probe.probe(input)
    if not data:
        click.echo(f"[ffprobe] Failed to read: {input}", err=True)
        sys.exit(1)
    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
    else:
        streams = data.get("streams", [])
        click.echo(f"Streams in {input}:")
        for i, s in enumerate(streams):
            click.echo(f"  [{i}] {s.get('codec_type', '?')}: {s.get('codec_name', '?')} "
                       f"{s.get('width', '')}x{s.get('height', '')} "
                       f"ch{s.get('channels', '')} {s.get('sample_rate', '')}Hz")


@probe_group.command("format")
@click.argument("input", type=click.Path(exists=True))
@click.pass_context
def probe_format(ctx, input):
    """Get format/container info."""
    probe = FFProbe(binary=ctx.obj["ffprobe_bin"])
    data = probe.format_info(input)
    if not data:
        click.echo(f"[ffprobe] Failed to read: {input}", err=True)
        sys.exit(1)
    if ctx.obj["json"]:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Format: {data.get('format_name', '?')}")
        click.echo(f"Duration: {float(data.get('duration', 0)):.1f}s")
        click.echo(f"Size: {int(data.get('size', 0))} bytes")
        click.echo(f"Bitrate: {int(data.get('bit_rate', 0))} bps")


# ── PRESET GROUP ─────────────────────────────────────────────────────────────

@cli.group("preset")
def preset_group():
    """Manage encoding presets."""
    pass


@preset_group.command("list")
@click.pass_context
def preset_list(ctx):
    """List all available presets."""
    names = list_presets()
    if ctx.obj["json"]:
        click.echo(json.dumps({"presets": names}))
    else:
        click.echo("Available presets:")
        for n in names:
            p = get_preset(n)
            if p:
                click.echo(f"  {n:20s}  codec={p['codec_video']}, crf={p.get('crf', 'N/A')}")


@preset_group.command("show")
@click.argument("name")
@click.pass_context
def preset_show(ctx, name):
    """Show preset details."""
    p = get_preset(name)
    if not p:
        click.echo(f"[ffmpeg] Unknown preset: {name}", err=True)
        sys.exit(1)
    if ctx.obj["json"]:
        click.echo(json.dumps(p, indent=2))
    else:
        click.echo(f"Preset: {name}")
        for k, v in p.items():
            click.echo(f"  {k}: {v}")


@preset_group.command("create")
@click.argument("name")
@click.option("--codec-video", "-c:v", default="libx264")
@click.option("--preset-video", "-preset", default="medium")
@click.option("--crf", type=int, default=23)
@click.option("--bitrate-video", "-b:v")
@click.option("--codec-audio", "-c:a", default="aac")
@click.option("--bitrate-audio", "-b:a", default="192k")
@click.option("--sample-rate", "-ar", type=int, default=48000)
@click.pass_context
def preset_create(ctx, name, codec_video, preset_video, crf, bitrate_video,
                  codec_audio, bitrate_audio, sample_rate):
    """Create a new preset."""
    if not validate_preset_name(name):
        click.echo("[ffmpeg] Invalid preset name (alphanumeric + hyphens only)", err=True)
        sys.exit(1)

    preset = {
        "name": name,
        "codec_video": codec_video,
        "preset_video": preset_video,
        "crf": crf,
        "bitrate_video": bitrate_video,
        "codec_audio": codec_audio,
        "bitrate_audio": bitrate_audio,
        "sample_rate": sample_rate,
        "extra_args": [],
    }
    save_preset(name, preset)
    click.echo(f"[ffmpeg] Preset '{name}' saved.")


@preset_group.command("delete")
@click.argument("name")
@click.pass_context
def preset_delete(ctx, name):
    """Delete a user preset."""
    from .core.preset import delete_preset
    ok = delete_preset(name)
    if ok:
        click.echo(f"[ffmpeg] Preset '{name}' deleted.")
    else:
        click.echo(f"[ffmpeg] Cannot delete builtin preset: {name}", err=True)


# ── SESSION GROUP ────────────────────────────────────────────────────────────

@cli.group("session")
def session_group():
    """Manage conversion sessions (job queues)."""
    pass


@session_group.command("save")
@click.argument("name")
@click.option("--preset", "-p", default="default")
@click.pass_context
def session_save(ctx, name, preset):
    """Save current session."""
    session = Session.load(name)
    session.active_preset = preset
    session.save()
    click.echo(f"[ffmpeg] Session '{name}' saved.")


@session_group.command("load")
@click.argument("name")
@click.pass_context
def session_load(ctx, name):
    """Load a session."""
    session = Session.load(name)
    if ctx.obj["json"]:
        click.echo(json.dumps({
            "name": session.name,
            "active_preset": session.active_preset,
            "jobs": len(session.jobs),
        }))
    else:
        click.echo(f"Session: {session.name}")
        click.echo(f"  Preset: {session.active_preset}")
        click.echo(f"  Jobs: {len(session.jobs)}")


@session_group.command("list")
@click.pass_context
def session_list(ctx):
    """List saved sessions."""
    names = Session.list_sessions()
    if ctx.obj["json"]:
        click.echo(json.dumps({"sessions": names}))
    else:
        if not names:
            click.echo("No saved sessions.")
        else:
            for n in names:
                click.echo(f"  {n}")


# ── MAIN ENTRY ───────────────────────────────────────────────────────────────

@cli.command("version")
@click.pass_context
def version_cmd(ctx):
    """Show version info."""
    info = check_installation()
    v = info["ffmpeg"]["version"] or "unknown"
    if ctx.obj["json"]:
        click.echo(json.dumps({"ffmpeg_version": v, "harness_version": "0.1.0"}))
    else:
        click.echo(f"ffmpeg {v}")
        click.echo(f"cli-anything-ffmpeg 0.1.0")


if __name__ == "__main__":
    cli(obj={})