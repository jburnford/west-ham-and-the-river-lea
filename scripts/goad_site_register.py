"""Shared helper for registers that model works on GeoPackage outlines with readings from a registered Goad sheet.

A register script supplies sites, buildings (one per outline), chimneys and kilns; make_register() writes
the register JSON in the form build_factory_buildings.py reads (additionalSites, additionalBuildings,
additionalStructures).
"""
import json
import math

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from prepare_berger_starch_alignment import load_outlines, ring


def make_register(out, *, sheet, sheet_note, date, name, method, sites, buildings, chimneys=(), kilns=(), notes=()):
    """sites: {id: (name, note)}; buildings: (fid, site, key, label, storeys, material, reading, extra);
    chimneys: (fid, site, key, feet or None, reading); kilns: (site, key, x, z, radius, height, reading)."""
    outlines = load_outlines([b[0] for b in buildings] + [c[0] for c in chimneys])
    records = []
    for fid, site, key, label, storeys, material, reading, extra in buildings:
        g = outlines[fid]
        extra = dict(extra)
        clip = extra.pop('clipBox', None)  # [x0, x1, z0, z1]: this record takes only that part of a shared outline
        if clip:
            g = g.intersection(box(clip[0], clip[2], clip[1], clip[3]))
            assert g.geom_type == 'Polygon' and g.area > 5, (key, g.geom_type, g.area)
        roof_bits = ['Pitched roof is an interpretation; Goad and the OS draw no ridges.']
        if extra.get('roofGlazing'):
            roof_bits.append('Glazed alternate roof planes stand for the skylights Goad colours grey-blue.')
        if extra.get('roofMaterial') == 'iron':
            roof_bits.append('Iron roof follows Goad\'s grey (metal) colour or an "iron roof" note.')
        b = {'id': f'b{site}-{key}', 'siteId': site, 'source': 'os-1893', 'name': f'{sites[site][0]} — {label}',
             'material': material, 'roof': 'gable', 'storeysEstimate': storeys,
             'footprintSource': 'author-os-footprints-1891-96', 'sourceFids': [fid],
             'footprintEvidence': ((f'Part ({g.area:.0f} m², x {clip[0]} to {clip[1]}, z {clip[2]} to {clip[3]}) of source outline fid {fid}, '
                                    'divided on a wall Goad draws; outline ' if clip else f'Source outline fid {fid} ({g.area:.0f} m²) ')
                                   + 'from the author\'s 1891–96 OS building GeoPackage, '
                                   'simplified at 0.15 m; checked against the cached NLS OS London five-foot mosaic (os-london-five-foot-1893) '
                                   f'and the registered Goad sheet {sheet}.'),
             'heightEvidence': (f'Storeys from {sheet_note}: {reading} '
                                + ('Eaves height is an explicit estimate.' if 'eavesHeight' in extra
                                   else 'Eaves height is the project default for that storey count (explicit estimate).')),
             'roofEvidence': ' '.join(roof_bits),
             'functionEvidence': f'Use as lettered on Goad sheet {sheet}: {reading}',
             'worldFootprint': ring(g)}
        b.update(extra)
        records.append(b)
    structures = []
    for fid, site, key, feet, reading, *more in chimneys:
        c = outlines[fid]
        section = more[0] if more else 'square'
        side = math.sqrt(c.area)
        s = {'id': key, 'siteId': site, 'source': 'os-1893', 'kind': 'chimney', 'name': f'{sites[site][0]} chimney',
             'x': round(c.centroid.x, 3), 'z': round(c.centroid.y, 3), 'radius': round(min(1.1, side*0.35), 2),
             'section': section, 'material': 'brick', 'baseHeight': 0.34, 'rotation': 0.0,
             'sourceFootprintFid': fid, 'sourcePolygons': [[ring(c)]], 'evidenceType': 'map-interpretation',
             'supportingSources': ['author-os-footprints-1891-96', 'os-1893', sheet], 'symbolKey': 'goad-symbol-key-1926',
             'positionEvidence': f'Placed on the small outline fid {fid} ({c.area:.1f} m²) where {reading}.',
             'profileEvidence': 'Square section follows the mapped base; taper, crown and brickwork are interpreted, not measured.'}
        if feet:
            s.update(height=round(feet*0.3048, 4), mappedHeightFeet=feet,
                     heightEvidence=f'"{feet}" printed beside the Goad chimney symbol, read as height in feet; converted at 0.3048 m/ft.')
        else:
            s.update(height=22.0, heightEvidence='No height printed; 22 m is the project’s typological estimate for an unmeasured works boiler stack.')
        structures.append(s)
    footprints = {b['id']: Polygon(b['worldFootprint']) for b in records}
    for site, key, x, z, radius, height, reading in kilns:
        disc = Point(x, z).buffer(radius)
        host = sorted((i for i, p in footprints.items() if p.intersects(disc)), key=lambda i: -footprints[i].intersection(disc).area)
        site_cover = unary_union([footprints[i] for i in host]).buffer(0.5) if host else Polygon()
        assert host and site_cover.contains(disc), ('kiln not inside modelled ranges', key)
        structures.append({
            'id': key, 'siteId': site, 'source': 'os-1893', 'kind': 'kiln', 'x': x, 'z': z, 'radius': radius, 'height': height,
            'evidence': f'{reading} on {sheet_note}.',
            'positionEvidence': f'Circle centre read on the registered Goad sheet {sheet}, inside range {host[0]}; the OS draws the range, not the kiln.',
            'radiusEvidence': f'Goad circle diameter about {2*radius:.1f} m.',
            'heightEvidence': f'Explicit estimate: {height:g} m, enough for the kiln to rise above its range; no height is printed.',
            'geometryEvidence': 'Drawn with the renderer’s simple cylindrical kiln; cone, cowl or pyramid roof not modelled.',
            'supportingSources': [sheet], 'evidenceType': 'map-interpretation'})
    register = {
        'schemaVersion': 1, 'date': date, 'sites': list(sites), 'name': name,
        'source': ("Author-supplied london_buildings_1891-96_corr_v1.gpkg (project extract west-ham-buffer-buildings-bng.geojson.gz); "
                   f"cached NLS OS London five-foot mosaic (os-london-five-foot-1893); {sheet_note}"),
        'sourceCRS': 'EPSG:27700 to scene origin E538900,N183209; x east, z south, metres',
        'method': method,
        'evidenceNotes': ['Goad colours read with the key (reference/factory-building-survey/goad-symbol-key-1926.jpg): pink brick, '
                          'yellow wood, grey metal buildings, grey-blue skylights; figures are storeys; feet are printed beside chimney symbols.',
                          *notes],
        'buildings': [], 'structures': [], 'groups': [],
        'additionalSites': [{'id': sid, 'name': n, 'sources': ['os-1893'],
                             'coverage': f'Individual OS-mapped ranges; uses, storeys and construction from Goad sheet {sheet}',
                             'notes': note + ' Roof exteriors are mapped; heights and roof forms are estimates.'}
                            for sid, (n, note) in sites.items()],
        'additionalBuildings': records,
        'additionalStructures': structures,
    }
    out.write_text(json.dumps(register, indent=2, ensure_ascii=False)+'\n')
    return register
