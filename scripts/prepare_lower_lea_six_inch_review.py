"""Preserve native six-inch second-edition samples for whole-network review."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image
from factory_map_sources import mosaic, TO_MERCATOR, SHIFT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reference/lower-lea-connection-review'
AREAS={
    'six-inch-north':(536450,184650,538300,186700,16),
    'six-inch-middle':(537000,183300,539000,185350,16),
    'six-inch-south':(537450,180250,539800,183450,16),
    'six-inch-bow-junction':(537500,181850,538700,182950,17),
    'six-inch-upper-channelsea':(537520,184965,537860,185305,17),
}


def build():
    OUT.mkdir(parents=True,exist_ok=True);areas={}
    for name,(e0,n0,e1,n1,z) in AREAS.items():
        arr,world,_=mosaic((e0-538900,183209-n1,e1-538900,183209-n0),zoom=z,layer='os-six-inch-2nd')
        path=OUT/(name+'.png');Image.fromarray(arr).save(path)
        corners=world([[0,0],[arr.shape[1],0],[arr.shape[1],arr.shape[0]],[0,arr.shape[0]]])*[1,-1]+[538900,183209]
        mx0,my1=TO_MERCATOR.transform(e0,n1);mx1,my0=TO_MERCATOR.transform(e1,n0)
        step=2*SHIFT/(2**z)
        tx0,tx1=[math.floor((v+SHIFT)/step) for v in [mx0,mx1]]
        ty0,ty1=[math.floor((SHIFT-v)/step) for v in [my1,my0]]
        tiles=[ROOT/f'reference/nls-tiles/os-six-inch-2nd/{z}/{tx}/{ty}.png' for tx in range(tx0,tx1+1) for ty in range(ty0,ty1+1)]
        areas[name]={'image':path.name,'imageSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'zoom':z,'requestedBoundsBNG':[e0,n0,e1,n1],'BNGCorners':corners.tolist(),
            'tileOrigin':[tx0,ty0],'size':list(arr.shape[:2]),
            'sourceTileHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tiles}}
    result={'layerId':'six-inch-2nd','localLayer':'os-six-inch-2nd',
        'seriesDates':'1888–1913; dates vary by sheet, not a single 1900 snapshot',
        'use':'Network continuity review using blue water colouring; large-scale plans remain the source for individual structures.',
        'coverageNote':'Review panels cover the cached corridor from Hackney/Leyton marshes to the Thames; northwestern Lea Bridge endpoint is outside these panels.',
        'attribution':'Reproduced with the permission of the National Library of Scotland, CC-BY',
        'areas':areas}
    (OUT/'six-inch-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Exported {len(areas)} native six-inch review panels.')


if __name__=='__main__':build()
