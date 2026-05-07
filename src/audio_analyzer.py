"""Audio analysis using librosa: tempo, beats, energy contour, section boundaries."""
import librosa
import numpy as np


def analyze_audio(path):
    """Analyze an audio file and return a dict of structural data."""
    y, sr = librosa.load(path, sr=22050, mono=True)
    duration = len(y) / sr

    # Tempo + beat grid
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    tempo_val = float(tempo) if np.isscalar(tempo) else float(tempo[0])
    sec_per_beat = 60.0 / tempo_val
    bar_length = sec_per_beat * 4  # assume 4/4

    # Downbeats (every 4th beat)
    downbeats = beats[::4].tolist()

    # Energy contour
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    times_rms = librosa.times_like(rms, sr=sr, hop_length=hop)

    # Smooth the RMS over 2 seconds
    window_sec = 2.0
    window_samples = max(1, int(window_sec * sr / hop))
    smoothed = np.convolve(rms, np.ones(window_samples) / window_samples, mode='same')
    smoothed_norm = (smoothed - smoothed.min()) / (smoothed.max() - smoothed.min() + 1e-9)

    # Section boundaries via spectral segmentation
    y_harm = librosa.effects.harmonic(y)
    chroma = librosa.feature.chroma_cqt(y=y_harm, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    feat = np.vstack([chroma, mfcc])

    # Auto-pick segment count based on song length
    n_segs = max(8, min(16, int(duration / 25)))
    boundaries_frames = librosa.segment.agglomerative(feat, n_segs)
    boundary_times = librosa.frames_to_time(boundaries_frames, sr=sr).tolist()

    # Energy profile sampled at 1-second intervals
    energy_profile = []
    for t in np.arange(0, duration, 1.0):
        idx = int(np.argmin(np.abs(times_rms - t)))
        energy_profile.append({"time": float(t), "energy": float(smoothed_norm[idx])})

    return {
        "duration": float(duration),
        "tempo": tempo_val,
        "sec_per_beat": sec_per_beat,
        "bar_length": bar_length,
        "beats": beats.tolist(),
        "downbeats": downbeats,
        "boundaries": boundary_times,
        "energy_profile": energy_profile,
    }
