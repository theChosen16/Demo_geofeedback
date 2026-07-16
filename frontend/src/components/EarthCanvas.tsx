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
    camera.position.z = 6

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
          
          // Fresnel effect: glow is strongest at the edges where angle is perpendicular
          float intensity = pow(1.0 - dot(normal, viewDir), 3.0);
          
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
    scene.add(atmosphereMesh)

    // 10. 3D Satellite and Laser Beam
    const satelliteGroup = new THREE.Group()

    // Satellite body (metallic gold/cyan/grey box)
    const bodyGeometry = new THREE.BoxGeometry(0.1, 0.1, 0.16)
    const bodyMaterial = new THREE.MeshPhongMaterial({
      color: 0x475569, // slate metallic
      shininess: 90,
    })
    const bodyMesh = new THREE.Mesh(bodyGeometry, bodyMaterial)
    satelliteGroup.add(bodyMesh)

    // Solar panels (extend horizontally)
    const panelGeometry = new THREE.BoxGeometry(0.35, 0.08, 0.01)
    const panelMaterial = new THREE.MeshPhongMaterial({
      color: 0x0f766e, // deep teal solar panel
      emissive: 0x115e59, // subtle glow
      shininess: 100,
    })
    
    const panelLeft = new THREE.Mesh(panelGeometry, panelMaterial)
    panelLeft.position.x = -0.22
    satelliteGroup.add(panelLeft)

    const panelRight = new THREE.Mesh(panelGeometry, panelMaterial)
    panelRight.position.x = 0.22
    satelliteGroup.add(panelRight)

    // Antenna dish pointing towards Earth (+Z axis when using lookAt)
    const antennaGeometry = new THREE.ConeGeometry(0.03, 0.05, 16)
    const antennaMaterial = new THREE.MeshPhongMaterial({
      color: 0x94a3b8, // silver dish
      shininess: 60,
    })
    const antennaMesh = new THREE.Mesh(antennaGeometry, antennaMaterial)
    antennaMesh.position.z = 0.08 // Position at front face
    antennaMesh.rotation.x = Math.PI / 2 // Rotate to point along local +Z axis
    satelliteGroup.add(antennaMesh)

    // Translucent Laser Scanner Cone
    // The laser extends along the local +Z axis from the satellite origin
    const laserHeight = 2.8
    const laserGeometry = new THREE.ConeGeometry(0.25, laserHeight, 16)
    // Translate geometry so the apex is at the local origin (0, 0, 0) and extends along -Y
    laserGeometry.translate(0, -laserHeight / 2, 0)
    
    const laserMaterial = new THREE.MeshBasicMaterial({
      color: 0x2dd4bf, // Teal laser beam
      transparent: true,
      opacity: 0.35,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
      depthWrite: false, // Ensures laser transparency blends beautifully
    })
    const laserMesh = new THREE.Mesh(laserGeometry, laserMaterial)
    // Rotate laser mesh so it extends along the local +Z axis
    laserMesh.rotation.x = -Math.PI / 2
    satelliteGroup.add(laserMesh)

    // Orbit group (controls orbital plane tilt)
    const orbitGroup = new THREE.Group()
    orbitGroup.rotation.x = 0.4 // Tilt the orbit plane (approx 23 degrees)
    orbitGroup.rotation.y = 0.3
    scene.add(orbitGroup)
    orbitGroup.add(satelliteGroup)

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

    const animate = (time: number) => {
      const delta = time - lastTime
      lastTime = time

      // Earth rotations
      earthMesh.rotation.y += 0.00008 * delta
      cloudsMesh.rotation.y += 0.0001 * delta // clouds move slightly faster for depth

      // Satellite orbit positioning
      satelliteAngle += 0.0002 * delta
      const orbitRadius = 3.6
      satelliteGroup.position.x = Math.cos(satelliteAngle) * orbitRadius
      satelliteGroup.position.z = Math.sin(satelliteAngle) * orbitRadius
      
      // Face Earth center automatically
      satelliteGroup.lookAt(0, 0, 0)

      // Laser intensity pulsing
      laserMaterial.opacity = 0.25 + Math.sin(time * 0.004) * 0.12

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
      panelGeometry.dispose()
      antennaGeometry.dispose()
      laserGeometry.dispose()

      // Material disposals
      earthMaterial.dispose()
      cloudsMaterial.dispose()
      atmosphereMaterial.dispose()
      bodyMaterial.dispose()
      panelMaterial.dispose()
      antennaMaterial.dispose()
      laserMaterial.dispose()
    }
  }, [])

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  )
}
