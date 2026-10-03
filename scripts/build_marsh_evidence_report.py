"""Publish the selected early review and the regional model comparison."""
import csv
import html
import json
import shutil
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/data/lower-lea-region'
review=json.loads((ROOT/'data/maps/lower-lea-region/marsh-baseline-1848-review.json').read_text())
meta=json.loads((OUT/'landscape-1900.json').read_text())
audit=json.loads((OUT/'elevation-audit.json').read_text())
assets=OUT/'marsh-evidence';assets.mkdir(exist_ok=True)
for r in review['observations']:
    source=ROOT/r['detailCrop'];shutil.copyfile(source,assets/source.name)
shutil.copyfile(ROOT/'reference/marsh-baseline-1848-2026-10-02/early-056-detail.png',assets/'early-056-detail.png')
(assets/'selected-readings.json').write_text(json.dumps(review,indent=2)+'\n')
with (assets/'selected-readings.csv').open('w') as f:
    writer=csv.writer(f);writer.writerow(['id','region','feet_original_datum','provisional_odn_m','easting','northing','baseline_proxy','surface_role','value_confidence','mosaic','pixel_x','pixel_y','notes'])
    for r in review['observations']:writer.writerow([r['id'],r['region'],r['valueFeet'],r['provisionalODNMetres'],*r['positionBNG'],r['baselineUse'],r['role'],r['valueConfidence'],r['mosaic'],*r['pixel'],r['notes']])
shape=(meta['height'],meta['width'])
def raster(key,dtype='<f4'):return np.fromfile(OUT/meta[key],dtype).reshape(shape)
ground=raster('groundFile');surface=raster('heightFile');weight=raster('earlyMarshWeightFile');kind=raster('kindFile','u1')
e0,n0,e1,n1=meta['boundsBNG'];step=meta['cellSizeMetres'];extent=[e0/1000,e1/1000,n0/1000,n1/1000]
fig,axes=plt.subplots(1,2,figsize=(12,9),layout='constrained');norm=Normalize(2,20)
for ax,values,title in zip(axes,[ground,surface],['Underlying marsh and adjoining ground','With later mapped surfaces']):
    ft=values/.3048-meta['verticalReference']['liverpoolToNewlynFeet']
    im=ax.imshow(np.ma.masked_where((weight==0)|~np.isfinite(values),ft),extent=extent,cmap='terrain',norm=norm,interpolation='nearest')
    outline=np.array(meta['regionalMarshBaseline']['config']['outlineBNG'])/1000;ax.plot(*outline.T,color='#777777',lw=.7,ls='--')
    for r in review['observations']:
        e,n=np.array(r['positionBNG'])/1000
        ax.scatter(e,n,s=15 if r['baselineUse'] else 25,c='#182f3a' if r['baselineUse'] else '#a83929',marker='o' if r['baselineUse'] else 'x',linewidths=.8)
    for text,e,n in [('Hackney / Temple',536.7,186.4),('Stratford',537.7,184.4),('Mill Meads',538.8,183.2),('Abbey marsh',539.5,182.8),('Plaistow marsh',540.9,181.9)]:
        ax.annotate(text,(e,n),fontsize=8,xytext=(3,3),textcoords='offset points',bbox={'facecolor':'white','alpha':.75,'edgecolor':'none','pad':1})
    ax.set(xlim=(536,542.2),ylim=(180,187),title=title,xlabel='BNG easting (km)',ylabel='BNG northing (km)');ax.set_aspect('equal')
fig.colorbar(im,ax=axes,shrink=.7,label='Feet, historical datum (provisional conversion for model)')
fig.suptitle('Early evidence across a continuous marsh base\nDots: accepted low-lane/ground-margin proxies · crosses: excluded comparisons',fontsize=12)
fig.savefig(assets/'regional-marsh-comparison.png',dpi=180);plt.close(fig)
used=set(meta['laterSurfaceLayers']['usedSourceIds'])
continuous=meta.get('continuousStructures',{})
role_reviews={r['id']:r for r in continuous.get('policy',{}).get('surfaceReview',[])}
# Inventory of all surface observations in the early-derived interior: presence
# of a point is distinct from an inferred feature footprint.
interior=[]
for r in audit['records']:
    e,n=r['positionBNG'];row,col=int((n1-n)//step),int((e-e0)//step)
    if not(0<=row<shape[0] and 0<=col<shape[1] and weight[row,col]==1):continue
    if r['type']!='spot' or r['confidence']!='high' or r['disputed'] or r.get('setting_conflict'):continue
    if r['surfaceFamily'] not in ('road','yard','wall','bank-or-embankment','railway'):continue
    interior.append({'id':r['id'],'family':'road' if r['id'] in role_reviews else r['surfaceFamily'],'setting':'footpath beside railway' if r['id'] in role_reviews else r['setting'],'surfaceReview':role_reviews.get(r['id']),'valueFeet':r['value_ft'],'heightODNMetres':r['provisionalODNMetres'],'positionBNG':r['positionBNG'],'usedInMappedLayer':r['id'] in used,'notes':r['notes']})
(assets/'later-surface-evidence.json').write_text(json.dumps(interior,indent=2)+'\n')
counts=Counter(r['family'] for r in interior);matched=Counter(r['family'] for r in interior if r['usedInMappedLayer'])
labels={'hackney-temple':'Hackney Marsh / Temple Mills','leyton-north':'Northern Leyton marsh (one point)','stratford-west':'Western Stratford marsh','stratford-east':'Eastern Stratford marsh','mill-meads':'Northern Mill Meads','abbey-marsh':'Abbey marsh, east of Abbey Creek','plaistow-west':'Western Plaistow marsh','plaistow-east':'Eastern Plaistow marsh','thames-marsh':'Southern marsh / Thames approaches'}
regional=''.join(f'<tr><td>{labels[r["id"]]}</td><td>{r["count"]}</td><td>{r["observedRangeFeet"][0]:g}–{r["observedRangeFeet"][1]:g}</td><td>{r["medianFeet"]:g}</td><td>{html.escape(r["description"])}</td></tr>' for r in review['regions'])
observations=''.join(f'<tr><td>{r["id"]}</td><td>{labels.get(r["region"],r["region"])}</td><td>{r["valueFeet"]:g}</td><td>{"Proxy" if r["baselineUse"] else "Excluded comparison"}: {r["role"]}</td><td>{r["valueConfidence"]}</td><td><a href="data/lower-lea-region/marsh-evidence/{Path(r["detailCrop"]).name}">{r["mosaic"]}, panel {r["detailPanel"]+1}</a></td></tr>' for r in review['observations'])
features=''.join(f'<tr><td>{html.escape(f["name"])}</td><td>{len(f["sourceIds"])}</td><td>{f.get("areaM2",f["cells"]*step**2):,.0f}</td><td>{html.escape(f["method"])}</td></tr>' for f in meta['laterSurfaceLayers']['features'])
inventory=''.join(f'<tr><td>{family}</td><td>{count}</td><td>{matched[family]}</td><td>{count-matched[family]}</td></tr>' for family,count in sorted(counts.items()))
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lower Lea marsh levels · 1848 evidence</title><link rel="stylesheet" href="lower-lea-region.css"><style>main{{display:block;max-width:1200px}}p{{max-width:1000px}}img{{width:100%;height:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;padding:9px;border-bottom:1px solid #ccc;vertical-align:top}}.scroll{{overflow-x:auto}}a{{color:#14747a}}h2{{margin-top:2em}}</style></head><body><header><nav><a href="lower-lea-landscape.html">Working landscape</a><a href="lower-lea-region.html?elevation=landscape">Elevation map and later sources</a></nav><p class="eyebrow">SELECTED REGIONAL REVIEW · 2 OCTOBER 2026</p><h1>The marsh beneath the later landscape</h1><p>The 1848–51 survey supports a broad marsh base falling from the northern Lea valley through Stratford to the lower southern and eastern marshes. Streets, factory yards and embankments are added as local surfaces.</p></header><main>
<p>Reviewed 57 selected readings in enlarged source crops and regional map context. Forty-five low-lane or ground-margin readings inform the marsh estimate; twelve bank, bridge, major-road, benchmark or terrace comparisons are excluded. This is a selected regional analysis, not a completed transcription of the 857 cached early mosaics. Most accepted readings are <strong>proxies along low lanes</strong>, not measurements in field interiors.</p>
<h2>Regional levels in the original feet</h2><p>Ranges describe the accepted observations; medians summarize each group, not a mandated flat level. The model interpolates the individual positions. Ordinary low lanes receive no blanket fill deduction.</p><div class="scroll"><table><thead><tr><th>Region</th><th>Readings</th><th>Range (ft)</th><th>Median (ft)</th><th>Interpretation</th></tr></thead><tbody>{regional}</tbody></table></div>
<p>Stratford’s roughly 11–13 ft and northern Mill Meads’ roughly 8 ft are supported. The 4–6 ft evidence belongs mainly to Abbey/Plaistow and the southern marshes. It does not establish a uniform fall through Mill Meads: later reviewed readings of 7.7 and 7.3 ft remain valid in southern Mill Meads. The eastern Stratford pair is lower, 10.5/10.7 ft, consistent with the later 11.2/10.8 ft ground-margin evidence.</p>
<p>The author’s <em>West Ham and the River Lea</em>, especially the 1805 map and “Marshlands and Early Industry” (PDF pages 35, 42–43 and 45), establishes the broader marsh setting and later development. The regional envelope is an interpretation of that evidence, not a surveyed boundary.</p>
<h2>One regional base, with local raised surfaces</h2><img src="data/lower-lea-region/marsh-evidence/regional-marsh-comparison.png" alt="Side-by-side maps of underlying marsh ground and later mapped raised surfaces, with early source positions and the provisional marsh envelope.">
<p>The fully early-derived base covers {meta['regionalMarshBaseline']['fullWeightAreaKm2']:.2f} km². It uses all accepted early proxies with inverse-distance weighting, 100 m positional smoothing and a smooth 600 m distance taper, refined by later accepted marsh or independently reviewed ground observations. Sparse interiors are estimated. Modern relief and non-marsh corrections cannot propagate into this interior. A 120 m transition at the approximate outer edge blends the surrounding model into the marsh-side ground level. This strip is classified as an estimated blend, not an exact historical control surface or a flood barrier. The former isolated Pudding–City correction is now part of this broader base.</p>
<p>A 29.7 ft workhouse-ground reading belongs outside the marsh estimate on the Bromley side. Other unreviewed premises and embankment-foot readings are retained separately: neither an open plot nor a bank foot establishes a marsh level or a bank crest. Knobshill Cottage’s 13.9 ft garden and reviewed 17.1–18.6 ft bank margins remain local raised features.</p>
<h2>Later surfaces fitted so far</h2><p>The banks now follow continuous joined shorelines. Crest readings control profiles by distance along each bank, rather than isolated patches around dots. Unanchored components use an explicitly inferred regional crest continuation. Railways retain their existing continuous station grades, including junction approaches, where no verified rail level is available. The sewer includes its full flat crest and side slopes, the High Street cover profile and separate elevated spans. Bridge decks do not fill the water or become ground barriers. Feature footprints below can overlap and are not additive.</p><div class="scroll"><table><thead><tr><th>Feature</th><th>Contributing readings</th><th>Modelled footprint (m²)</th><th>Method</th></tr></thead><tbody>{features}</tbody></table></div>
<h2>Remaining geometry and evidence gaps</h2><p>Within the early-derived interior, the following high-confidence, undisputed later spot readings are available. “Matched” means actually contributing to one of the mapped layer fits above. Unmatched readings remain in the evidence inventory; they do not create arbitrary elevated patches. The separate cottage/bank review is recorded in the landscape provenance rather than these counts.</p><div class="scroll"><table><thead><tr><th>Surface</th><th>Available readings</th><th>Matched</th><th>Unmatched</th></tr></thead><tbody>{inventory}</tbody></table></div>
<p>Next geometry priorities are the streets, industrial plots and additional railway alignments represented by unmatched points. Buildings alone do not establish yard fill height. Continuous banks and the mapped railway/sewer routes now have a separate fine mesh with 4 m edge sampling; the 10 m raster alone cannot encode their hydraulic topology. The 11.3 ft point north of the LT&amp;SR was checked on the source map and excluded as a rail-formation control: it lies on the footpath beside the railway. The <a href="./?rivers=1">main industrial reconstruction</a> now uses this marsh base, continuous bank profiles, refitted railway/sewer slopes and seated buildings. Premises without yard observations retain an explicitly estimated floor. Channel beds and exposed tidal mud retain their existing sections. The flood solver has not yet been recalibrated to the revised ground.</p>
<h2>Readings and source crops</h2><p><a href="data/lower-lea-region/marsh-evidence/selected-readings.csv">Download early readings (CSV)</a> · <a href="data/lower-lea-region/marsh-evidence/selected-readings.json">Review, coordinates and source hashes (JSON)</a> · <a href="data/lower-lea-region/marsh-evidence/later-surface-evidence.json">Later surface inventory</a> · <a href="data/lower-lea-region/landscape-1900.json">Model provenance</a>. Contact sheets contain six or eight numbered source panels. The expanded <a href="data/lower-lea-region/marsh-evidence/early-056-detail.png">6.2 ft crop</a> provides additional context for early-056.</p><div class="scroll"><table><thead><tr><th>ID</th><th>Region</th><th>Feet</th><th>Role</th><th>Value confidence</th><th>Source crop</th></tr></thead><tbody>{observations}</tbody></table></div>
<p>Original datum is provisionally identified as OD Liverpool; the tile margins do not verify it. Model conversion is (feet − 1.3) × 0.3048 to provisional ODN. Value confidence is separate from positional and surface-role uncertainty. Approximately 3 m picking uncertainty is allowed for manually located early evidence. Thirty-centimetre accuracy is a working aim, not a demonstrated bound.</p></main></body></html>'''
(ROOT/'docs/lower-lea-marsh-evidence.html').write_text(page)
print('Published early review, comparison map and later-surface inventory:',dict(counts),'matched',dict(matched))
