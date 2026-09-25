import * as THREE from 'three';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const $ = (id) => document.getElementById(id);
const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xf7eff1, 0x635967, 2.5));
const key = new THREE.DirectionalLight(0xffffff, 3);
key.position.set(2, 4, 5);
scene.add(key);

const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
camera.position.set(0, 1, 4);
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas: $('canvas'), alpha: true, antialias: true });
  renderer.setClearColor(0x000000, 0);
} catch (error) {
  $('load').disabled = true;
  $('status').dataset.error = 'true';
  $('status').textContent = `WebGL unavailable; no import attempted: ${error.message}`;
  throw error;
}
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

let avatar = null;
let mixer = null;
let clips = [];
let morphs = new Map();
let objectUrls = [];
let report = null;
const clock = new THREE.Clock();

function resize() {
  const { width, height } = $('viewport').getBoundingClientRect();
  if (width < 1 || height < 1) return;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe($('viewport'));
resize();

function frame() {
  requestAnimationFrame(frame);
  if (mixer) mixer.update(Math.min(clock.getDelta(), 0.1));
  else clock.getDelta();
  controls.update();
  renderer.render(scene, camera);
  if (report && report.rendered_frame_observed === false && renderer.info.render.triangles > 0) {
    report.rendered_frame_observed = true; // A draw call, NOT proof of visual correctness.
    $('report').textContent = JSON.stringify(report, null, 2);
  }
}
requestAnimationFrame(frame);

function status(message, error = false) {
  $('status').dataset.error = String(error);
  $('status').textContent = message;
}
function basename(url) {
  let value = url;
  try { value = decodeURIComponent(url); } catch { /* Preserve undecodable references. */ }
  return value.replaceAll('\\', '/').split(/[?#]/)[0].split('/').at(-1).toLowerCase();
}
function resetCurrentModel() {
  if (avatar) scene.remove(avatar);
  if (mixer) mixer.stopAllAction();
  avatar = null;
  mixer = null;
  clips = [];
  morphs = new Map();
  for (const url of objectUrls) URL.revokeObjectURL(url);
  objectUrls = [];
  $('animation').replaceChildren(new Option('No clips imported', ''));
  $('morph').replaceChildren(new Option('No morph targets imported', ''));
  $('animation').disabled = $('morph').disabled = $('weight').disabled = true;
  $('weight').value = '0';
  report = null;
  window.__ff02Report = null; // Exposes only observations for local manual/automated checks.
}
function fitCamera(object) {
  const bounds = new THREE.Box3().setFromObject(object);
  if (bounds.isEmpty()) throw new Error('Importer returned no visible bounds.');
  const center = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  const span = Math.max(size.x, size.y, size.z, 0.01);
  const distance = (span / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)))) * 1.3;
  camera.near = Math.max(distance / 1000, 0.0001);
  camera.far = distance * 100;
  camera.position.set(center.x + distance * 0.2, center.y + distance * 0.08, center.z + distance);
  camera.lookAt(center);
  camera.updateProjectionMatrix();
  controls.target.copy(center);
  controls.update();
  return size.toArray().map(n => Number(n.toFixed(4)));
}
function inspect(object, asset, unresolved) {
  const bones = new Set();
  const materials = new Set();
  let meshes = 0, skinned = 0, textureReferences = 0;
  object.traverse(node => {
    if (node.isBone) bones.add(node.name || '(unnamed)');
    if (!node.isMesh) return;
    meshes++;
    if (node.isSkinnedMesh) skinned++;
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
      if (!material || materials.has(material)) continue;
      materials.add(material);
      for (const value of Object.values(material)) if (value?.isTexture) textureReferences++;
    }
    for (const [name, index] of Object.entries(node.morphTargetDictionary || {})) {
      const list = morphs.get(name) || [];
      list.push({ node, index });
      morphs.set(name, list);
    }
  });
  const bounds = fitCamera(object);
  return {
    importer: `Three.js FBXLoader r${THREE.REVISION}`,
    asset_name: asset.name,
    asset_bytes: asset.size,
    import_status: 'parsed',
    imported_meshes: meshes,
    imported_skinned_meshes: skinned,
    imported_bone_names: [...bones].sort(),
    imported_materials: materials.size,
    imported_texture_references: textureReferences,
    unresolved_texture_requests: [...unresolved].sort(),
    imported_morph_names: [...morphs.keys()].sort(),
    imported_clips: clips.map(clip => ({ name: clip.name, duration_s: Number(clip.duration.toFixed(3)), tracks: clip.tracks.length })),
    bounds_xyz_import_units: bounds,
    rendered_frame_observed: false,
    note: 'Parse/draw evidence only. Humanoid mapping, pose quality, texture fidelity, facial/eye control, physics, FPS and Wayland overlay still need separate tests.'
  };
}

$('load').addEventListener('click', async () => {
  const model = $('model').files[0];
  if (!model || !model.name.toLowerCase().endsWith('.fbx')) return status('Select an FBX file first.', true);
  if (model.size > 128 * 1024 * 1024) return status('Model exceeds the 128 MiB inspection limit.', true);
  $('load').disabled = true;
  resetCurrentModel();
  status('Importing from local files…');
  try {
    const textureFiles = [...$('textures').files];
    if (textureFiles.length > 128 || textureFiles.reduce((n, f) => n + f.size, 0) > 256 * 1024 * 1024) {
      throw new Error('Too many or too-large textures for this probe.');
    }
    const textures = new Map(textureFiles.map(file => [file.name.toLowerCase(), file]));
    const unresolved = new Set();
    const manager = new THREE.LoadingManager();
    manager.setURLModifier(url => {
      if (url.startsWith('blob:') || url.startsWith('data:')) return url; // Embedded FBX texture.
      const name = basename(url);
      const file = textures.get(name);
      if (file) {
        const objectUrl = URL.createObjectURL(file);
        objectUrls.push(objectUrl);
        return objectUrl;
      }
      unresolved.add(name || '(unnamed)');
      // Never fetch paths/URLs found inside an untrusted model from the network.
      // A placeholder allows geometry inspection; the missing image is not a PASS.
      return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/BBkAAAAASUVORK5CYII=';
    });
    manager.onError = url => {
      unresolved.add(basename(url));
      // Image decoding is asynchronous; do not leave a stale "no missing textures"
      // report when an image fails after FBXLoader.parse() has returned.
      if (report && report.asset_name === model.name) {
        report.unresolved_texture_requests = [...unresolved].sort();
        $('report').textContent = JSON.stringify(report, null, 2);
        status('Parsed, but at least one texture failed to load. Material correctness is UNKNOWN.', true);
      }
    };
    const buffer = await model.arrayBuffer();
    const imported = new FBXLoader(manager).parse(buffer, './');
    avatar = imported;
    clips = imported.animations || [];
    mixer = new THREE.AnimationMixer(avatar);
    const observations = inspect(avatar, model, unresolved);
    scene.add(avatar);
    if (clips.length) {
      $('animation').replaceChildren(new Option('Rest pose (no playback)', ''), ...clips.map((clip, i) => new Option(clip.name || `Clip ${i}`, String(i))));
      $('animation').disabled = false;
    }
    if (morphs.size) {
      $('morph').replaceChildren(new Option('Choose a channel', ''), ...[...morphs.keys()].sort().map(name => new Option(name, name)));
      $('morph').disabled = false;
    }
    report = observations;
    window.__ff02Report = report;
    $('report').textContent = JSON.stringify(report, null, 2);
    status(unresolved.size
      ? `Parsed, but ${unresolved.size} texture references are unresolved. Materials are NOT validated; see the report.`
      : 'Parsed locally. Orbit and inspect visually; copy observations to the FF-02 checklist.',
    unresolved.size > 0);
  } catch (error) {
    resetCurrentModel();
    status(`Import failed: ${error.message}`, true);
    $('report').textContent = 'FAIL — importer threw an error. See browser console for details; verify on target machine before blaming the asset.';
    console.error('FF-02 import error', error);
  } finally {
    $('load').disabled = false;
  }
});
$('animation').addEventListener('change', () => {
  mixer.stopAllAction();
  if ($('animation').value !== '') mixer.clipAction(clips[Number($('animation').value)]).reset().play();
});
$('morph').addEventListener('change', () => {
  for (const entries of morphs.values()) {
    for (const { node, index } of entries) node.morphTargetInfluences[index] = 0;
  }
  $('weight').value = '0';
  $('weight').disabled = !$('morph').value;
});
$('weight').addEventListener('input', () => {
  for (const { node, index } of morphs.get($('morph').value) || []) node.morphTargetInfluences[index] = Number($('weight').value);
});
