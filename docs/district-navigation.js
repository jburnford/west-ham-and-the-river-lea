import { createBridgeWalker } from './bridge-movement.js';

// A viewing envelope, not a historical pedestrian route. Flight has no collision detection.
export const districtBounds = { x: [-4500, 6700], z: [-5891, 6809], height: [2, 2400] };
export const districtViews = [
  {
    id: 'lower-lea-rivers',
    name: 'River system — Lea Bridge to the Thames',
    position: [1500, 2400, 3200],
    target: [-1250, 0, -600],
    fov: 78,
  },
  {
    id: 'lea-bridge-rivers',
    name: 'Lea Bridge — Old Lea and Hackney Cut',
    position: [-2500, 700, -2250],
    target: [-3200, 0, -3220],
    fov: 65,
  },
  {
    id: 'upper-channelsea-rivers',
    name: 'Upper Channelsea — Waterworks branches',
    position: [-650, 450, -1390],
    target: [-1275, 0, -2080],
    fov: 65,
  },
  {
    id: 'hackney-cut-rivers',
    name: 'Hackney Cut — Old Ford connections',
    position: [-1200, 650, -650],
    target: [-1830, 0, -1460],
    fov: 65,
  },
  {
    id: 'limehouse-cut-rivers',
    name: 'Limehouse Cut — navigation and Bow Creek',
    position: [-1200, 650, 2100],
    target: [-1150, 0, 1120],
    fov: 70,
  },
  {
    id: 'thames-mouth-rivers',
    name: 'Bow Creek — mouth at the Thames',
    position: [1500, 750, 3300],
    target: [440, 0, 2320],
    fov: 65,
  },
  {
    id: 'earth-river-banks',
    name: 'Earth banks — Old Lea',
    position: [-1790, 12, -2960],
    target: [-1830, 0, -3025],
    fov: 62,
  },
  {
    id: 'surveyed-marsh-banks',
    name: 'Marsh heights — north of the railway',
    position: [-1180, 110, -1320],
    target: [-1340, 1.8, -1500],
    fov: 60,
  },
  {
    id: 'surveyed-lea-banks',
    name: 'Bank heights — Old Lea margin',
    position: [-1240, 18, -1060],
    target: [-1305, 2, -1085],
    fov: 62,
  },
  {
    id: 'surveyed-pudding-banks',
    name: 'River fork — surveyed bank heights',
    position: [-1300, 36, -865],
    target: [-1390, 3, -945],
    fov: 62,
  },
  {
    id: 'knobshill-marsh-banks',
    name: 'Low marsh — opposite Knobshill Cottage',
    position: [-1480, 38, -855],
    target: [-1405, 1.5, -820],
    fov: 62,
  },
  {
    id: 'railway-marsh-banks',
    name: 'Railway foot — surveyed marsh ground',
    position: [-1450, 32, -1475],
    target: [-1460, 1.8, -1397],
    fov: 62,
  },
  {
    id: 'waterworks-margin-banks',
    name: 'Waterworks margin — surveyed river edge',
    position: [-1180, 25, -1660],
    target: [-1225, 2.3, -1700],
    fov: 62,
  },
  {
    id: 'waterworks-upper-banks',
    name: 'Upper Waterworks — surveyed bank',
    position: [-1170, 28, -1910],
    target: [-1250, 3.2, -1940],
    fov: 62,
  },
  {
    id: 'temple-mills-path-banks',
    name: 'Temple Mills — surveyed bank path',
    position: [-1250, 45, -2380],
    target: [-1340, 2.8, -2440],
    fov: 62,
  },
  {
    id: 'potters-ditch-banks',
    name: 'Potter’s Ditch — surveyed low ground',
    position: [-1350, 65, -2025],
    target: [-1230, 2.3, -2065],
    fov: 62,
  },
  {
    id: 'city-mill-ground-banks',
    name: 'City Mill River — bank and low ground',
    position: [-1380, 110, -930],
    target: [-1140, 1.7, -1080],
    fov: 62,
  },
  {
    id: 'hackney-canal-banks',
    name: 'Canal banks — Hackney Cut',
    position: [-2410, 10, -2550],
    target: [-2479, 0, -2603],
    fov: 62,
  },
  {
    id: 'limehouse-canal-banks',
    name: 'Brick canal edges — Limehouse Cut',
    position: [-1797, 5, 1797],
    target: [-1655, 0.5, 1695],
    fov: 62,
  },
  {
    id: 'channelsea-east',
    name: 'Channelsea — eastern works and market',
    position: [440, 360, 400],
    target: [15, 0, -210],
    fov: 65,
  },
  {
    id: 'stratford-railways',
    name: 'Stratford — northern railway connections',
    position: [-750, 560, -650],
    target: [-720, 0, -1110],
    fov: 70,
  },
  {
    id: 'pumping-station',
    name: 'Abbey Mills — pumping station',
    position: [-250, 45, 75],
    target: [-183, 15, -10],
    fov: 62,
  },
  {
    id: 'west-ham-region',
    name: 'West Ham & surroundings — building plans',
    position: [800, 2200, 2800],
    target: [1000, 0, -700],
    fov: 70,
  },
  {
    id: 'forest-gate-plan',
    name: 'Forest Gate — building plans',
    position: [1400, 500, -1450],
    target: [1600, 0, -2350],
    fov: 65,
  },
  {
    id: 'plaistow-plan',
    name: 'Plaistow & Canning Town — building plans',
    position: [1300, 650, 1200],
    target: [1900, 0, 2000],
    fov: 65,
  },
  {
    id: 'woolwich-junction',
    name: 'Woolwich branch — main-line connection',
    position: [-150, 160, -830],
    target: [-370, 0, -1030],
    fov: 65,
  },
  {
    id: 'western-industry',
    name: 'Old Lea — western industrial bank',
    position: [-1250, 230, 680],
    target: [-975, 0, 130],
    fov: 62,
  },
  {
    id: 'bow-works',
    name: 'Bow brewery, safe works & foundry',
    position: [-970, 100, 400],
    target: [-955, 0, 205],
    fov: 65,
  },
  {
    id: 'three-mills-west',
    name: 'Three Mills — west-bank works',
    position: [-560, 120, 600],
    target: [-715, 0, 405],
    fov: 62,
  },
  {
    id: 'jute-housing',
    name: 'Biggerstaff & Preston — beside the jute mill',
    position: [-710, 125, -490],
    target: [-535, 0, -650],
    fov: 60,
  },
  {
    id: 'gasworks-housing',
    name: 'Union & Stanley — gasworks housing',
    position: [-260, 135, -210],
    target: [-430, 0, -410],
    fov: 60,
  },
  {
    id: 'livingstone-housing',
    name: 'Stanley & Livingstone — enclosed triangle',
    position: [-305, 90, -220],
    target: [-430, 0, -335],
    fov: 60,
  },
  {
    id: 'gibbins-leet',
    name: 'Gibbins, Blyth & Leet — northern housing',
    position: [-670, 170, -590],
    target: [-410, 0, -845],
    fov: 65,
  },
  {
    id: 'eastern-housing',
    name: 'Paul, Barnby & Hotham — enclosed blocks',
    position: [150, 180, -480],
    target: [170, 0, -760],
    fov: 65,
  },
  {
    id: 'portway-housing',
    name: 'Portway & Montague — housing',
    position: [430, 170, 30],
    target: [420, 0, -230],
    fov: 65,
  },
  {
    id: 'western-housing',
    name: 'Western streets — housing and works',
    position: [-1040, 145, 690],
    target: [-920, 0, 440],
    fov: 65,
  },
  {
    id: 'millmeads-blocks',
    name: 'Roberts, Beck & Lucas — housing blocks',
    position: [-578, 58, -145],
    target: [-515, 0, -196],
    fov: 60,
  },
  {
    id: 'housing-street',
    name: 'Terraced street — ground level',
    position: [-561.397, 2, -207.244],
    target: [-540.821, 3, -225.178],
    fov: 68,
  },
  {
    id: 'housing',
    name: 'Mill Meads — terraces and back yards',
    position: [-470, 95, -100],
    target: [-450, 0, -300],
    fov: 60,
  },
  {
    id: 'northern-housing',
    name: 'Northern streets — terraced housing',
    position: [-360, 145, -470],
    target: [-380, 0, -750],
    fov: 65,
  },
  {
    id: 'great-eastern',
    name: 'Great Eastern Railway — northern boundary',
    position: [-1150, 155, -180],
    target: [-1000, 5, -440],
    fov: 64,
  },
  {
    id: 'ritchie-jute',
    name: 'Ritchie & Sons — jute mill',
    position: [-520, 135, -590],
    target: [-640, 2, -775],
    fov: 62,
  },
  {
    id: 'marsh-ditches',
    name: 'Mill Meads — marsh and ditches',
    position: [-710, 210, 300],
    target: [-400, 0, 60],
    fov: 60,
  },
  {
    id: 'sewer-high-street',
    name: 'Sewer and High Street',
    position: [-615, 45, -320],
    target: [-557, 3.5, -375],
    fov: 60,
  },
  {
    id: 'wall-vista',
    name: 'Wall River — photograph study',
    position: [-625, 6, -262],
    target: [-638, 3, -105],
    fov: 48,
  },
  { id: 'high-street', name: 'High Street frontages', position: [-1020, 130, 190], target: [-825, 0, -50] },
  { id: 'city', name: 'City Mills / Howards and Sons', position: [-800, 150, -95], target: [-745, 0, -330] },
  { id: 'marshgate', name: 'Marshgate Lane', position: [-1050, 150, -170], target: [-881, 0, -335] },
  { id: 'sugar', name: 'Sugar House Lane', position: [-900, 160, 220], target: [-700, 0, -20] },
  { id: 'three-mills', name: 'Three Mills', position: [-666, 110, 555], target: [-527, 0, 401] },
  { id: 'old-lea', name: 'Old Lea works', position: [-1350, 180, 90], target: [-1107, 0, -175] },
  {
    id: 'sawmill-yard',
    name: 'New Imperial Saw Mills — timber yard',
    position: [-950, 150, 65],
    target: [-1100, 0, -85],
    fov: 58,
  },
  { id: 'west-ham', name: 'West Ham Gas Works', position: [-417, 150, -82], target: [-214, 0, -345] },
  { id: 'bromley', name: 'Bromley-by-Bow gasworks', position: [-680, 250, 1100], target: [-309, 0, 800] },
  { id: 'abbey', name: 'Abbey Mills and Channelsea', position: [70, 110, 130], target: [-185, 0, -13] },
];

export function factoryViews(factories) {
  return factories.sites.map((site) => {
    const points = factories.buildings.filter((b) => b.siteId === site.id).flatMap((b) => b.footprint);
    const xs = points.map((p) => p[0]),
      zs = points.map((p) => p[1]);
    const x = (Math.min(...xs) + Math.max(...xs)) / 2,
      z = (Math.min(...zs) + Math.max(...zs)) / 2;
    const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...zs) - Math.min(...zs));
    const distance = Math.max(65, span * 0.85);
    return {
      id: `factory-${site.id}`,
      name: site.name,
      position: [x - distance * 0.5, Math.min(300, distance), z + distance],
      target: [x, 0, z],
    };
  });
}

export function viewPose(position, target) {
  const [dx, dy, dz] = target.map((v, i) => v - position[i]);
  return {
    yaw: (Math.atan2(dx, -dz) * 180) / Math.PI,
    pitch: (Math.atan2(dy, Math.hypot(dx, dz)) * 180) / Math.PI,
    fov: 62,
  };
}

export function createDistrictNavigator(sewer) {
  const bridge = createBridgeWalker(sewer);
  let mode = 'bridge',
    position = bridge.world();
  const clamp = (n, [low, high]) => Math.max(low, Math.min(high, n));
  function flyTo(point) {
    mode = 'district';
    position = [
      clamp(point[0], districtBounds.x),
      clamp(point[1], districtBounds.height),
      clamp(point[2], districtBounds.z),
    ];
  }
  return {
    get mode() {
      return mode;
    },
    flyTo,
    move(dx, dz, dy = 0) {
      if (mode === 'bridge') bridge.move(dx, dz);
      else flyTo([position[0] + dx, position[1] + dy, position[2] + dz]);
    },
    side(name) {
      mode = 'bridge';
      bridge.side(name);
    },
    reset() {
      mode = 'bridge';
      bridge.reset();
    },
    world() {
      return mode === 'bridge' ? bridge.world() : [...position];
    },
    corners: bridge.corners,
    snapshot() {
      return { ...bridge.snapshot(), mode, position: this.world(), bounds: districtBounds };
    },
  };
}
