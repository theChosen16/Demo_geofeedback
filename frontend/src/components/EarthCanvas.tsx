import React, { useEffect, useRef } from 'react'
import * as THREE from 'three'

const TEXTURES = {
  day: 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/textures/planets/earth_atmos_2048.jpg',
  normal: 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/textures/planets/earth_normal_2048.jpg',
  specular: 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/textures/planets/earth_specular_2048.jpg',
  clouds: 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/textures/planets/earth_clouds_1024.png',
}

export const EarthCanvas: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    if (!container || !canvas) return

    let width = container.clientWidth
    let height = container.clientHeight

    // 1. Renderer Setup
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.z = 7

    // 3. Scene Setup
    const scene = new THREE.Scene()

    // 4. Lights Setup
    // Sun light (bright white/yellow)
    const sunLight = new THREE.DirectionalLight(0xffffff, 2.5)
    sunLight.position.set(-5, 3, 5)
    scene.add(sunLight)

    // Ambient space light (deep dark blueish fill)
    const ambientLight = new THREE.AmbientLight(0x0f172a, 0.6)
    scene.add(ambientLight)

    // Space rim fill light (faint teal-blue glow from shadow side)
    const fillLight = new THREE.DirectionalLight(0x0d9488, 0.5)
    fillLight.position.set(5, -3, -5)
    scene.add(fillLight)

    // 5. Earth and Atmosphere Groups
    const earthGroup = new THREE.Group()
    // Earth axial tilt of 23.5 degrees (0.41 radians)
    earthGroup.rotation.z = 23.5 * Math.PI / 180
    scene.add(earthGroup)

    // 6. Textures Loading
    const loader = new THREE.TextureLoader()
    loader.setCrossOrigin('anonymous')

    // 7. Earth Surface Mesh
    const earthGeometry = new THREE.SphereGeometry(2, 64, 64)
    const earthMaterial = new THREE.MeshPhongMaterial({
      color: 0x1e293b, // Dark base color while textures load
      shininess: 15,
    })
    const earthMesh = new THREE.Mesh(earthGeometry, earthMaterial)
    earthGroup.add(earthMesh)

    // Load textures asynchronously to prevent blocking and white flash
    loader.load(TEXTURES.day, (texture) => {
      earthMaterial.map = texture
      earthMaterial.color.setHex(0xffffff) // Reset color to white so texture matches original colors
      earthMaterial.needsUpdate = true
    })

    loader.load(TEXTURES.normal, (texture) => {
      earthMaterial.normalMap = texture
      earthMaterial.normalScale = new THREE.Vector2(0.18, 0.18) // Realistic elevation scale
      earthMaterial.needsUpdate = true
    })

    loader.load(TEXTURES.specular, (texture) => {
      earthMaterial.specularMap = texture
      earthMaterial.specular = new THREE.Color(0x333333) // Shiny oceans, matte land
      earthMaterial.needsUpdate = true
    })

    // 8. Clouds Layer Mesh
    const cloudsGeometry = new THREE.SphereGeometry(2.02, 64, 64)
    const cloudsMaterial = new THREE.MeshPhongMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0, // Starts fully transparent, fades in once loaded
      depthWrite: false, // Prevents cloud transparency sorting issues
    })
    const cloudsMesh = new THREE.Mesh(cloudsGeometry, cloudsMaterial)
    earthGroup.add(cloudsMesh)

    loader.load(TEXTURES.clouds, (texture) => {
      cloudsMaterial.map = texture
      cloudsMaterial.opacity = 0.45 // Perfect realistic cloud opacity
      cloudsMaterial.needsUpdate = true
    })

    // 9. Atmosphere Glow Mesh (using custom Fresnel shader)
    const atmosphereGeometry = new THREE.SphereGeometry(2.1, 64, 64)
    const atmosphereMaterial = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        void main() {
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          vNormal = normalize(normalMatrix * normal);
          vViewPosition = -mvPosition.xyz;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        void main() {
          vec3 normal = normalize(vNormal);
          vec3 viewDir = normalize(vViewPosition);
          
          // Fresnel effect: corrected for BackSide to glow only at the edges
          float intensity = pow(1.0 + dot(normal, viewDir), 6.0);
          
          // Beautiful glowing teal color matching the Geofeedback theme (#2dd4bf)
          vec3 atmosphereColor = vec3(0.176, 0.831, 0.749);
          gl_FragColor = vec4(atmosphereColor, 1.0) * intensity * 0.75;
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
    })
    const atmosphereMesh = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial)
    // Commented out because the atmosphere is superfluous (color azul/celeste around the Earth)
    // scene.add(atmosphereMesh)

    // 10. 3D Satellites and Laser Beams (Realistic PBR models)
    // Shared Geometries for Satellite Details
    const bodyGeometry = new THREE.BoxGeometry(0.12, 0.12, 0.2)
    const instrumentGeometry = new THREE.BoxGeometry(0.08, 0.08, 0.06) // Instrument pack on top
    const connectorGeometry = new THREE.CylinderGeometry(0.008, 0.008, 0.12, 8) // Solar panel support rods
    const panelFrameGeometry = new THREE.BoxGeometry(0.48, 0.12, 0.01) // Solar panel frame
    const panelCellsGeometry = new THREE.BoxGeometry(0.45, 0.1, 0.015) // Solar cells
    const antennaDishGeometry = new THREE.SphereGeometry(0.06, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2) // Parabolic dish
    const antennaHornGeometry = new THREE.CylinderGeometry(0.005, 0.005, 0.04, 8) // Feed horn support
    const thrusterGeometry = new THREE.ConeGeometry(0.03, 0.05, 12) // Thruster nozzle
    
    // Laser height 1 matches Satellite 1 orbit (2.6)
    const laserHeight1 = 2.6
    const laserGeometry1 = new THREE.ConeGeometry(0.2, laserHeight1, 16)
    laserGeometry1.translate(0, -laserHeight1 / 2, 0)

    // Laser height 2 matches Satellite 2 orbit (2.8)
    const laserHeight2 = 2.8
    const laserGeometry2 = new THREE.ConeGeometry(0.2, laserHeight2, 16)
    laserGeometry2.translate(0, -laserHeight2 / 2, 0)

    // Shared realistic PBR Materials
    const goldFoilMaterial = new THREE.MeshStandardMaterial({
      color: 0xf59e0b, // beautiful warm gold
      metalness: 0.9,
      roughness: 0.15,
      emissive: 0x451a03, // faint golden glow reflection
    })

    const chromeMaterial = new THREE.MeshStandardMaterial({
      color: 0x94a3b8, // slate silver
      metalness: 0.95,
      roughness: 0.1,
    })

    const engineMaterial = new THREE.MeshStandardMaterial({
      color: 0x1e293b, // dark slate
      metalness: 0.8,
      roughness: 0.4,
    })

    const solarCellsMaterial1 = new THREE.MeshStandardMaterial({
      color: 0x0f172a, // dark navy/teal
      emissive: 0x0d9488, // glowing teal
      metalness: 0.9,
      roughness: 0.05,
    })

    const solarCellsMaterial2 = new THREE.MeshStandardMaterial({
      color: 0x0f172a, // dark navy
      emissive: 0x7e22ce, // glowing purple
      metalness: 0.9,
      roughness: 0.05,
    })

    // --- Satellite 1 (Teal Laser / Gold Foil Body) ---
    const satelliteGroup = new THREE.Group()

    // 1. Gold Main Body
    const bodyMesh = new THREE.Mesh(bodyGeometry, goldFoilMaterial)
    satelliteGroup.add(bodyMesh)

    // 2. Instrument block on top
    const instrumentMesh = new THREE.Mesh(instrumentGeometry, chromeMaterial)
    instrumentMesh.position.y = 0.08
    satelliteGroup.add(instrumentMesh)

    // 3. Solar panels (extend horizontally)
    const leftRod = new THREE.Mesh(connectorGeometry, chromeMaterial)
    leftRod.position.x = -0.1
    leftRod.rotation.z = Math.PI / 2
    satelliteGroup.add(leftRod)

    const rightRod = new THREE.Mesh(connectorGeometry, chromeMaterial)
    rightRod.position.x = 0.1
    rightRod.rotation.z = -Math.PI / 2
    satelliteGroup.add(rightRod)

    // Left solar panel (frame + cells)
    const panelFrameLeft = new THREE.Mesh(panelFrameGeometry, chromeMaterial)
    panelFrameLeft.position.x = -0.32
    satelliteGroup.add(panelFrameLeft)

    const panelCellsLeft = new THREE.Mesh(panelCellsGeometry, solarCellsMaterial1)
    panelCellsLeft.position.x = -0.32
    satelliteGroup.add(panelCellsLeft)

    // Right solar panel (frame + cells)
    const panelFrameRight = new THREE.Mesh(panelFrameGeometry, chromeMaterial)
    panelFrameRight.position.x = 0.32
    satelliteGroup.add(panelFrameRight)

    const panelCellsRight = new THREE.Mesh(panelCellsGeometry, solarCellsMaterial1)
    panelCellsRight.position.x = 0.32
    satelliteGroup.add(panelCellsRight)

    // 4. Antenna dish pointing towards Earth
    const antennaDishMesh = new THREE.Mesh(antennaDishGeometry, goldFoilMaterial)
    antennaDishMesh.position.z = 0.1
    antennaDishMesh.rotation.x = Math.PI / 2
    satelliteGroup.add(antennaDishMesh)

    const antennaHornMesh = new THREE.Mesh(antennaHornGeometry, chromeMaterial)
    antennaHornMesh.position.z = 0.13
    antennaHornMesh.rotation.x = Math.PI / 2
    satelliteGroup.add(antennaHornMesh)

    // 5. Thruster at the back
    const thrusterMesh = new THREE.Mesh(thrusterGeometry, engineMaterial)
    thrusterMesh.position.z = -0.12
    thrusterMesh.rotation.x = -Math.PI / 2
    satelliteGroup.add(thrusterMesh)

    // 6. Laser scanner cone
    const laserMaterial = new THREE.MeshBasicMaterial({
      color: 0x2dd4bf, // Teal laser beam
      transparent: true,
      opacity: 0.3,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
    const laserMesh = new THREE.Mesh(laserGeometry1, laserMaterial)
    laserMesh.rotation.x = -Math.PI / 2
    satelliteGroup.add(laserMesh)

    const orbitGroup = new THREE.Group()
    orbitGroup.rotation.x = 0.4
    orbitGroup.rotation.y = 0.3
    scene.add(orbitGroup)
    orbitGroup.add(satelliteGroup)

    // --- Satellite 2 (Purple Laser / Chrome Body) ---
    const satelliteGroup2 = new THREE.Group()

    // 1. Silver Main Body
    const bodyMesh2 = new THREE.Mesh(bodyGeometry, chromeMaterial)
    satelliteGroup2.add(bodyMesh2)

    // 2. Instrument block on top (gold contrast)
    const instrumentMesh2 = new THREE.Mesh(instrumentGeometry, goldFoilMaterial)
    instrumentMesh2.position.y = 0.08
    satelliteGroup2.add(instrumentMesh2)

    // 3. Solar panels (extend horizontally)
    const leftRod2 = new THREE.Mesh(connectorGeometry, chromeMaterial)
    leftRod2.position.x = -0.1
    leftRod2.rotation.z = Math.PI / 2
    satelliteGroup2.add(leftRod2)

    const rightRod2 = new THREE.Mesh(connectorGeometry, chromeMaterial)
    rightRod2.position.x = 0.1
    rightRod2.rotation.z = -Math.PI / 2
    satelliteGroup2.add(rightRod2)

    // Left solar panel (frame + cells)
    const panelFrameLeft2 = new THREE.Mesh(panelFrameGeometry, chromeMaterial)
    panelFrameLeft2.position.x = -0.32
    satelliteGroup2.add(panelFrameLeft2)

    const panelCellsLeft2 = new THREE.Mesh(panelCellsGeometry, solarCellsMaterial2)
    panelCellsLeft2.position.x = -0.32
    satelliteGroup2.add(panelCellsLeft2)

    // Right solar panel (frame + cells)
    const panelFrameRight2 = new THREE.Mesh(panelFrameGeometry, chromeMaterial)
    panelFrameRight2.position.x = 0.32
    satelliteGroup2.add(panelFrameRight2)

    const panelCellsRight2 = new THREE.Mesh(panelCellsGeometry, solarCellsMaterial2)
    panelCellsRight2.position.x = 0.32
    satelliteGroup2.add(panelCellsRight2)

    // 4. Antenna dish pointing towards Earth
    const antennaDishMesh2 = new THREE.Mesh(antennaDishGeometry, chromeMaterial)
    antennaDishMesh2.position.z = 0.1
    antennaDishMesh2.rotation.x = Math.PI / 2
    satelliteGroup2.add(antennaDishMesh2)

    const antennaHornMesh2 = new THREE.Mesh(antennaHornGeometry, goldFoilMaterial)
    antennaHornMesh2.position.z = 0.13
    antennaHornMesh2.rotation.x = Math.PI / 2
    satelliteGroup2.add(antennaHornMesh2)

    // 5. Thruster at the back
    const thrusterMesh2 = new THREE.Mesh(thrusterGeometry, engineMaterial)
    thrusterMesh2.position.z = -0.12
    thrusterMesh2.rotation.x = -Math.PI / 2
    satelliteGroup2.add(thrusterMesh2)

    // 6. Laser scanner cone
    const laserMaterial2 = new THREE.MeshBasicMaterial({
      color: 0xc084fc, // purple/lavender laser beam
      transparent: true,
      opacity: 0.3,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
    const laserMesh2 = new THREE.Mesh(laserGeometry2, laserMaterial2)
    laserMesh2.rotation.x = -Math.PI / 2
    satelliteGroup2.add(laserMesh2)

    const orbitGroup2 = new THREE.Group()
    orbitGroup2.rotation.x = -0.4
    orbitGroup2.rotation.y = -0.5
    scene.add(orbitGroup2)
    orbitGroup2.add(satelliteGroup2)

    // 11. Resize Handling
    const handleResize = () => {
      if (!container) return
      width = container.clientWidth
      height = container.clientHeight
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height)
    }

    const resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(container)

    // 12. Animation Loop
    let lastTime = 0
    let reqId: number
    let satelliteAngle = 0
    let satelliteAngle2 = Math.PI // start opposite to avoid overlap

    const animate = (time: number) => {
      const delta = time - lastTime
      lastTime = time

      // Earth rotations
      earthMesh.rotation.y += 0.00008 * delta
      cloudsMesh.rotation.y += 0.0001 * delta // clouds move slightly faster for depth

      // Satellite 1 orbit positioning
      satelliteAngle += 0.00015 * delta
      const orbitRadius1 = 2.6
      satelliteGroup.position.x = Math.cos(satelliteAngle) * orbitRadius1
      satelliteGroup.position.z = Math.sin(satelliteAngle) * orbitRadius1
      satelliteGroup.lookAt(0, 0, 0)

      // Satellite 2 orbit positioning (faster and opposite)
      satelliteAngle2 -= 0.00022 * delta
      const orbitRadius2 = 2.8
      satelliteGroup2.position.x = Math.cos(satelliteAngle2) * orbitRadius2
      satelliteGroup2.position.z = Math.sin(satelliteAngle2) * orbitRadius2
      satelliteGroup2.lookAt(0, 0, 0)

      // Laser intensity pulsing
      laserMaterial.opacity = 0.2 + Math.sin(time * 0.003) * 0.1
      laserMaterial2.opacity = 0.2 + Math.cos(time * 0.004) * 0.1

      renderer.render(scene, camera)
      reqId = requestAnimationFrame(animate)
    }

    reqId = requestAnimationFrame(animate)

    // Cleanup
    return () => {
      cancelAnimationFrame(reqId)
      resizeObserver.disconnect()
      renderer.dispose()
      
      // Geometry disposals
      earthGeometry.dispose()
      cloudsGeometry.dispose()
      atmosphereGeometry.dispose()
      bodyGeometry.dispose()
      instrumentGeometry.dispose()
      connectorGeometry.dispose()
      panelFrameGeometry.dispose()
      panelCellsGeometry.dispose()
      antennaDishGeometry.dispose()
      antennaHornGeometry.dispose()
      thrusterGeometry.dispose()
      laserGeometry1.dispose()
      laserGeometry2.dispose()

      // Material disposals
      earthMaterial.dispose()
      cloudsMaterial.dispose()
      atmosphereMaterial.dispose()
      goldFoilMaterial.dispose()
      chromeMaterial.dispose()
      engineMaterial.dispose()
      solarCellsMaterial1.dispose()
      solarCellsMaterial2.dispose()
      laserMaterial.dispose()
      laserMaterial2.dispose()
    }
  }, [])

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  )
}
