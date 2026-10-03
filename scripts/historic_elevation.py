"""Dated height selection and shared grid sampling; no cross-epoch averaging."""
import numpy as np


def select_controls(observations, config, epoch_id):
    epoch = config['epochs'][epoch_id]
    if epoch['geometryEpoch'] != epoch_id:
        raise ValueError(f'Epoch {epoch_id} requires its own reviewed period geometry')
    by_id = {p['id']: p for p in observations}
    if len(by_id) != len(observations):
        raise ValueError('Observation identities must be unique across source epochs')
    result = []
    for key in epoch['controlIds']:
        p = by_id[key]
        source = config['observationSources'].get(p['layer'])
        if not source or source['epoch'] not in epoch['allowedObservationEpochs']:
            raise ValueError(f'{key}: observation epoch is not authorized for {epoch_id}')
        if p['type'] != 'spot' or p['setting'] not in {'marsh', 'open_ground'}:
            raise ValueError(f'{key}: a structure height cannot control marsh terrain')
        if p['confidence'] != 'high' or p['disputed']:
            raise ValueError(f'{key}: unresolved observation')
        if p.get('setting_conflict'):
            resolution = epoch.get('surfaceConflictResolutions', {}).get(key, {})
            if (resolution.get('useAs') != 'adjacent-ground-approximation'
                    or not resolution.get('reason') or not epoch.get('surfaceReviews', {}).get(key)):
                raise ValueError(f'{key}: unresolved surface classification')
        if p.get('setting_rule') == 'value_fallback' and not epoch.get('surfaceReviews', {}).get(key):
            raise ValueError(f'{key}: surface classification requires review')
        if not p.get('datum', '').startswith('OD Liverpool'):
            raise ValueError(f'{key}: unsupported datum')
        result.append(p)
    if not result:
        raise ValueError(f'No reviewed controls for {epoch_id}')
    return result


def smooth(a, b, value):
    t = np.clip((value-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def sample_grid(values, bounds, step, x, z):
    """Bilinear grid nodes, inclusive edges; caller controls exterior policy."""
    fx = np.clip((np.asarray(x)-bounds[0])/step, 0, values.shape[1]-1)
    fz = np.clip((np.asarray(z)-bounds[1])/step, 0, values.shape[0]-1)
    i = np.minimum(np.floor(fx).astype(int), values.shape[1]-2)
    j = np.minimum(np.floor(fz).astype(int), values.shape[0]-2)
    u, v = fx-i, fz-j
    return (values[j, i]*(1-u)+values[j, i+1]*u)*(1-v)+(values[j+1, i]*(1-u)+values[j+1, i+1]*u)*v


def apply_grid(original, x, z, target, weight, bounds, step=1):
    x, z = np.broadcast_arrays(x, z)
    active = (x >= bounds[0]) & (x <= bounds[2]) & (z >= bounds[1]) & (z <= bounds[3])
    result = np.array(original, dtype=float, copy=True)
    if active.any():
        w = sample_grid(weight, bounds, step, x[active], z[active])
        y = sample_grid(target, bounds, step, x[active], z[active])
        result[active] += (y-result[active])*w
    return result
