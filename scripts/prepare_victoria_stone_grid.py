"""Save the independently inspected OS intersections of the open 20-cell grid."""
import json
from pathlib import Path

from PIL import Image, ImageDraw
from shapely.geometry import Polygon

from factory_map_sources import mosaic
from victoria_stone_grid import ROOT, REGISTER

BOUNDS = [-140, -395, 95, -235]
# Visible line intersections, inspected on the unmodified native OS tile.
# Rows run northwest to southeast; columns run southwest to northeast.
PIXELS = [
    [[335,224],[354,218],[373,211],[391,205],[410,198],[425,189]],
    [[341,240],[360,233],[378,226],[396,219],[415,212],[432,206]],
    [[348,256],[366,249],[384,243],[402,236],[421,229],[438,223]],
    [[354,272],[372,266],[391,259],[409,253],[427,246],[444,240]],
    [[359,287],[378,281],[396,274],[414,267],[432,261],[449,255]],
]
EVIDENCE = 'reference/footprint-model-alignment/victoria-stone-working-grid'


def build():
    canvas, world, _ = mosaic(BOUNDS)
    nodes = [world(row).round(3).tolist() for row in PIXELS]
    outline = (nodes[0] + [nodes[r][-1] for r in range(1, 5)] +
               list(reversed(nodes[-1][:-1])) + [nodes[r][0] for r in range(3, 0, -1)])
    cells = []
    for row in range(4):
        for col in range(5):
            ring = [nodes[row][col], nodes[row][col+1],
                    nodes[row+1][col+1], nodes[row+1][col]]
            cells.append(dict(id=f'victoria-stone-cell-{row+1}-{col+1}',
                              row=row, column=col, worldOutline=ring,
                              areaM2=Polygon(ring).area, open=True))
    dividers = []
    for row in range(5):
        for col in range(5):
            dividers.append(dict(id=f'victoria-stone-boundary-h-{row}-{col}',
                points=[nodes[row][col], nodes[row][col+1]], exterior=row in (0, 4)))
    for col in range(6):
        for row in range(4):
            dividers.append(dict(id=f'victoria-stone-boundary-v-{col}-{row}',
                points=[nodes[row][col], nodes[row+1][col]], exterior=col in (0, 5)))
    record = dict(id='victoria-stone-working-grid', siteId=9004, yardId=13013,
        name='Victoria Stone Works open working grid', source='os-1893',
        sourceFids=[], sourceGeometryKind='direct native OS line trace',
        register=REGISTER, reviewedSourceBounds=BOUNDS, reviewedSourcePixels=PIXELS,
        worldNodes=nodes, worldOutline=outline, areaM2=Polygon(outline).area,
        rows=4, columns=5, cells=cells, dividers=dividers,
        representation='ground-atlas-lines', lineWidth=.28, lineColour='#68645a',
        addedHeight=0, material='interpreted subdued stone/ground boundary colour',
        classification='Mapped open twenty-cell working grid; exact apparatus unresolved',
        planEvidence='Five columns and four rows of unshaded cells east of the diagonally hatched Victoria Stone western shed. Native wall/line crossings were inspected individually; the source building extract contains no polygon for the grid. Keep all interiors open and the neighbouring access lanes clear.',
        heightEvidence='No added elevation. Boundaries are drawn on the existing ground surface; apparatus height is not established by the OS plan.',
        appearanceEvidence='Line width and stone/ground colour are interpreted display choices, not measured wall thickness or identified construction material. No roof, enclosure, tank contents or exact production process is asserted.',
        evidenceImages=[EVIDENCE+'-raw.png', EVIDENCE+'-after.png'])
    (ROOT / REGISTER).write_text(json.dumps(record, indent=2)+'\n')
    raw = Image.fromarray(canvas).convert('RGB')
    raw.crop((318,175,466,304)).resize((888,774)).save(ROOT / (EVIDENCE+'-raw.png'))
    after = raw.copy(); draw = ImageDraw.Draw(after)
    for row in PIXELS:
        draw.line([tuple(p) for p in row], fill='#316893', width=1)
    for col in range(6):
        draw.line([tuple(row[col]) for row in PIXELS], fill='#316893', width=1)
    after.crop((318,175,466,304)).resize((888,774)).save(ROOT / (EVIDENCE+'-after.png'))
    print(f'Victoria Stone: 20 open cells, 49 unique boundaries, {record["areaM2"]:.2f} m², no elevation/roof.')


if __name__ == '__main__':
    build()
