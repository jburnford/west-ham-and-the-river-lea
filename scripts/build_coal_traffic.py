"""Build source-informed coal traffic, rejecting dry-land or overlapping hulls."""
import hashlib
import json
from pathlib import Path

from shapely.affinity import rotate, translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / 'data/maps/coal-traffic-1900.json'
SYSTEM = ROOT / 'docs/data/river-system-1900.json'
NETWORK = ROOT / 'docs/data/river-network.json'


def build():
    spec = json.loads(REGISTER.read_text())
    system = json.loads(SYSTEM.read_text())
    network = json.loads(NETWORK.read_text())
    waters = {
        'tidal': unary_union([Polygon(p[0], p[1:]) for p in system['tidalWaterPolygons'] + network['tide']['polygons']]),
        'retained': unary_union([Polygon(p[0], p[1:]) for p in system['waterPolygons']]),
    }
    thames = unary_union([Polygon(p[0], p[1:]) for r in system['reaches']
                          if r['id'] == 'thames-mouth-context' for p in r['polygons']])
    hulls = []
    for vessel in spec['vessels']:
        form = spec['forms'][vessel['form']]
        footprint = translate(rotate(box(-form['beam']/2, -form['length']/2,
                                        form['beam']/2, form['length']/2),
                                    -vessel['heading'], origin=(0, 0)), vessel['x'], vessel['z'])
        water = waters[vessel['water']]
        assert water.covers(footprint), f"{vessel['id']}: full hull envelope not in drawn {vessel['water']} water"
        if form['kind'] == 'collier':
            assert thames.covers(footprint), f"{vessel['id']}: seagoing ship outside Thames"
        for other_id, other_hull in hulls:
            assert not footprint.intersects(other_hull), f"{vessel['id']} overlaps {other_id}"
        vessel['bankClearanceMetres'] = round(footprint.distance(water.boundary), 3)
        hulls.append((vessel['id'], footprint))
    for source in spec['sources']:
        if 'localFile' in source:
            archive = ROOT/source['localFile']
            # Reference downloads are private/ignored; a fresh checkout can still
            # rebuild geometry from the committed register. Verify any local copy.
            if archive.exists():
                assert hashlib.sha256(archive.read_bytes()).hexdigest() == source['sha256'], source['id']
    spec['registerSha256'] = hashlib.sha256(REGISTER.read_bytes()).hexdigest()
    spec['waterSystemSha256'] = hashlib.sha256(SYSTEM.read_bytes()).hexdigest()
    spec['waterNetworkSha256'] = hashlib.sha256(NETWORK.read_bytes()).hexdigest()
    (ROOT/'docs/data/coal-traffic.json').write_text(json.dumps(spec, indent=2)+'\n')
    print(f"Coal traffic: {len(hulls)} separated hulls within their drawn water; three unloading groups.")


if __name__ == '__main__':
    build()
