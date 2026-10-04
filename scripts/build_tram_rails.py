"""Copy the High Street horse-tramway register into docs/data for the page.

The rail geometry itself is built in the browser by docs/tram-rails.js from the
High Street route in docs/data/infrastructure.json, so the rails follow any later
road retrace. This step only validates the register against that data and
publishes it:

    python3 scripts/build_tram_rails.py
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/maps/high-street-tramway.json'
OUT = ROOT / 'docs/data/tram-rails.json'


def main():
    raw = SOURCE.read_bytes()
    register = json.loads(raw)
    infra = json.loads((ROOT / 'docs/data/infrastructure.json').read_text())
    roads = {r['name'] for r in infra['roads']}
    bridges = {b.get('id') for b in infra['roadBridges']}
    missing = [n for n in register['route']['roads'] if n not in roads]
    assert not missing, f'High Street roads missing from infrastructure.json: {missing}'
    missing = [b for b in register['route']['followsBridgeDecks'] if b not in bridges]
    assert not missing, f'High Street bridges missing from infrastructure.json: {missing}'
    track, rail = register['track'], register['rail']
    assert track['form'] in ('single', 'double')
    assert abs(track['gaugeMetres'] - 1.435) < 1e-9, 'Standard gauge expected'
    if track['form'] == 'double':
        assert track['trackCentreSpacingMetres'] > track['gaugeMetres'] + 2 * rail['headWidthMetres']
    assert 0.005 <= rail['headAboveSettsMetres'] <= 0.01, 'Rail head 5-10 mm above the setts'
    for record in (register['operation'], track, rail, register['route']):
        assert record.get('evidence'), 'Every record needs an evidence string'
    for source in register['sources']:
        assert source['path'] and source['note']
    out = {
        **register,
        'register': str(SOURCE.relative_to(ROOT)),
        'registerSha256': hashlib.sha256(raw).hexdigest(),
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(
        f"Tram rails: {track['form']} track, gauge {track['gaugeMetres']} m, "
        f"{len(register['route']['roads'])} roads, {len(register['route']['followsBridgeDecks'])} bridge decks "
        f'-> {OUT.relative_to(ROOT)}'
    )


if __name__ == '__main__':
    main()
