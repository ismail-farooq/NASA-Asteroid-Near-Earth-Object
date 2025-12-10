// ******  SETUP  ******
console.log("Create the scene");
const scene = new THREE.Scene();

console.log("Create a perspective projection camera");
var camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(201, 47, -130);

console.log("Create the renderer");
const renderer = new THREE.WebGLRenderer({ 
    antialias: true,
    powerPreference: "high-performance"
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1;

console.log("Create an orbit control");
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.75;
controls.screenSpacePanning = false;

console.log("Set up texture loader");
const cubeTextureLoader = new THREE.CubeTextureLoader();
const loadTexture = new THREE.TextureLoader();

// Set crossOrigin for textures if needed
loadTexture.crossOrigin = "anonymous";

// ****** LIGHTING FIXES ******
console.log("Add the ambient light");
// Increased ambient light
var lightAmbient = new THREE.AmbientLight(0x444444, 2); 
scene.add(lightAmbient);

// Add directional light for better illumination
const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(50, 50, 50);
scene.add(directionalLight);



// ******  Star background  ******
console.log("Loading background...");
scene.background = cubeTextureLoader.load([
    STATIC_URL + 'images/3.jpg',
    STATIC_URL + 'images/3.jpg',
    STATIC_URL + 'images/3.jpg',
    STATIC_URL + 'images/2.jpg',
    STATIC_URL + 'images/4.jpg',
    STATIC_URL + 'images/2.jpg'
], 
function() {
    console.log("Background loaded successfully");
},
function() {
    console.log("Background loading in progress");
},
function(error) {
    console.error("Error loading background:", error);
});

// ******  POSTPROCESSING setup ******
const composer = new EffectComposer(renderer);
const renderPass = new RenderPass(scene, camera);
composer.addPass(renderPass);

// ******  OUTLINE PASS  ******
const outlinePass = new OutlinePass(new THREE.Vector2(window.innerWidth, window.innerHeight), scene, camera);
outlinePass.edgeStrength = 3;
outlinePass.edgeGlow = 1;
outlinePass.visibleEdgeColor.set(0xffffff);
outlinePass.hiddenEdgeColor.set(0x190a05);
composer.addPass(outlinePass);

// ******  BLOOM PASS  ******
const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
bloomPass.threshold = 0.8; // Lowered threshold
bloomPass.strength = 1.5;  // Increased strength
bloomPass.radius = 0.9;
composer.addPass(bloomPass);

// ******  CONTROLS  ******
const gui = new dat.GUI({ autoPlace: false });
const customContainer = document.getElementById('gui-container');
customContainer.appendChild(gui.domElement);

// ****** SETTINGS FOR INTERACTIVE CONTROLS  ******
const settings = {
    accelerationOrbit: 1,
    acceleration: 1,
};

gui.add(settings, 'accelerationOrbit', 0, 10).name('Orbit Speed');


// mouse movement
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function onMouseMove(event) {
    event.preventDefault();
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = - (event.clientY / window.innerHeight) * 2 + 1;
}

// ******  SELECT PLANET  ******
let selectedPlanet = null;
let isMovingTowardsPlanet = false;
let targetCameraPosition = new THREE.Vector3();
let isZoomingOut = false;
let zoomOutTargetPosition = new THREE.Vector3(-175, 115, 5);

// close 'x' button function
function closeInfo() {
    var info = document.getElementById('planetInfo');
    info.style.display = 'none';
    settings.accelerationOrbit = 1;
    isZoomingOut = true;
    controls.target.set(0, 0, 0);
}
window.closeInfo = closeInfo;

// ******  SUN  ******
let sunMat;
console.log("Creating sun...");

const sunSize = 697/40;
const sunGeom = new THREE.SphereGeometry(sunSize, 64, 32);
sunMat = new THREE.MeshBasicMaterial({
    map: loadTexture.load(STATIC_URL + 'images/sun.jpg', 
        function() { console.log("Sun texture loaded"); },
        undefined,
        function(err) { console.error("Error loading sun texture:", err); }
    ),
    emissive: 0xFFF88F,
    emissiveIntensity: settings.sunIntensity
});
const sun = new THREE.Mesh(sunGeom, sunMat);
scene.add(sun);

// Point light in the sun - INCREASED INTENSITY
const pointLight = new THREE.PointLight(0xFDFFD3, 1200, 1000, 2);
pointLight.position.copy(sun.position);
//scene.add(pointLight);

// Add point light helper for debugging
// const lightHelper = new THREE.PointLightHelper(pointLight, 10);
// scene.add(lightHelper);

// ******  PLANET CREATION FUNCTION  ******
function createPlanet(planetName, size, position, tilt, texture, bump, ring, atmosphere, moons) {
    console.log(`Creating planet: ${planetName}`);

    let material;
    if (texture instanceof THREE.Material) {
        material = texture;
    } else if (bump) {
        material = new THREE.MeshStandardMaterial({
            map: loadTexture.load(texture),
            bumpMap: loadTexture.load(bump),
            bumpScale: 0.7,
            roughness: 0.8,
            metalness: 0.2
        });
    } else {
        material = new THREE.MeshStandardMaterial({
            map: loadTexture.load(texture),
            roughness: 0.8,
            metalness: 0.2
        });
    }

    const name = planetName;
    const geometry = new THREE.SphereGeometry(size, 64, 32);
    const planet = new THREE.Mesh(geometry, material);
    const planet3d = new THREE.Object3D();
    const planetSystem = new THREE.Group();
    planetSystem.add(planet);
    
    let Atmosphere;
    let Ring;
    
    planet.position.x = position;
    planet.rotation.z = tilt * Math.PI / 180;

    // add orbit path - INCREASED OPACITY
    const orbitPath = new THREE.EllipseCurve(
        0, 0,
        position, position,
        0, 2 * Math.PI,
        false,
        0
    );

    const pathPoints = orbitPath.getPoints(100);
    const orbitGeometry = new THREE.BufferGeometry().setFromPoints(pathPoints);
    const orbitMaterial = new THREE.LineBasicMaterial({ 
        color: 0xFFFFFF, 
        transparent: true, 
        opacity: 0.3 // Increased opacity
    });
    const orbit = new THREE.LineLoop(orbitGeometry, orbitMaterial);
    orbit.rotation.x = Math.PI / 2;
    planetSystem.add(orbit);

    // add ring
    if (ring) {
        const RingGeo = new THREE.RingGeometry(ring.innerRadius, ring.outerRadius, 32);
        const RingMat = new THREE.MeshStandardMaterial({
            map: loadTexture.load(ring.texture),
            side: THREE.DoubleSide,
            transparent: true
        });
        Ring = new THREE.Mesh(RingGeo, RingMat);
        planetSystem.add(Ring);
        Ring.position.x = position;
        Ring.rotation.x = -0.5 * Math.PI;
        Ring.rotation.y = -tilt * Math.PI / 180;
    }

    // add atmosphere
    if (atmosphere) {
        const atmosphereGeom = new THREE.SphereGeometry(size + 0.1, 64, 32);
        const atmosphereMaterial = new THREE.MeshPhongMaterial({
            map: loadTexture.load(atmosphere),
            transparent: true,
            opacity: 0.6, // Increased opacity
            side: THREE.FrontSide
        });
        Atmosphere = new THREE.Mesh(atmosphereGeom, atmosphereMaterial);
        Atmosphere.rotation.z = 0.41;
        planet.add(Atmosphere);
    }

    // add moons
        // add moons (FIXED VERSION)
    if (moons) {
        moons.forEach(moon => {
            let moonMaterial;
            if (moon.bump) {
                moonMaterial = new THREE.MeshStandardMaterial({
                    map: loadTexture.load(moon.texture),
                    bumpMap: loadTexture.load(moon.bump),
                    bumpScale: 0.5,
                    roughness: 0.8,
                    metalness: 0.2
                });
            } else {
                moonMaterial = new THREE.MeshStandardMaterial({
                    map: loadTexture.load(moon.texture),
                    roughness: 0.8,
                    metalness: 0.2
                });
            }
            
            const moonGeometry = new THREE.SphereGeometry(moon.size, 32, 16);
            const moonMesh = new THREE.Mesh(moonGeometry, moonMaterial);
            
            // Store moon orbit data
            moon.mesh = moonMesh;
            moon.orbitAngle = Math.random() * Math.PI * 2; // Random start position
            moon.orbitRadius = moon.orbitRadius || size * 2.5;
            
            // Add moon to planet system (NOT directly to planet)
            planetSystem.add(moonMesh);
            
            console.log(`Moon created for ${planetName}, orbit radius: ${moon.orbitRadius}`);
        });
    }

    planet3d.add(planetSystem);
    scene.add(planet3d);
    
    console.log(`Planet ${planetName} created successfully`);
    return { name, planet, planet3d, Atmosphere, moons, planetSystem, Ring };
}

// Earth day/night effect shader material
// ******  EARTH CREATION (FIXED)  ******
console.log("Creating Earth material...");

// Preload textures first
const earthDayTexture = loadTexture.load(STATIC_URL + 'images/earth_daymap.jpg');
const earthNightTexture = loadTexture.load(STATIC_URL + 'images/earth_nightmap.jpg');

// Create Earth with proper material loading
const earthMaterial = new THREE.ShaderMaterial({
    uniforms: {
        dayTexture: { value: earthDayTexture },
        nightTexture: { value: earthNightTexture },
        sunPosition: { value: sun.position }
    },
    vertexShader: `
        varying vec3 vNormal;
        varying vec2 vUv;
        varying vec3 vSunDirection;
        uniform vec3 sunPosition;
        void main() {
            vUv = uv;
            vec4 worldPosition = modelMatrix * vec4(position, 1.0);
            vNormal = normalize(normalMatrix * normal);
            vSunDirection = normalize(sunPosition - worldPosition.xyz);
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    fragmentShader: `
        uniform sampler2D dayTexture;
        uniform sampler2D nightTexture;
        varying vec3 vNormal;
        varying vec2 vUv;
        varying vec3 vSunDirection;
        void main() {
            float intensity = max(dot(vNormal, vSunDirection), 0.0);
            vec4 dayColor = texture2D(dayTexture, vUv);
            vec4 nightColor = texture2D(nightTexture, vUv);
            // Enhanced day/night transition
            gl_FragColor = mix(nightColor * 0.6, dayColor, intensity * 1.2);
        }
    `
});

// Alternative: Use standard material if shader fails
const earthFallbackMaterial = new THREE.MeshStandardMaterial({
    map: earthDayTexture,
    roughness: 0.8,
    metalness: 0.2,
    bumpScale: 0.05
});

// ******  MOONS  ******
// ******  MOONS (FIXED)  ******
// ******  MOONS (FIXED)  ******
const earthMoon = [{
    size: 1.6,
    texture: STATIC_URL + 'images/moonmap.jpg',
    bump: STATIC_URL + 'images/moonbump.jpg',
    orbitSpeed: 0.02, // Increased speed for better visibility
    orbitRadius: 20, // Increased distance from Earth
    name: 'Moon'
}];

// ******  PLANET CREATIONS (UPDATED)  ******
console.log("Creating Earth...");
const earth = createPlanet(
    'Earth', 
    6.4, 
    90, 
    23, 
    earthMaterial, 
    null, 
    null, 
    STATIC_URL + 'images/earth_atmosphere.jpg', 
    earthMoon
);


// ******  ASTEROID ORBITS  ******

console.log("Loading asteroid data...");

// Fetch asteroid JSON
fetch('/api/asteroid')
  .then(response => {
    if (!response.ok) {
      throw new Error(`Failed to load asteroid.json: ${response.status} ${response.statusText}`);
    }
    return response.json();
  })
  .then(data => {
    console.log("Loaded asteroid data:", data);

    if (!data) {
      throw new Error('Asteroid data is empty or invalid');
    }

    addAsteroid(data);
  })
  .catch(error => {
    console.error('Error loading asteroid data:', error);
    console.log('Creating test asteroid belt instead...');
    createTestAsteroid();
  });

// Add single asteroid
function addAsteroid(data) {
    const AU = 90;
    const a = (data.Semi_Major_Axis || 1.0) * AU;
    const e = (typeof data.Eccentricity === 'number') ? data.Eccentricity : 0.1;
    const inc = THREE.MathUtils.degToRad(data.Inclination || 0);
    const raan = THREE.MathUtils.degToRad(data.Asc_Node_Longitude || 0);
    const argp = THREE.MathUtils.degToRad(data.Perihelion_Arg || 0);

    // Asteroid mesh
    const asteroidSize = 2;
    const asteroidGeom = new THREE.SphereGeometry(asteroidSize, 16, 16);
    const asteroidMat = new THREE.MeshStandardMaterial({
        color: data.Hazardous ? 0xff4444 : 0x888888,
        emissive: data.Hazardous ? 0x331111 : 0x111111,
        roughness: 0.8,
        metalness: 0.2
    });
    const asteroid = new THREE.Mesh(asteroidGeom, asteroidMat);
    scene.add(asteroid);
    raycastTargets.push(asteroid);

    // ---------- helper math functions ----------
    function solveKepler(M_rad, e, tol = 1e-9, maxIter = 60) {
        M_rad = ((M_rad % (2 * Math.PI)) + (2 * Math.PI)) % (2 * Math.PI);
        let E = (e < 0.8) ? M_rad : Math.PI;
        for (let i = 0; i < maxIter; i++) {
            const f = E - e * Math.sin(E) - M_rad;
            const fprime = 1 - e * Math.cos(E);
            const dE = -f / fprime;
            E += dE;
            if (Math.abs(dE) < tol) break;
        }
        return E;
    }

    function trueAnomalyFromMean(M_rad, e) {
        const E = solveKepler(M_rad, e);
        const cos_nu = (Math.cos(E) - e) / (1 - e * Math.cos(E));
        const sin_nu = (Math.sqrt(Math.max(0, 1 - e * e)) * Math.sin(E)) / (1 - e * Math.cos(E));
        const nu = Math.atan2(sin_nu, cos_nu);
        return nu;
    }

    function rotatePerifocalToEcliptic(vec_pf, raan, inc, argp) {
        const v = vec_pf.clone();
        v.applyAxisAngle(new THREE.Vector3(0,0,1), argp);
        v.applyAxisAngle(new THREE.Vector3(1,0,0), inc);
        v.applyAxisAngle(new THREE.Vector3(0,0,1), raan);
        return v;
    }

    // Precompute orbit line points
    const orbitPoints = [];
    const numPoints = 360;
    for (let k = 0; k < numPoints; k++) {
        const M_k = (k / numPoints) * 2 * Math.PI;
        const nu_k = trueAnomalyFromMean(M_k, e);
        const r_k = (a * (1 - e * e)) / (1 + e * Math.cos(nu_k));
        const x_pf = r_k * Math.cos(nu_k);
        const y_pf = r_k * Math.sin(nu_k);
        const v_pf = new THREE.Vector3(x_pf, y_pf, 0);
        const v_ecl = rotatePerifocalToEcliptic(v_pf, raan, inc, argp);
        orbitPoints.push(v_ecl);
    }
    const orbitGeometry = new THREE.BufferGeometry().setFromPoints(orbitPoints);
    const orbitMaterial = new THREE.LineBasicMaterial({
        color: data.Hazardous ? 0xff0000 : 0x00ff00,
        transparent: true,
        opacity: 0.8
    });
    const orbit = new THREE.Line(orbitGeometry, orbitMaterial);
    scene.add(orbit);

    // SIMPLIFIED ANIMATION - Use the working approach
    let M = (typeof data.Mean_Anomaly === 'number') ? THREE.MathUtils.degToRad(data.Mean_Anomaly % 360) : Math.random() * Math.PI * 2;
    
    function animateAsteroid() {
        // Simple increment like the working version
        M += 0.002 * settings.accelerationOrbit;
        
        // Solve for true anomaly
        const nu = trueAnomalyFromMean(M, e);
        
        // Calculate position
        const r = (a * (1 - e * e)) / (1 + e * Math.cos(nu));
        const x_pf = r * Math.cos(nu);
        const y_pf = r * Math.sin(nu);
        const v_pf = new THREE.Vector3(x_pf, y_pf, 0);
        const v_ecl = rotatePerifocalToEcliptic(v_pf, raan, inc, argp);

        asteroid.position.copy(v_ecl);
    }

    // Hook into animation loop
    const oldAnimate = animate;
    animate = function() {
        animateAsteroid();
        oldAnimate();
    };
}

// Fallback: create test asteroid belt
function createTestAsteroid() {
  console.log("Creating test asteroid belt");
  
  const asteroidCount = 100;
  const minDistance = 120; // Between Mars and Jupiter
  const maxDistance = 180;
  
  for (let i = 0; i < asteroidCount; i++) {
    const distance = THREE.MathUtils.lerp(minDistance, maxDistance, Math.random());
    const angle = Math.random() * Math.PI * 2;
    const inclination = (Math.random() - 0.5) * 0.3;
    
    const asteroidSize = Math.random() * 0.5 + 0.1;
    const asteroidGeom = new THREE.SphereGeometry(asteroidSize, 8, 6);
    const asteroidMat = new THREE.MeshStandardMaterial({
      color: 0x888888,
      roughness: 0.9,
      metalness: 0.1
    });
    
    const asteroid = new THREE.Mesh(asteroidGeom, asteroidMat);
    
    // Position in a belt (mostly in the XZ plane with some inclination)
    const x = distance * Math.cos(angle);
    const z = distance * Math.sin(angle);
    const y = Math.tan(inclination) * distance;
    
    asteroid.position.set(x, y, z);
    scene.add(asteroid);
    
    raycastTargets.push(asteroid);
  }
  
  console.log("Test asteroid belt created with", asteroidCount, "asteroids");
}

// ****** ASTEROID ORBIT VISUALIZATION (ADD AFTER EXISTING ASTEROID CODE) ******
console.log("Setting up asteroid orbit visualization...");

// Global variables for orbit visualization
let currentOrbitVisualization = null;
let currentEarthOrbit = null;

// Function to generate asteroid orbit data (similar to Python)
function generateAsteroidOrbit(asteroid) {
    const AU = 90; // scene scale (matches your existing AU)
    const a = asteroid.Semi_Major_Axis * AU;
    const e = asteroid.Eccentricity || 0.1;
    const i = THREE.MathUtils.degToRad(asteroid.Inclination || 0);
    const raan = THREE.MathUtils.degToRad(asteroid.Asc_Node_Longitude || 0);
    const argp = THREE.MathUtils.degToRad(asteroid.Perihelion_Arg || 0);
    
    // Number of points to simulate the orbit
    const numPoints = 500;
    const theta = Array.from({length: numPoints}, (_, i) => 2 * Math.PI * i / numPoints);
    
    // Orbit in the orbital plane
    const r = theta.map(t => a * (1 - e**2) / (1 + e * Math.cos(t)));
    const x_orb = theta.map((t, idx) => r[idx] * Math.cos(t));
    const y_orb = theta.map((t, idx) => r[idx] * Math.sin(t));
    const z_orb = new Array(numPoints).fill(0);
    
    // Rotation matrix functions
    function rotMatrix(axis, angleRad) {
        const cos = Math.cos(angleRad);
        const sin = Math.sin(angleRad);
        
        if (axis === 'x') {
            return [
                [1, 0, 0],
                [0, cos, -sin],
                [0, sin, cos]
            ];
        } else if (axis === 'z') {
            return [
                [cos, -sin, 0],
                [sin, cos, 0],
                [0, 0, 1]
            ];
        }
    }
    
    // Matrix multiplication function
    function matrixMultiply(A, B) {
        const result = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
        for (let i = 0; i < 3; i++) {
            for (let j = 0; j < 3; j++) {
                for (let k = 0; k < 3; k++) {
                    result[i][j] += A[i][k] * B[k][j];
                }
            }
        }
        return result;
    }
    
    // Matrix-vector multiplication
    function matrixVectorMultiply(M, v) {
        return [
            M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2],
            M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2],
            M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2]
        ];
    }
    
    // Apply rotations: Arg of Perihelion -> Inclination -> RAAN
    const R_argp = rotMatrix('z', argp);
    const R_i = rotMatrix('x', i);
    const R_raan = rotMatrix('z', raan);
    
    // Combine rotations: R_raan * R_i * R_argp
    const R_temp = matrixMultiply(R_raan, R_i);
    const R_final = matrixMultiply(R_temp, R_argp);
    
    // Transform coordinates
    const x = [];
    const y = [];
    const z = [];
    
    for (let idx = 0; idx < numPoints; idx++) {
        const coords = [x_orb[idx], y_orb[idx], z_orb[idx]];
        const transformed = matrixVectorMultiply(R_final, coords);
        x.push(transformed[0]);
        y.push(transformed[1]);
        z.push(transformed[2]);
    }
    
    // Earth orbit (approx circular, 1 AU)
    const theta_e = Array.from({length: numPoints}, (_, i) => 2 * Math.PI * i / numPoints);
    const x_e = theta_e.map(t => Math.cos(t) * 1.0 * AU); // 1 AU in scene units
    const y_e = theta_e.map(t => Math.sin(t) * 1.0 * AU);
    const z_e = new Array(numPoints).fill(0);
    
    return {
        asteroid: asteroid,
        orbit: { x, y, z },
        earthOrbit: { x: x_e, y: y_e, z: z_e }
    };
}

// Function to create Three.js orbit visualization
function createAsteroidOrbitVisualization(orbitData) {
    const { asteroid, orbit, earthOrbit } = orbitData;
    
    // Clear previous visualization if exists
    if (currentOrbitVisualization) {
        scene.remove(currentOrbitVisualization);
    }
    if (currentEarthOrbit) {
        scene.remove(currentEarthOrbit);
    }
    
    // Create asteroid orbit line
    const orbitPoints = [];
    for (let i = 0; i < orbit.x.length; i++) {
        orbitPoints.push(new THREE.Vector3(orbit.x[i], orbit.y[i], orbit.z[i]));
    }
    
    const orbitGeometry = new THREE.BufferGeometry().setFromPoints(orbitPoints);
    const orbitMaterial = new THREE.LineBasicMaterial({
        color: asteroid.Hazardous ? 0xff0000 : 0x00ff00,
        linewidth: 2,
        transparent: true,
        opacity: 0.8
    });
    const orbitLine = new THREE.Line(orbitGeometry, orbitMaterial);
    scene.add(orbitLine);
    currentOrbitVisualization = orbitLine;
    
    // Create Earth orbit line
    const earthOrbitPoints = [];
    for (let i = 0; i < earthOrbit.x.length; i++) {
        earthOrbitPoints.push(new THREE.Vector3(earthOrbit.x[i], earthOrbit.y[i], earthOrbit.z[i]));
    }
    
    const earthOrbitGeometry = new THREE.BufferGeometry().setFromPoints(earthOrbitPoints);
    const earthOrbitMaterial = new THREE.LineBasicMaterial({
        color: 0x0000ff,
        linewidth: 1,
        transparent: true,
        opacity: 0.6
    });
    const earthOrbitLine = new THREE.Line(earthOrbitGeometry, earthOrbitMaterial);
    scene.add(earthOrbitLine);
    currentEarthOrbit = earthOrbitLine;
    
    // Update UI with asteroid info
    const asteroidInfo = document.getElementById('asteroid-info');
    if (asteroidInfo) {
        asteroidInfo.innerHTML = `
            <h3>Asteroid: ${asteroid.Name || 'Unknown'}</h3>
            <p>Hazardous: ${asteroid.Hazardous ? 'True' : 'False'}</p>
            <p>Semi-Major Axis: ${asteroid.Semi_Major_Axis.toFixed(3)} AU</p>
            <p>Eccentricity: ${asteroid.Eccentricity.toFixed(3)}</p>
            <p>Inclination: ${asteroid.Inclination.toFixed(2)}°</p>
            <p>Orbital Period: ${asteroid.Orbital_Period ? asteroid.Orbital_Period.toFixed(2) + ' days' : 'Unknown'}</p>
        `;
        asteroidInfo.style.display = 'block';
    }
    
    console.log("Asteroid orbit visualization created");
}


// Function to auto-center camera on the orbit
function autoCenterOnOrbit(orbitData) {
    // Calculate bounding box of the orbit
    const orbit = orbitData.orbit;
    const minX = Math.min(...orbit.x);
    const maxX = Math.max(...orbit.x);
    const minY = Math.min(...orbit.y);
    const maxY = Math.max(...orbit.y);
    const minZ = Math.min(...orbit.z);
    const maxZ = Math.max(...orbit.z);
    
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const centerZ = (minZ + maxZ) / 2;
    
    const sizeX = maxX - minX;
    const sizeY = maxY - minY;
    const sizeZ = maxZ - minZ;
    const maxSize = Math.max(sizeX, sizeY, sizeZ);
    
    // Set camera position to show entire orbit
    const cameraDistance = maxSize * 1.5;
    targetCameraPosition = new THREE.Vector3(centerX + cameraDistance, centerY + cameraDistance * 0.5, centerZ + cameraDistance);
    isMovingTowardsPlanet = true;
    
    // Set controls target to orbit center
    controls.target.set(centerX, centerY, centerZ);
}

// Function to clear orbit visualization
function clearOrbitVisualization() {
    if (currentOrbitVisualization) {
        scene.remove(currentOrbitVisualization);
        currentOrbitVisualization = null;
    }
    if (currentEarthOrbit) {
        scene.remove(currentEarthOrbit);
        currentEarthOrbit = null;
    }
    
    const asteroidInfo = document.getElementById('asteroid-info');
    if (asteroidInfo) {
        asteroidInfo.style.display = 'none';
    }
    
    // Reset camera to default position
    zoomOutTargetPosition = new THREE.Vector3(-175, 115, 5);
    isZoomingOut = true;
    controls.target.set(0, 0, 0);
}

// Add to your GUI controls
const asteroidFolder = gui.addFolder('Asteroid Orbits');
//asteroidFolder.add({ showRandomOrbit: () => showRandomAsteroidOrbit() }, 'showRandomOrbit').name('Show Random Orbit');
asteroidFolder.add({ clearOrbit: () => clearOrbitVisualization() }, 'clearOrbit').name('Re-center Orbit');
asteroidFolder.open();

// Create asteroid info display element
const asteroidInfoDiv = document.createElement('div');
asteroidInfoDiv.id = 'asteroid-info';
asteroidInfoDiv.style.cssText = `
    position: absolute;
    top: 80px;
    right: 20px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 15px;
    border-radius: 10px;
    max-width: 300px;
    display: none;
    z-index: 1000;
    border: 2px solid #00ff00;
`;
document.body.appendChild(asteroidInfoDiv);

console.log("Asteroid orbit visualization setup complete");

// Hide loading screen when ready
setTimeout(() => {
    document.getElementById('loading').style.display = 'none';
}, 2000);

// Array of planets and atmospheres for raycasting
const raycastTargets = [
    earth.planet, 
    earth.Atmosphere
].filter(Boolean); // Remove null/undefined

// ******  SHADOWS  ******
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

pointLight.castShadow = true;
pointLight.shadow.mapSize.width = 2048;
pointLight.shadow.mapSize.height = 2048;
pointLight.shadow.camera.near = 0.5;
pointLight.shadow.camera.far = 500;
pointLight.shadow.bias = -0.0001;

// Enable shadows for objects
if (earth.planet) earth.planet.castShadow = earth.planet.receiveShadow = true;
if (earth.Atmosphere) earth.Atmosphere.castShadow = earth.Atmosphere.receiveShadow = true;
if (earth.moons) {
    earth.moons.forEach(moon => {
        if (moon.mesh) {
            moon.mesh.castShadow = moon.mesh.receiveShadow = true;
        }
    });
}

// Missing function declarations
function showPlanetInfo(planetName) {
    const info = document.getElementById('planetInfo');
    const data = planetData[planetName];
    if (data) {
        document.getElementById('planetName').textContent = planetName;
        document.getElementById('planetRadius').textContent = data.radius;
        document.getElementById('planetTilt').textContent = data.tilt;
        document.getElementById('planetRotation').textContent = data.rotation;
        document.getElementById('planetOrbit').textContent = data.orbit;
        document.getElementById('planetDistance').textContent = data.distance;
        document.getElementById('planetMoons').textContent = data.moons;
        document.getElementById('planetDescription').textContent = data.info;
        info.style.display = 'block';
    }
}

function onDocumentMouseDown(event) {
    event.preventDefault();
    // Add planet selection logic here
}

// Animation function
function animate() {
    requestAnimationFrame(animate);

    // Update sun position for shader
    if (earthMaterial && earthMaterial.uniforms) {
        earthMaterial.uniforms.sunPosition.value.copy(sun.position);
    }

    // Rotating planets
    sun.rotateY(0.001 * settings.acceleration);
    if (earth.planet) earth.planet.rotateY(0.005 * settings.acceleration);
    if (earth.Atmosphere) earth.Atmosphere.rotateY(0.001 * settings.acceleration);
    if (earth.planet3d) earth.planet3d.rotateY(0.001 * settings.accelerationOrbit);

    // Animate Earth's moon
    // Animate Earth's moon (FIXED VERSION)
    if (earth.moons) {
        earth.moons.forEach(moon => {
            if (moon.mesh) {
                // Update orbit angle
                moon.orbitAngle += moon.orbitSpeed * settings.accelerationOrbit;
                
                // Calculate moon position in circular orbit around Earth
                // Earth is at position (90, 0, 0) in the planetSystem
                const orbitX = 90 + Math.cos(moon.orbitAngle) * moon.orbitRadius;
                const orbitZ = Math.sin(moon.orbitAngle) * moon.orbitRadius;
                
                // Set moon position - Y coordinate can have slight variation for inclination
                const inclination = 5 * Math.PI / 180; // 5 degree inclination
                const orbitY = Math.sin(moon.orbitAngle) * Math.sin(inclination) * moon.orbitRadius;
                
                moon.mesh.position.set(orbitX, orbitY, orbitZ);
                
                // Rotate moon on its own axis
                moon.mesh.rotateY(0.01 * settings.acceleration);
                
                // Debug logging (uncomment if needed)
                // if (Math.random() < 0.001) {
                //     console.log('Moon position:', moon.mesh.position);
                //     console.log('Moon orbit angle:', moon.orbitAngle);
                // }
            }
        });
    }

    // Raycasting for outlines
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(raycastTargets);
    outlinePass.selectedObjects = [];

    if (intersects.length > 0) {
        const intersectedObject = intersects[0].object;
        if (intersectedObject === earth.Atmosphere) {
            outlinePass.selectedObjects = [earth.planet];
        } else {
            outlinePass.selectedObjects = [intersectedObject];
        }
    }

    // Camera zoom logic
    if (isMovingTowardsPlanet) {
        camera.position.lerp(targetCameraPosition, 0.03);
        if (camera.position.distanceTo(targetCameraPosition) < 1) {
            isMovingTowardsPlanet = false;
            showPlanetInfo(selectedPlanet?.name || 'Earth');
        }
    } else if (isZoomingOut) {
        camera.position.lerp(zoomOutTargetPosition, 0.05);
        if (camera.position.distanceTo(zoomOutTargetPosition) < 1) {
            isZoomingOut = false;
        }
    }

    controls.update();
    composer.render();
}

// Start animation
animate();

// Event listeners
window.addEventListener('mousemove', onMouseMove, false);
window.addEventListener('mousedown', onDocumentMouseDown, false);
window.addEventListener('resize', function() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
});

console.log("Solar system initialization complete");