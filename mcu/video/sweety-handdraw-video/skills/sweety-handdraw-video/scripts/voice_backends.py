"""Find already installed local voice tools and optional cloud keys; never installs or downloads."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

VOICE_HOME = Path.home()/'.local/share/sweety-handdraw-video/voices'
HF_HUB = Path(os.environ.get('HF_HUB_CACHE', Path.home()/'.cache/huggingface/hub'))


def python_with(module, variable):
    configured = os.environ.get(variable)
    if configured:
        return configured if Path(configured).is_file() else None
    return sys.executable if importlib.util.find_spec(module) else None


def hub_snapshot(repository, filename):
    matches = sorted((HF_HUB/('models--'+repository.replace('/', '--'))/'snapshots').glob('*/'+filename))
    return matches[-1] if matches else None


def existing(variable, default, marker=None):
    value = os.environ.get(variable)
    path = Path(value).expanduser() if value else default
    return path if path and path.exists() and (marker is None or (path/marker).is_file()) else None


def tools():
    whisper = hub_snapshot('mlx-community/whisper-large-v3-turbo', 'weights.safetensors')
    personal = VOICE_HOME/'catalog.json'
    voxcpm = os.environ.get('HANDDRAW_VOXCPM_MODEL')
    if not voxcpm and personal.is_file():
        voxcpm = next((voice.get('verified_generation_parameters', {}).get('model_path') for voice in json.loads(personal.read_text())['voices']
                       if voice.get('verified_generation_parameters', {}).get('model_path')), None)
    return {'mlx_python': python_with('mlx_audio', 'HANDDRAW_MLX_PYTHON'),
            'demucs_python': python_with('demucs', 'HANDDRAW_DEMUCS_PYTHON'),
            'htdemucs_weights': existing('HANDDRAW_HTDEMUCS_WEIGHTS', hub_snapshot('adefossez/HTDemucs', '*.safetensors')),
            'deepfilternet3': existing('HANDDRAW_DFN_MODEL', VOICE_HOME/'models/DeepFilterNet3', 'model.safetensors'),
            'asr_model': existing('HANDDRAW_ASR_MODEL', whisper.parent if whisper else None),
            'forced_aligner': existing('HANDDRAW_ALIGNER_MODEL', None),
            'voxcpm_model': existing('HANDDRAW_VOXCPM_MODEL', Path(voxcpm).expanduser() if voxcpm else None, 'config.json')}


def run_python(python, script, *arguments, timeout=1800):
    """Run a helper in another installed environment; offline so no model is fetched implicitly."""
    environment = {**os.environ, 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}
    result = subprocess.run([python, '-c', script, *map(str, arguments)], capture_output=True, text=True, timeout=timeout, env=environment)
    if result.returncode:
        raise RuntimeError(result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'helper failed')
    return json.loads(result.stdout.strip().splitlines()[-1])


def voice_studio_reachable(url='http://127.0.0.1:3900'):
    try:
        with urllib.request.urlopen(url.rstrip('/')+'/engines/tts', timeout=3) as response:
            return response.status == 200
    except OSError:
        return False


def voice_backends_report(voice_studio_url='http://127.0.0.1:3900'):
    found = tools()
    local = bool(found['mlx_python'] and found['voxcpm_model'])
    return {'default': 'local',
            'local_voxcpm2': {'available': local, 'python': found['mlx_python'],
                              'model': str(found['voxcpm_model']) if found['voxcpm_model'] else None},
            'voice_studio': {'reachable': voice_studio_reachable(voice_studio_url), 'url': voice_studio_url},
            'cleanup': {'htdemucs': bool(found['demucs_python'] and found['htdemucs_weights']), 'deepfilternet3': bool(found['mlx_python'] and found['deepfilternet3'])},
            'asr': bool(found['mlx_python'] and found['asr_model']), 'forced_aligner': bool(found['mlx_python'] and found['forced_aligner']),
            'cloud_optional': {'volcengine': bool(os.environ.get('VOLC_TTS_API_KEY') or (os.environ.get('VOLC_TTS_APP_ID') and os.environ.get('VOLC_TTS_ACCESS_KEY'))),
                               'gemini': bool(os.environ.get('GEMINI_API_KEY'))},
            'note': 'Cloud TTS is used only when the user configures a key and selects it; local generation stays the default.'}


if __name__ == '__main__':
    print(json.dumps(voice_backends_report(), ensure_ascii=False, indent=2))
