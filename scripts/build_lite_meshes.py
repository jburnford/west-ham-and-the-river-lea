"""Lite (phone) tier meshes (task G, 9 October 2026).

The river network is drawn from 1.84 million triangles on a 1 m grid, the largest single cost on a phone. This writes a
simplified copy for the lite tier only: the final vertex positions are composed by the page's own code
(scripts/bake_network_heights.mjs), simplified by quadric edge collapse (fast-simplification, borders preserved), and
each new vertex takes the sediment and land cover of the nearest original vertex (the page does not draw the network's
vertex colours). The full tier, and every height lookup on both tiers, keep the full network; only the drawn lite mesh
changes.

Writes docs/data/river-network-lite.json and docs/data/river-network.lite.{f32,u32,silt,cover}.
Run after the main landscape (it bakes that build's heights); then rebuild the scene manifest.
scripts/check_river_network_lite.mjs fails when the recorded input hashes no longer match.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import fast_simplification
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'docs/data'
REDUCTION = 0.75   # keep about a quarter of the triangles
AGGRESSION = 7.0   # fast-simplification default


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    meta = json.loads((DATA/'river-network.json').read_text())
    with tempfile.TemporaryDirectory() as tmp:
        baked = Path(tmp)/'network-final.f32'
        subprocess.run(['node', str(ROOT/'scripts/bake_network_heights.mjs'), str(baked)], check=True, cwd=ROOT)
        points = np.fromfile(baked, '<f4').reshape(-1, 3).astype(np.float64)
    faces = np.fromfile(DATA/meta['indexFile'], '<u4').reshape(-1, 3).astype(np.int32)
    silt = np.fromfile(DATA/meta['sedimentFile'], 'u1')
    cover = np.fromfile(DATA/meta['landcoverFile'], 'u1').reshape(-1, 2)
    assert len(points) == meta['vertices'] == len(silt) == len(cover)
    assert len(faces) == meta['triangles']
    lite_points, lite_faces = fast_simplification.simplify(points, faces, target_reduction=REDUCTION,
                                                           agg=AGGRESSION, preserve_border=True)
    # Drop vertices no face uses, then carry the per-vertex surface attributes over from the nearest original vertex.
    used = np.unique(lite_faces)
    remap = np.full(len(lite_points), -1, np.int64); remap[used] = np.arange(len(used))
    lite_points, lite_faces = lite_points[used], remap[lite_faces]
    nearest = cKDTree(points).query(lite_points)[1]
    files = {'positionFile': 'river-network.lite.f32', 'indexFile': 'river-network.lite.u32',
             'sedimentFile': 'river-network.lite.silt',
             'landcoverFile': 'river-network.lite.cover'}
    lite_points.astype('<f4').tofile(DATA/files['positionFile'])
    lite_faces.astype('<u4').tofile(DATA/files['indexFile'])
    silt[nearest].tofile(DATA/files['sedimentFile'])
    cover[nearest].tofile(DATA/files['landcoverFile'])
    record = {
        'description': ('Lite (phone) tier copy of the drawn river network: final positions composed by the page code '
                        '(scripts/bake_network_heights.mjs), simplified by quadric edge collapse with the open borders kept '
                        '(fast-simplification), surface attributes from the nearest original vertex. Drawn only; height '
                        'lookups use the full network.'),
        **files, 'vertices': int(len(lite_points)), 'triangles': int(len(lite_faces)),
        'sourceVertices': int(len(points)), 'sourceTriangles': int(len(faces)),
        'targetReduction': REDUCTION, 'aggression': AGGRESSION, 'preserveBorder': True,
        'inputHashes': {name: sha(DATA/name) for name in ['river-network.json', meta['positionFile'], meta['indexFile'],
                                                          'main-landscape-1900.json', 'main-landscape-1900.network.f32',
                                                          'river-system-1900.json', 'terrain-1900.json']},
    }
    (DATA/'river-network-lite.json').write_text(json.dumps(record, indent=1)+'\n')
    print(f"river network lite: {len(faces):,} -> {len(lite_faces):,} triangles, {len(points):,} -> {len(lite_points):,} vertices")


if __name__ == '__main__':
    main()
