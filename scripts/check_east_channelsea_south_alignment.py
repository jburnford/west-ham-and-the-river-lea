"""Validate individual eastern roofs, direct trace and preserved earlier work."""
import sys
from shapely.geometry import Polygon
from factory_alignment_checks import check_register,load

r=load('data/maps/east-channelsea-south-footprint-alignment.json')
assert len(r['additionalSites'])==7
assert len(r['additionalBuildings'])==84
assert len({b['id'] for b in r['additionalBuildings']})==84
assert {s['id'] for s in r['additionalSites']}=={874,512,513,875,876,1125,9008}
assert {b['modelId'] for b in r['mapTracedBuildings']}=={'east-875-main-direct'}
assert r['directMapTraces'][0]['pixels'] and r['directMapTraces'][0]['localPixelOffset']==[-10,-1]
p=Polygon(r['mapTracedBuildings'][0]['worldFootprint'])
assert p.is_valid and 1600<p.area<2600,p.area
check_register('east-channelsea-south',{b['modelId'] for b in r['buildings']},83,0,
    'east-channelsea-before',preflight='--preflight' in sys.argv,
    later_registers=['east-channelsea-north','east-channelsea-upper'])
print('Six eastern compounds and the municipal stores replace sketch masses; OS roof exteriors and interpreted profiles are distinguished.')
