let scene, camera, renderer, controls, terrainMesh, clock;
const container = document.getElementById('canvas-container');

function init() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0d14);
  
  camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 5000);
  camera.position.set(0, -180, 140);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);

  clock = new THREE.Clock();

  // Fly Controls
  controls = new THREE.FlyControls(camera, renderer.domElement);
  controls.movementSpeed = 60;
  controls.domElement = renderer.domElement;
  controls.rollSpeed = Math.PI / 6;
  controls.autoForward = false;
  controls.dragToLook = true;

  // Lights
  const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
  dirLight.position.set(100, 150, 200);
  scene.add(dirLight);
  scene.add(new THREE.AmbientLight(0x555555));

  window.addEventListener('resize', onWindowResize);
  animate();
}

function buildTerrain(textureUrl, heightmapUrl, scaleFactor = 35.0) {
  if (terrainMesh) scene.remove(terrainMesh);

  const loader = new THREE.TextureLoader();
  loader.load(textureUrl, (opticalTex) => {
    loader.load(heightmapUrl, (depthTex) => {
      // 256x256 vertex subdivision grid
      const geometry = new THREE.PlaneGeometry(200, 200, 256, 256);
      const material = new THREE.MeshStandardMaterial({
        map: opticalTex,
        displacementMap: depthTex,
        displacementScale: scaleFactor,
        roughness: 0.8,
        metalness: 0.1
      });

      terrainMesh = new THREE.Mesh(geometry, material);
      terrainMesh.rotation.x = 0; // Natural nadir orientation
      scene.add(terrainMesh);
    });
  });
}

// Raycaster Height Probe
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

window.addEventListener('mousemove', (event) => {
  if (!terrainMesh) return;
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
  
  raycaster.setFromCamera(mouse, camera);
  const intersects = raycaster.intersectObject(terrainMesh);
  if (intersects.length > 0) {
    const point = intersects[0].point;
    // Map Z elevation back to estimated physical meters
    document.getElementById('probeElevation').innerText = (point.z * 1.5 + 350).toFixed(2) + " m";
  }
});

// Upload & Backend Trigger
document.getElementById('imageInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);
  
  document.getElementById('modeDisplay').innerText = "Processing...";
  const res = await fetch('http://localhost:8000/api/process', { method: 'POST', body: formData });
  const data = await res.json();

  document.getElementById('modeDisplay').innerText = data.metrics.mode;
  buildTerrain(
    `http://localhost:8000${data.texture_url}`,
    `http://localhost:8000${data.heightmap_url}`,
    data.is_georeferenced ? 45.0 : 25.0
  );
});

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  controls.update(delta);
  renderer.render(scene, camera);
}

init();