"""Export native cached map samples for the dated river-connection review."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image
from factory_map_sources import mosaic, TO_MERCATOR, SHIFT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reference/lower-lea-connection-review'
SITES={'pudding-mill':(538023,183408,90),'old-ford':(537379,183940,190),
       'upper-channelsea':(537590,185490,200),'abbey-mill':(538908,183258,100),
       'bow-back-mouth':(537851,183134,130),'three-mills':(538292,182827,130),
       'bow-locks-junction':(538270,182275,230)}
# upper-channelsea is the original search-area filename; the reviewed structure
# in that crop is Temple Mills bridge/weir, not the whole upper Channelsea.


def build():
    OUT.mkdir(parents=True,exist_ok=True);meta={}
    for name,(e,n,r) in SITES.items():
        meta[name]={}
        for layer in ['os-london-five-foot-1893','os-london-skeleton-5280']:
            margin=r+30  # Web Mercator/BNG rotation can otherwise clip a crop corner.
            bounds=(e-538900-margin,183209-n-margin,e-538900+margin,183209-n+margin)
            arr,world,pixel=mosaic(bounds,layer=layer)
            px=pixel([[e-538900,183209-n]])[0]
            # Fixed native-pixel crop; never resample the cartography.
            crop=tuple(round(v) for v in [px[0]-r/.373,px[1]-r/.373,px[0]+r/.373,px[1]+r/.373])
            assert 0<=crop[0]<crop[2]<=arr.shape[1] and 0<=crop[1]<crop[3]<=arr.shape[0]
            image_path=OUT/f'{name}-{layer}.png'
            Image.fromarray(arr).crop(crop).save(image_path)
            corners=world([[crop[0],crop[1]],[crop[2],crop[1]],[crop[2],crop[3]],[crop[0],crop[3]]])*[1,-1]+[538900,183209]
            mx0,my1=TO_MERCATOR.transform(e-margin,n+margin);mx1,my0=TO_MERCATOR.transform(e+margin,n-margin)
            step=2*SHIFT/(2**18)
            tx0,tx1=[math.floor((v+SHIFT)/step) for v in [mx0,mx1]]
            ty0,ty1=[math.floor((SHIFT-v)/step) for v in [my1,my0]]
            tiles=[ROOT/f'reference/nls-tiles/{layer}/18/{tx}/{ty}.png' for tx in range(tx0,tx1+1) for ty in range(ty0,ty1+1)]
            meta[name][layer]={'cropPixelBox':crop,'BNGCorners':corners.tolist(),
                'centreBNG':[e,n],'image':image_path.name,'imageSHA256':hashlib.sha256(image_path.read_bytes()).hexdigest(),
                'zoom':18,'tileOrigin':[tx0,ty0],'tileSize':256,
                'sourceTileHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tiles},
                'dateStatus':'Layer attribution only; individual sheet date not verified',
                'attribution':'Reproduced with the permission of the National Library of Scotland, CC-BY',
                'pixelConvention':'Native crop pixels: add cropPixelBox origin, then tileOrigin*256 for global Web Mercator XYZ pixels'}
    (OUT/'map-crops.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(f'Exported {sum(map(len,meta.values()))} georeferenced map crops without resampling.')


if __name__=='__main__':build()
