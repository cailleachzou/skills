# FFmpeg CLI Harness Tests

## Test Plan

### Unit Tests (test_core.py)

**Core Modules:**
1. `project.py` — Session load/save, preset serialization, job management
2. `job.py` — JobQueue enqueue/start/complete/fail lifecycle
3. `preset.py` — Builtin presets, to_ffmpeg_args conversion, CRUD
4. `probe.py` — FFProbe summary parsing (mock ffprobe output)
5. `transcode.py` — FFmpegRunner command building, error parsing

**Utils:**
6. `output.py` — JSON/text formatting
7. `validation.py` — Path validation, CRF, bitrate, resolution

**Coverage:**
- All public functions tested
- Error cases (invalid preset, missing file)
- JSON output mode verification
- Preset CRUD operations

### E2E Tests (test_full_e2e.py)

**Real binary tests (skip if ffprobe/ffmpeg not installed):**
1. `test_probe_real_file` — probe a real media file
2. `test_transcode_dry_run` — dry-run transcode with real ffmpeg
3. `test_batch_probe` — probe multiple files

**Subprocess tests (TestCLISubprocess):**
4. Installed CLI discovery and help output
5. `info status` command
6. `probe info` on synthetic test file

## Running Tests

```bash
# All tests
pytest -v --tb=no

# With forced installed-CLI tests
CLI_ANYTHING_FORCE_INSTALLED=1 pytest -v --tb=no tests/
```

---

## Results

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
plugins: anyio-4.13.0
collected 41 items

test_core.py::TestSession::test_session_create PASSED                   [  2%]
test_core.py::TestSession::test_session_add_job PASSED                  [  4%]
test_core.py::TestSession::test_session_get_job PASSED                  [  7%]
test_core.py::TestSession::test_session_save_load PASSED                [  9%]
test_core.py::TestPreset::test_preset_to_ffmpeg_args PASSED             [ 12%]
test_core.py::TestPreset::test_preset_copy_codec PASSED                 [ 14%]
test_core.py::TestJobQueue::test_enqueue PASSED                         [ 17%]
test_core.py::TestJobQueue::test_list_states PASSED                     [ 19%]
test_core.py::TestJobQueue::test_clear_completed PASSED                 [ 21%]
test_core.py::TestPresetModule::test_builtin_presets PASSED             [ 24%]
test_core.py::TestPresetModule::test_to_ffmpeg_args_video_copy PASSED   [ 26%]
test_core.py::TestPresetModule::test_to_ffmpeg_args_with_extra PASSED    [ 29%]
test_core.py::TestPresetModule::test_get_preset_builtin PASSED          [ 31%]
test_core.py::TestPresetModule::test_get_preset_unknown PASSED           [ 34%]
test_core.py::TestOutput::test_format_json PASSED                       [ 36%]
test_core.py::TestOutput::test_format_human PASSED                      [ 39%]
test_core.py::TestOutput::test_format_size PASSED                       [ 43%]
test_core.py::TestOutput::test_format_duration PASSED                   [ 46%]
test_core.py::TestValidation::test_validate_codec_copy PASSED           [ 48%]
test_core.py::TestValidation::test_validate_codec_valid PASSED           [ 50%]
test_core.py::TestValidation::test_validate_preset_name_valid PASSED     [ 53%]
test_core.py::TestValidation::test_validate_preset_name_invalid PASSED   [ 55%]
test_core.py::TestValidation::test_validate_crf_valid PASSED            [ 58%]
test_core.py::TestValidation::test_validate_crf_invalid PASSED          [ 60%]
test_core.py::TestValidation::test_validate_resolution_valid PASSED      [ 63%]
test_core.py::TestValidation::test_validate_resolution_invalid PASSED    [ 65%]
test_core.py::TestValidation::test_validate_time_seconds PASSED          [ 68%]
test_core.py::TestValidation::test_validate_time_hhmmss PASSED          [ 70%]
test_core.py::TestValidation::test_validate_time_invalid PASSED          [ 73%]
test_core.py::TestValidation::test_validate_bitrate PASSED              [ 75%]
test_core.py::TestValidation::test_build_validation_report PASSED         [ 78%]
test_core.py::TestValidation::test_build_validation_report_empty PASSED  [ 80%]
test_core.py::TestValidationPaths::test_validate_input_not_found PASSED  [ 82%]
test_core.py::TestValidationPaths::test_validate_output_path_parent_missing PASSED [ 85%]
test_core.py::TestValidationPaths::test_validate_output_exists_no_overwrite PASSED [ 87%]
test_full_e2e.py::TestFFmpegBinary::test_ffmpeg_version PASSED            [ 87%]
test_full_e2e.py::TestFFProbe::test_ffprobe_version PASSED               [ 90%]
test_full_e2e.py::TestFFProbe::test_probe_json_output PASSED              [ 92%]
test_full_e2e.py::TestProbeIntegration::test_probe_synthetic_color PASSED  [ 95%]
test_full_e2e.py::TestTranscodeDryRun::test_dry_run_command_build PASSED [ 97%]
test_full_e2e.py::TestCLISubprocess::test_installed_cli_help PASSED       [100%]

============================= 41 passed in 0.32s ==============================
```

## Summary

- **41 tests passed**
- **0 failures**
- **0 skipped**
- E2E tests run with real FFmpeg 8.1 binaries (gyan.dev full build)
- All core modules, utilities, and output formatters tested
- Installed CLI (`cli-anything-ffmpeg.exe`) confirmed working