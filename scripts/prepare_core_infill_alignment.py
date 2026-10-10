"""Prepare the infill registers (task F core, 9 October 2026; task H north, 10 October 2026): buildings on the author's 1891-96 OS footprints
that the scene did not model, from the reviewed selections in data/maps/core-infill-selection.json and north-infill-selection.json (their
descriptions and methods say how each selection was made and what was held back).

Writes data/maps/core-infill-footprint-alignment.json in the form build_factory_buildings.py reads (additionalSites,
additionalBuildings). Uses, storeys and materials are typological estimates; no Goad sheet is read here.
"""
import json
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from prepare_berger_starch_alignment import load_outlines, ring

ROOT = Path(__file__).resolve().parents[1]
# Batches: task F (core, south of the G.E.R. main line) and task H (north of it). Each reads its own selection and writes
# its own register; build_factory_buildings.py reads both.
BATCHES = {
    'core': dict(selection=ROOT/'data/maps/core-infill-selection.json', out=ROOT/'data/maps/core-infill-footprint-alignment.json',
                 label='task F core infill', audit='task F audit', estimate='task F typological estimate',
                 name='Core infill: unmodelled OS buildings in the core area'),
    'north': dict(selection=ROOT/'data/maps/north-infill-selection.json', out=ROOT/'data/maps/north-infill-footprint-alignment.json',
                  label='task H north infill', audit='task H audit', estimate='task H typological estimate (task F rules)',
                  name='North infill: unmodelled OS buildings north of the G.E.R. main line'),
}
CLEAR_M = .15      # kept clear of existing scene buildings
FRONTAGE_CLEAR_M = .35
KEEP_FRACTION = .7  # an outline losing more than this share to existing buildings is not added


def existing_buildings():
    """Every building the scene draws apart from this register's own ranges (so reruns are unchanged)."""
    read = lambda name: json.loads((ROOT/'docs/data'/name).read_text())
    fb, plan = read('factory-buildings.json'), read('ground-plan.json')['neighbourhood']
    polys = [Polygon(q['outer'], q['holes']) for b in fb['buildings'] if '-infill-' not in b['id'] for q in b['renderPolygons']]
    # The recorded outlines too: a street-trimmed range draws less than its footprint, and the reviews check footprints.
    polys += [Polygon(b['footprint'], b.get('worldHoles', [])) for b in fb['buildings'] if '-infill-' not in b['id']]
    polys += [Point(h['x'], h['z']).buffer(h['radius']) for h in fb['holders'] + plan['holders']]
    # High Street frontages by their source outlines, and further clear: their renders yield to factory ranges
    # within 0.3 m (build_high_street_frontages.py), these among them.
    frontages = unary_union([Polygon(b['footprint']).buffer(0) for b in read('high-street-frontages.json')['buildings']]).buffer(FRONTAGE_CLEAR_M)
    housing = read('housing-detail.json')
    polys += [Polygon(b['footprint']) for k in ('rows', 'extensions', 'privies') for b in housing[k] if b.get('footprint')]
    polys += [Polygon(b['footprint']) for k in ('terraces', 'houses', 'mappedFactories') for b in plan[k] if b.get('footprint')]
    return unary_union([p.buffer(0) for p in polys]).buffer(CLEAR_M).union(frontages)


def main(batch='core'):
    B = BATCHES[batch]
    sel = json.loads(B['selection'].read_text())
    outlines = load_outlines([b['fid'] for b in sel['buildings']])
    occupied = existing_buildings()
    records, new_sites, not_added = [], {}, []
    for b in sel['buildings']:
        source = outlines[b['fid']]
        g = source.difference(occupied)
        g = max(getattr(g, 'geoms', [g]), key=lambda q: q.area) if not g.is_empty else g
        if g.is_empty or g.area < KEEP_FRACTION*source.area or g.area < 10:
            not_added.append(f"fid {b['fid']} ({source.area:.0f} m²): {source.area - (0 if g.is_empty else g.area):.0f} m² under existing scene buildings")
            continue
        clipped = (f' Clipped {CLEAR_M} m clear of existing scene buildings: {source.area - g.area:.1f} m² removed.'
                   if source.area - g.area > .5 else '')
        site = b['site']
        if b['siteStatus'] == 'context site':
            new_sites[site] = (sel['contextSites'][str(site)],
                               f"Context grouping of scattered buildings by nearest street ({B['label']}); a model grouping, not a parcel.")
        elif b['siteStatus'] == 'new site':
            new_sites[site] = (b['siteName'], f"Site from the author's Industry_1893-95 polygon (feature index); first modelled in the {B['label']}.")
        review = (' Of 300 m² and over: to be read individually on the OS (and Goad where a sheet exists).' if b['reviewIndividually'] else '')
        records.append({
            'id': f"b{site}-infill-{b['fid']}", 'siteId': site, 'source': 'os-1893',
            'name': f"{new_sites.get(site, (b['siteName'],))[0]} — {b['label']} (OS outline {b['fid']})",
            'material': b['material'], 'roof': 'gable', 'storeysEstimate': b['storeys'],
            'footprintSource': 'author-os-footprints-1891-96', 'sourceFids': [b['fid']],
            'footprintEvidence': (f"Source outline fid {b['fid']} ({source.area:.0f} m²) from the author's 1891–96 OS building GeoPackage, simplified "
                                  'at 0.15 m; the OS five-foot plan draws it as a roofed building that the scene did not model ('+B['audit']+', '
                                  + B['selection'].relative_to(ROOT).as_posix() + ').' + clipped + review),
            'heightEvidence': (f"No reading: {b['storeys']} storey{'s' if b['storeys'] > 1 else ''} is the {B['estimate']} for a "
                               f"{b['label']} of this size; eaves height is the project default for that storey count (explicit estimate)."),
            'roofEvidence': 'Pitched roof is an interpretation; the OS draws no ridges.',
            'functionEvidence': (f"Not lettered: '{b['label']}' is an estimate from its size and position "
                                 f"({b['streetDistanceM']:.0f} m from {b['nearestStreet']})."),
            'worldFootprint': ring(g)})
    register = {
        'schemaVersion': 1, 'date': sel['date'], 'name': B['name'],
        'source': ("Author-supplied london_buildings_1891-96_corr_v1.gpkg (project extract west-ham-buffer-buildings-bng.geojson.gz); "
                   'cached NLS OS London five-foot mosaic (os-london-five-foot-1893)'),
        'sourceCRS': 'EPSG:27700 to scene origin E538900,N183209; x east, z south, metres',
        'method': sel['method'],
        'notAdded': not_added,
        'evidenceNotes': ['Storeys, materials, uses and roof forms are typological estimates; buildings of 300 m² and over are flagged for '
                          'individual reading. Held back for review: ' + '; '.join(f"fid {h['fid']}: {h['reason']}" for h in sel['heldBack'])],
        'buildings': [], 'structures': [], 'groups': [],
        'additionalSites': [{'id': sid, 'name': n, 'sources': ['os-1893'], 'coverage': f"Individual OS-mapped outlines ({B['label']})",
                             'notes': note + ' Roof exteriors are mapped; heights, uses and roof forms are estimates.'}
                            for sid, (n, note) in sorted(new_sites.items())],
        'additionalBuildings': records,
        'additionalStructures': []}
    B['out'].write_text(json.dumps(register, indent=2, ensure_ascii=False)+'\n')
    return register


if __name__ == '__main__':
    import sys
    for batch in (sys.argv[1:] or [b for b, spec in BATCHES.items() if spec['selection'].exists()]):
        r = main(batch)
        print(batch, len(r['additionalBuildings']), 'buildings,', len(r['additionalSites']), 'new sites;', len(r['notAdded']), 'not added:', r['notAdded'])
