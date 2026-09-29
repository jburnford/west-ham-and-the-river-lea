import { createBridgeWalker } from './bridge-movement.js';

// A viewing envelope, not a historical pedestrian route. Flight has no collision detection.
export const districtBounds = { x: [-4500, 6700], z: [-5891, 6809], height: [2, 2400] };
export const districtViews = [
  { id: 'pumping-station', name: 'Abbey Mills — pumping station', position: [-250,45,75], target: [-183,15,-10], fov:62 },
  { id: 'west-ham-region', name: 'West Ham & surroundings — building plans', position: [800,2200,2800], target: [1000,0,-700], fov:70 },
  { id: 'forest-gate-plan', name: 'Forest Gate — building plans', position: [1400,500,-1450], target: [1600,0,-2350], fov:65 },
  { id: 'plaistow-plan', name: 'Plaistow & Canning Town — building plans', position: [1300,650,1200], target: [1900,0,2000], fov:65 },
  { id: 'woolwich-junction', name: 'Woolwich branch — main-line connection', position: [-150,160,-830], target: [-370,0,-1030], fov:65 },
  { id: 'western-industry', name: 'Old Lea — western industrial bank', position: [-1250,230,680], target: [-975,0,130], fov:62 },
  { id: 'bow-works', name: 'Bow brewery, safe works & foundry', position: [-970,100,400], target: [-955,0,205], fov:65 },
  { id: 'three-mills-west', name: 'Three Mills — west-bank works', position: [-560,120,600], target: [-715,0,405], fov:62 },
  { id: 'jute-housing', name: 'Biggerstaff & Preston — beside the jute mill', position: [-710,125,-490], target: [-535,0,-650], fov:60 },
  { id: 'gasworks-housing', name: 'Union & Stanley — gasworks housing', position: [-260,135,-210], target: [-430,0,-410], fov:60 },
  { id: 'livingstone-housing', name: 'Stanley & Livingstone — enclosed triangle', position: [-305,90,-220], target: [-430,0,-335], fov:60 },
  { id: 'gibbins-leet', name: 'Gibbins, Blyth & Leet — northern housing', position: [-670,170,-590], target: [-410,0,-845], fov:65 },
  { id: 'eastern-housing', name: 'Paul, Barnby & Hotham — enclosed blocks', position: [150,180,-480], target: [170,0,-760], fov:65 },
  { id: 'portway-housing', name: 'Portway & Montague — housing', position: [430,170,30], target: [420,0,-230], fov:65 },
  { id: 'western-housing', name: 'Western streets — housing and works', position: [-1040,145,690], target: [-920,0,440], fov:65 },
  { id: 'millmeads-blocks', name: 'Roberts, Beck & Lucas — housing blocks', position: [-578,58,-145], target: [-515,0,-196], fov:60 },
  { id: 'housing-street', name: 'Terraced street — ground level', position: [-561.397, 2, -207.244], target: [-540.821, 3, -225.178], fov:68 },
  { id: 'housing', name: 'Mill Meads — terraces and back yards', position: [-470,95,-100], target: [-450,0,-300], fov:60 },
  { id: 'northern-housing', name: 'Northern streets — terraced housing', position: [-360,145,-470], target: [-380,0,-750], fov:65 },
  { id: 'great-eastern', name: 'Great Eastern Railway — northern boundary', position: [-1150,155,-180], target: [-1000,5,-440], fov:64 },
  { id: 'ritchie-jute', name: 'Ritchie & Sons — jute mill', position: [-520,135,-590], target: [-640,2,-775], fov:62 },
  { id: 'marsh-ditches', name: 'Mill Meads — marsh and ditches', position: [-710,210,300], target: [-400,0,60], fov:60 },
  { id: 'sewer-high-street', name: 'Sewer and High Street', position: [-615,45,-320], target: [-557,3.5,-375], fov:60 },
  { id: 'wall-vista', name: 'Wall River — photograph study', position: [-625, 6, -262], target: [-638, 3, -105], fov: 48 },
  { id: 'high-street', name: 'High Street frontages', position: [-1020, 130, 190], target: [-825, 0, -50] },
  { id: 'city', name: 'City Mills / Howards and Sons', position: [-800, 150, -95], target: [-745, 0, -330] },
  { id: 'marshgate', name: 'Marshgate Lane', position: [-1050, 150, -170], target: [-881, 0, -335] },
  { id: 'sugar', name: 'Sugar House Lane', position: [-900, 160, 220], target: [-700, 0, -20] },
  { id: 'three-mills', name: 'Three Mills', position: [-666, 110, 555], target: [-527, 0, 401] },
  { id: 'old-lea', name: 'Old Lea works', position: [-1350, 180, 90], target: [-1107, 0, -175] },
  { id: 'sawmill-yard', name: 'New Imperial Saw Mills — timber yard', position: [-950, 150, 65], target: [-1100, 0, -85], fov:58 },
  { id: 'west-ham', name: 'West Ham Gas Works', position: [-417, 150, -82], target: [-214, 0, -345] },
  { id: 'bromley', name: 'Bromley-by-Bow gasworks', position: [-680, 250, 1100], target: [-309, 0, 800] },
  { id: 'abbey', name: 'Abbey Mills and Channelsea', position: [70, 110, 130], target: [-185, 0, -13] },
];

export function factoryViews(factories) {
  return factories.sites.map(site => {
    const points = factories.buildings.filter(b => b.siteId === site.id).flatMap(b => b.footprint);
    const xs = points.map(p => p[0]), zs = points.map(p => p[1]);
    const x = (Math.min(...xs) + Math.max(...xs)) / 2, z = (Math.min(...zs) + Math.max(...zs)) / 2;
    const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...zs) - Math.min(...zs));
    const distance = Math.max(65, span * .85);
    return { id: `factory-${site.id}`, name: site.name, position: [x - distance * .5, Math.min(300, distance), z + distance], target: [x, 0, z] };
  });
}

export function viewPose(position, target) {
  const [dx, dy, dz] = target.map((v, i) => v - position[i]);
  return { yaw: Math.atan2(dx, -dz) * 180 / Math.PI, pitch: Math.atan2(dy, Math.hypot(dx, dz)) * 180 / Math.PI, fov: 62 };
}

export function createDistrictNavigator(sewer) {
  const bridge = createBridgeWalker(sewer);
  let mode = 'bridge', position = bridge.world();
  const clamp = (n, [low, high]) => Math.max(low, Math.min(high, n));
  function flyTo(point) {
    mode = 'district';
    position = [clamp(point[0], districtBounds.x), clamp(point[1], districtBounds.height), clamp(point[2], districtBounds.z)];
  }
  return {
    get mode() { return mode; },
    flyTo,
    move(dx, dz, dy = 0) {
      if (mode === 'bridge') bridge.move(dx, dz);
      else flyTo([position[0] + dx, position[1] + dy, position[2] + dz]);
    },
    side(name) { mode = 'bridge'; bridge.side(name); },
    reset() { mode = 'bridge'; bridge.reset(); },
    world() { return mode === 'bridge' ? bridge.world() : [...position]; },
    corners: bridge.corners,
    snapshot() { return { ...bridge.snapshot(), mode, position: this.world(), bounds: districtBounds }; },
  };
}
