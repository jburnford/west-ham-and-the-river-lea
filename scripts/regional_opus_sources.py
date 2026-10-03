"""Reconcile a frozen Opus update without changing original/reviewed sources."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

FIELDS = ['type','value_ft','confidence','setting','disputed','setting_conflict','layer','survey_dates','datum']
IMPORT_PATH = 'data/maps/lower-lea-region/opus-import-2026-10-02.json'


def reconcile(base, sources, live, protected):
    by_id = {r['id']:r for r in base}
    ids = list(by_id)
    tree = cKDTree([by_id[i]['positionBNG'] for i in ids])
    view_ids = {}
    for identifier, source in sources.items():
        if identifier not in by_id:
            continue
        for v in source.get('views', []):
            view_ids.setdefault(v.split('=')[0],set()).add(identifier)
    mappings, new, withheld, collisions = [], [], [], []
    occupied = set()
    for feature in live:
        r=feature['properties'];e,n=r['bng_e'],r['bng_n']
        if not (535000<=e<=542000 and 180000<=n<=187000):
            continue
        identifier=r['id'];canonical=None;reason=None
        if identifier in by_id:
            canonical=identifier;reason='same ID'
        else:
            provenance=set().union(*(view_ids.get(v.split('=')[0],set()) for v in r.get('views',[])))
            provenance={i for i in provenance if by_id[i]['layer']==r['layer'] and by_id[i]['type']==r['type']}
            near=tree.query_ball_point([e,n],6)
            compatible=[ids[j] for j in near if by_id[ids[j]]['layer']==r['layer'] and by_id[ids[j]]['type']==r['type']]
            if len(provenance)==1:
                canonical=next(iter(provenance));reason='shared original reading provenance; merged ID moved'
            elif len(compatible)==1 and abs(by_id[compatible[0]]['value_ft']-r['value_ft'])<.01 and np.linalg.norm(np.array(by_id[compatible[0]]['positionBNG'])-[e,n])<3:
                canonical=compatible[0];reason='same value/type/layer, overlapping source mosaic and under 3 m'
                if not set(sources[canonical].get('mosaics',[])).intersection(r.get('mosaics',[])):
                    canonical=None
            if canonical is None and compatible:
                withheld.append({'sourceId':identifier,'nearbyIds':compatible,'reason':'Possible duplicate requires source review; not added as another control.'})
                continue
        if canonical is not None:
            if canonical in occupied:
                collisions.append({'sourceId':identifier,'canonicalId':canonical,'reason':'Second live record maps to one canonical observation; withheld.'})
                continue
            occupied.add(canonical)
            changes={k:[by_id[canonical].get(k),r.get(k)] for k in FIELDS if by_id[canonical].get(k)!=r.get(k)}
            mappings.append({'sourceId':identifier,'canonicalId':canonical,'match':reason,
                             'preserveReviewedObservation':canonical in protected,'changes':changes})
        else:
            new.append(identifier)
    return {'mappings':mappings,'newIds':new,'withheldPossibleDuplicates':withheld,
            'withheldManyToOne':collisions,'unmatchedOriginalIds':sorted(set(ids)-occupied)}


def load_update(root, marks, sources):
    path=root/IMPORT_PATH
    data=json.loads(path.read_text())
    source_path=root/data['sourceSnapshot']
    raw=source_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==data['sourceSHA256']
    live={f['properties']['id']:f['properties'] for f in json.loads(raw)['features']}
    mapping={m['canonicalId']:m for m in data['mappings']}
    result=[]

    def mark_from(source,identifier,old=None):
        return {**(old or {}),**{k:source.get(k) for k in FIELDS},'id':identifier,
                'positionBNG':[source['bng_e'],source['bng_n']],
                'appliedFieldControl':(old or {}).get('appliedFieldControl',False),
                'observationSource':data['sourceSnapshot'],'opusSourceId':source['id']}

    for old in marks:
        m=mapping.get(old['id'])
        if m and not m['preserveReviewedObservation']:
            r=live[m['sourceId']]
            result.append(mark_from(r,old['id'],old))
            sources[old['id']]={**r,'id':old['id']}
        else:
            result.append(old)
    for identifier in data['newIds']:
        assert identifier not in sources
        r=live[identifier];result.append(mark_from(r,identifier));sources[identifier]=r
    restrictions={r['id']:r for r in data.get('surfaceRestrictions',[])}
    result=[{**r,'sourceUseRestriction':restrictions[r['id']]} if r['id'] in restrictions else r for r in result]
    summary={'sourceSnapshot':data['sourceSnapshot'],'sourceRecords':data['sourceRecords'],
             'newObservations':len(data['newIds']),
             'matchedExistingObservations':len(data['mappings']),
             'movedIdsMatched':sum(m['sourceId']!=m['canonicalId'] for m in data['mappings']),
             'reviewedObservationsPreserved':sum(m['preserveReviewedObservation'] for m in data['mappings']),
             'withheldPossibleDuplicates':data['withheldPossibleDuplicates'],
             'withheldManyToOne':data['withheldManyToOne'],'surfaceRestrictions':data.get('surfaceRestrictions',[])}
    return result,sources,summary,[path,source_path,Path(__file__).resolve()]
