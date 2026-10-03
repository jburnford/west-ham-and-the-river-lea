// An optional, deterministic film of the actual reconstruction. No new scene assets.
// Times are seconds; positions use the scene's local metres (x east, z south).
export const duration = 56;
export const chapters = [
  {
    start: 0,
    end: 7,
    label: 'WEST HAM · ABOUT 1900',
    title: 'Above the\nChannelsea',
    text: 'A walk above London’s sewage.\nAn industrial world on either side.',
    source: 'Opening: Northern Outfall Sewer; book chapter 3.',
    from: [8, 18, 8],
    to: [3, 20, 30],
    target: [-25, 8, 210],
    fov: 36,
    narration: 'West Ham, around nineteen hundred. A public walk ran above the Northern Outfall Sewer.',
  },
  {
    start: 7,
    end: 14,
    label: '01 / THE WORKING RIVER',
    title: 'A river at work',
    text: 'Barges carried supplies to riverside works, linking local jobs to the needs of a much larger city.',
    source: 'Website: The working river; book figure 4.',
    from: [3, 20, 30],
    to: [-5, 21, 50],
    target: [-20, 6, 230],
    fov: 34,
    narration:
      'Below, barges carried supplies along the Channelsea to riverside factories, linking local work to London.',
  },
  {
    start: 14,
    end: 21,
    label: '02 / BROMLEY GASWORKS',
    title: 'Fuel for the city',
    text: 'Gas holders stored fuel for homes and workplaces. Employment and environmental costs stood close together.',
    source: 'Website: Making gas; Bromley holder plan and listings.',
    from: [-5, 21, 50],
    to: [-10, 24, 80],
    target: [-285, 16, 590],
    fov: 25,
    narration:
      'Bromley’s gas holders stored fuel for homes and workplaces. Industry brought jobs, and environmental costs.',
  },
  {
    start: 21,
    end: 28,
    label: '03 / ABBEY MILLS',
    title: 'Where the\nsewage went',
    text: 'The pumping station lifted sewage into London’s higher-level drainage system. A public walk ran above the sewer.',
    source: 'Website: London’s sewage; book chapter 3.',
    from: [-10, 24, 80],
    to: [5, 22, 35],
    target: [-185, 21, -13],
    fov: 34,
    narration: 'At Abbey Mills, the pumping station lifted sewage into the higher levels of London’s drainage system.',
  },
  {
    start: 28,
    end: 35,
    label: '04 / HOMES & GASWORKS',
    title: 'Living beside\nthe works',
    text: 'Abbey Lane’s houses stood near West Ham Gas Works. Homes, industry and the sewer shared a small area.',
    source: 'Website: Homes & gasworks; OS VIII.32 and VIII.22.',
    from: [5, 22, 35],
    to: [15, 24, 10],
    target: [-140, 10, -170],
    fov: 32,
    narration:
      'Nearby, Abbey Lane’s houses stood beside West Ham Gas Works. Homes, industry and waste shared this landscape.',
  },
  {
    start: 35,
    end: 42,
    label: '05 / THE NORTHERN STREETS',
    title: 'A place to live',
    text: 'Rows of houses spread beyond the railway goods yard. This industrial district was also a densely inhabited neighbourhood.',
    source: 'Website: The northern streets; OS VIII.22 and map mosaic.',
    from: [15, 24, 10],
    to: [25, 22, -10],
    target: [100, 8, -390],
    fov: 25,
    narration: 'Beyond the railway, long rows of houses remind us that this was also a place to live.',
  },
  {
    start: 42,
    end: 49,
    label: '06 / ABBEY MILL',
    title: 'An older\nworking river',
    text: 'The map names Abbey Mill as a corn mill. Milling belonged to the river’s history long before the gasworks and pumping station.',
    source: 'Website: The corn mill; OS VIII.32; book figure 1.',
    from: [25, 22, -10],
    to: [30, 18, 15],
    target: [-12, 7, -58],
    fov: 38,
    narration: 'And Abbey Mill recalls an older working river, long before the gasworks and the pumping station.',
  },
  {
    start: 49,
    end: 56,
    label: 'EXPLORE THE LANDSCAPE',
    title: 'West Ham and\nthe River Lea',
    text: 'A public history project by Jim Clifford.\nExplore the scene and its stories.',
    source: 'Project credit and website.',
    from: [30, 18, 15],
    to: [25, 21, 30],
    target: [-165, 18, -20],
    fov: 38,
    narration: 'Explore West Ham and the River Lea. A public history project by Jim Clifford.',
  },
];

const smooth = (t) => t * t * (3 - 2 * t);
const mix = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);

export function sample(time) {
  const t = Math.max(0, Math.min(duration, time));
  const index = Math.min(chapters.length - 1, Math.floor(t / 7));
  const chapter = chapters[index],
    local = t - chapter.start;
  // Ease changes of view over three seconds; the camera drifts throughout each shot.
  const previous = chapters[Math.max(0, index - 1)];
  return {
    time: t,
    index,
    chapter,
    position: mix(chapter.from, chapter.to, smooth(local / 7)),
    target: mix(previous.target, chapter.target, smooth(Math.min(1, local / 3))),
    fov: previous.fov + (chapter.fov - previous.fov) * smooth(Math.min(1, local / 3)),
    opacity: Math.min(1, index === 0 ? 1 : local / 0.6, index === chapters.length - 1 ? 1 : (7 - local) / 0.5),
  };
}

export async function installFilm({ THREE, renderer, scene, surfaces, stop }) {
  await Promise.all([
    document.fonts.load('400 64px "Libre Caslon Text"'),
    document.fonts.load('500 32px "Archivo"'),
    document.fonts.load('600 24px "Archivo"'),
  ]);
  stop();
  const canvas = document.createElement('canvas');
  canvas.id = 'social-film';
  canvas.width = innerWidth;
  canvas.height = innerHeight;
  canvas.style.cssText =
    'position:fixed;inset:0;width:100vw;height:100vh;z-index:1000;object-fit:contain;background:#0f1716;cursor:pointer';
  canvas.setAttribute('role', 'img');
  canvas.tabIndex = 0;
  document.body.append(canvas);
  document.body.style.overflow = 'hidden';
  const ctx = canvas.getContext('2d', { alpha: false });
  const camera = new THREE.PerspectiveCamera(52, canvas.width / canvas.height, 0.15, 3200);
  const w = canvas.width,
    h = canvas.height,
    portrait = h > w;
  const unit = portrait ? w / 1080 : h / 1080;
  const margin = (portrait ? 85 : 90) * unit;
  const textWidth = portrait ? w - 2 * margin - 30 * unit : w * 0.63;
  const lines = (text, size, family, weight = 400) => {
    ctx.font = `${weight} ${size * unit}px "${family}"`;
    return text.split('\n').flatMap((paragraph) => {
      const result = [];
      let line = '';
      for (const word of paragraph.split(' ')) {
        const next = line ? `${line} ${word}` : word;
        if (line && ctx.measureText(next).width > textWidth) {
          result.push(line);
          line = word;
        } else line = next;
      }
      result.push(line);
      return result;
    });
  };
  const drawText = (text, y, size, family, colour, weight = 400, leading = 1.25) => {
    const wrapped = lines(text, size, family, weight);
    ctx.fillStyle = colour;
    for (const line of wrapped) {
      ctx.fillText(line, margin, y);
      y += size * unit * leading;
    }
    return y;
  };
  let currentTime = 0,
    animation = 0,
    started = 0;
  function render(time) {
    const shot = sample(time);
    currentTime = shot.time;
    if (renderer.getContext().isContextLost()) throw new Error('WebGL context lost during film render');
    camera.position.fromArray(shot.position);
    camera.fov = shot.fov;
    camera.updateProjectionMatrix();
    camera.lookAt(new THREE.Vector3(...shot.target));
    surfaces?.reflect(camera);
    renderer.render(scene, camera);
    ctx.globalAlpha = 1;
    ctx.drawImage(renderer.domElement, 0, 0, w, h);
    const gradient = ctx.createLinearGradient(0, h * (portrait ? 0.4 : 0.62), 0, h);
    gradient.addColorStop(0, 'rgba(10,18,17,0)');
    gradient.addColorStop(0.53, 'rgba(10,18,17,.78)');
    gradient.addColorStop(1, 'rgba(10,18,17,.98)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, w, h);
    const top = ctx.createLinearGradient(0, 0, 0, h * 0.23);
    top.addColorStop(0, 'rgba(10,18,17,.65)');
    top.addColorStop(1, 'rgba(10,18,17,0)');
    ctx.fillStyle = top;
    ctx.fillRect(0, 0, w, h * 0.23);
    ctx.textBaseline = 'top';
    drawText('WEST HAM / c.1900', h * 0.075, 24, 'Archivo', '#f2ede1', 600);
    drawText('A reconstruction in progress', h * 0.075 + 37 * unit, 21, 'Archivo', '#d2d8d0');
    ctx.globalAlpha = Math.max(0, shot.opacity);
    let y = portrait ? h * 0.625 : h * 0.77;
    ctx.fillStyle = '#d6a54d';
    ctx.fillRect(margin, y - 27 * unit, 66 * unit, 3 * unit);
    y = drawText(shot.chapter.label, y, 23, 'Archivo', '#e9c176', 600) + 24 * unit;
    y =
      drawText(
        portrait ? shot.chapter.title : shot.chapter.title.replaceAll('\n', ' '),
        y,
        portrait ? 67 : 50,
        'Libre Caslon Text',
        '#f2ede1',
        400,
        1.08
      ) +
      18 * unit;
    // The narrated landscape edition keeps only the chapter title on screen.
    if (portrait) y = drawText(shot.chapter.text, y, 32, 'Archivo', '#f2ede1', 400, 1.4);
    if (shot.index === chapters.length - 1) {
      drawText(
        'jimclifford.ca/west-ham-and-the-river-lea/',
        y + (portrait ? 24 : 0) * unit,
        portrait ? 22 : 24,
        'Archivo',
        '#e9c176',
        500
      );
    }
    ctx.globalAlpha = 1;
    canvas.setAttribute(
      'aria-label',
      `${shot.chapter.title.replaceAll('\n', ' ')}. ${shot.chapter.text} Click or press Space to play or pause.`
    );
    return { time: shot.time, chapter: shot.index, position: shot.position, target: shot.target };
  }
  function pause() {
    cancelAnimationFrame(animation);
    animation = 0;
  }
  function play() {
    pause();
    if (currentTime >= duration - 0.05) currentTime = 0;
    started = performance.now() - currentTime * 1000;
    const tick = (now) => {
      render(Math.min(duration - 0.001, (now - started) / 1000));
      if (now - started < duration * 1000) animation = requestAnimationFrame(tick);
      else animation = 0;
    };
    animation = requestAnimationFrame(tick);
  }
  const toggle = () => (animation ? pause() : play());
  canvas.addEventListener('click', toggle);
  canvas.addEventListener('keydown', (event) => {
    if (event.code === 'Space') {
      event.preventDefault();
      toggle();
    }
    if (event.code === 'Home') {
      pause();
      render(0);
    }
  });
  window.socialFilm = {
    duration,
    chapters,
    render,
    play,
    pause,
    frame(time) {
      pause();
      render(time);
      return canvas.toDataURL('image/jpeg', 0.94);
    },
  };
  render(0.8);
  if (!new URLSearchParams(location.search).has('capture') && !matchMedia('(prefers-reduced-motion: reduce)').matches)
    play();
}
