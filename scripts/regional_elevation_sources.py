"""Native-map additions for the regional trial; never rewrite the snapshot."""
import hashlib
import json

from shapely.geometry import Polygon

from spot_height_mosaics import pixel_to_coords


def load_supplement(root):
    path = root/'data/maps/lower-lea-region/regional-elevation-supplement-1900.json'
    data = json.loads(path.read_text())
    assert data['targetEpoch']=='1900'
    paths = [path, root/'scripts/regional_elevation_sources.py', root/'scripts/spot_height_mosaics.py']
    registrations = {}
    for name, source in data['sources'].items():
        for source_path, digest in source['hashes'].items():
            p = root/source_path
            assert hashlib.sha256(p.read_bytes()).hexdigest()==digest, source_path
            paths.append(p)
        registrations[name] = json.loads((root/source['registration']).read_text())
        assert registrations[name]['layer']==data['sourceLayer']

    def bng(name, pixel):
        # Match the original transcription's pixel-centre convention.
        p = pixel_to_coords(registrations[name],pixel[0]+.5,pixel[1]+.5)
        return [p['bng_e'],p['bng_n']]

    marks, sources, exclusions = [], {}, []
    for r in data['observations']:
        assert r['confidence'] in {'high','medium','low'}
        e,n = bng(r['mosaic'],r['mapPixel'])
        assert r['id']==f'sh_{round(e)}_{round(n)}'
        assert 0<=r['mapPixel'][0]<1024 and 0<=r['mapPixel'][1]<1024
        paths.append(root/r['reviewCrop'])
        source = data['sources'][r['mosaic']]
        marks.append({'id':r['id'],'type':'spot','value_ft':r['valueFeet'],
                      'confidence':r['confidence'],'setting':r['setting'],
                      'disputed':False,'setting_conflict':False,
                      'layer':data['sourceLayer'],'survey_dates':data['surveyDates'],
                      'datum':data['datum'],'positionBNG':[round(e,3),round(n,3)],
                      'appliedFieldControl':False,'observationSource':str(path.relative_to(root)),
                      'regionalSurfaceReview':{**r,'mosaic':source['mosaic'],
                          'registration':source['registration']}})
        sources[r['id']] = {'setting_source':'reader','notes':r['review'],
                            'mosaics':[r['mosaic']],
                            'views':[f"regional-review:{r['mosaic']}@{r['mapPixel'][0]},{r['mapPixel'][1]}={r['valueFeet']}"],
                            'readers':['regional-map-review'],'spread_m':0}
    assert len(sources)==len(marks),'Duplicate supplemental IDs'
    for r in data['terrainExclusions']:
        for key in ['reviewCrop','contextCrop']:
            if r.get(key):
                paths.append(root/r[key])
        points = [bng(r['mosaic'],p) for p in r['pixels']]
        geometry = Polygon(points)
        assert geometry.is_valid and geometry.area>0,r['id']
        exclusions.append({**r,'polygonBNG':points,'areaM2':geometry.area})
    return marks,sources,exclusions,paths,data
