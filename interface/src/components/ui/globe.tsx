"use client";
import { useEffect, useRef, useState } from "react";
import { Color, Scene, Fog, PerspectiveCamera, Vector3 } from "three";
import ThreeGlobe from "three-globe";
import { useThree, Canvas, extend, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

declare module "@react-three/fiber" {
    interface ThreeElements {
        threeGlobe: ThreeElements["mesh"] & {
            new(): ThreeGlobe;
        };
    }
}

extend({ ThreeGlobe: ThreeGlobe });

const RING_PROPAGATION_SPEED = 3;

type Position = {
    order: number;
    startLat: number;
    startLng: number;
    endLat: number;
    endLng: number;
    arcAlt: number;
    color: string;
};

export type GlobeConfig = {
    pointSize?: number;
    globeColor?: string;
    showAtmosphere?: boolean;
    atmosphereColor?: string;
    atmosphereAltitude?: number;
    emissive?: string;
    emissiveIntensity?: number;
    shininess?: number;
    polygonColor?: string;
    ambientLight?: string;
    directionalLeftLight?: string;
    directionalTopLight?: string;
    pointLight?: string;
    arcTime?: number;
    arcLength?: number;
    rings?: number;
    maxRings?: number;
    initialPosition?: {
        lat: number;
        lng: number;
    };
    autoRotate?: boolean;
    autoRotateSpeed?: number;
};

interface WorldProps {
    globeConfig: GlobeConfig;
    data: Position[];
}

function genRandomNumbers(min: number, max: number, count: number) {
    const arr: number[] = [];
    while (arr.length < count) {
        const r = Math.floor(Math.random() * (max - min)) + min;
        if (arr.indexOf(r) === -1) arr.push(r);
    }
    return arr;
}

export function Globe({ globeConfig, data }: WorldProps) {
    const globeRef = useRef<ThreeGlobe | null>(null);
    const groupRef = useRef<any>();
    const [isInitialized, setIsInitialized] = useState(false);

    const defaultProps = {
        pointSize: 1,
        atmosphereColor: "#10b981",
        showAtmosphere: true,
        atmosphereAltitude: 0.15,
        polygonColor: "rgba(16,185,129,0.5)",
        globeColor: "#1a1a2e",
        emissive: "#0f172a",
        emissiveIntensity: 0.2,
        shininess: 0.9,
        arcTime: 2000,
        arcLength: 0.9,
        rings: 1,
        maxRings: 3,
        ...globeConfig,
    };

    useEffect(() => {
        if (!globeRef.current && groupRef.current) {
            globeRef.current = new ThreeGlobe({ animateIn: false })
                .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
                .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png');

            groupRef.current.add(globeRef.current);
            setIsInitialized(true);
        }
    }, []);

    useEffect(() => {
        if (!globeRef.current || !isInitialized) return;

        const globeMaterial = globeRef.current.globeMaterial() as unknown as {
            color: Color;
            emissive: Color;
            emissiveIntensity: number;
            shininess: number;
        };
        globeMaterial.color = new Color(defaultProps.globeColor);
        globeMaterial.emissive = new Color(defaultProps.emissive);
        globeMaterial.emissiveIntensity = defaultProps.emissiveIntensity;
        globeMaterial.shininess = defaultProps.shininess;
    }, [isInitialized, defaultProps.globeColor, defaultProps.emissive, defaultProps.emissiveIntensity, defaultProps.shininess]);

    useEffect(() => {
        if (!globeRef.current || !isInitialized || !data) return;

        const arcs = data;
        const points: any[] = [];
        for (let i = 0; i < arcs.length; i++) {
            const arc = arcs[i];
            points.push({
                size: defaultProps.pointSize,
                order: arc.order,
                color: arc.color,
                lat: arc.startLat,
                lng: arc.startLng,
            });
            points.push({
                size: defaultProps.pointSize,
                order: arc.order,
                color: arc.color,
                lat: arc.endLat,
                lng: arc.endLng,
            });
        }

        const filteredPoints = points.filter(
            (v, i, a) =>
                a.findIndex((v2) =>
                    ["lat", "lng"].every(
                        (k) => v2[k as "lat" | "lng"] === v[k as "lat" | "lng"]
                    )
                ) === i
        );

        globeRef.current
            .showAtmosphere(defaultProps.showAtmosphere)
            .atmosphereColor(defaultProps.atmosphereColor)
            .atmosphereAltitude(defaultProps.atmosphereAltitude);

        globeRef.current
            .arcsData(data)
            .arcStartLat((d: any) => d.startLat)
            .arcStartLng((d: any) => d.startLng)
            .arcEndLat((d: any) => d.endLat)
            .arcEndLng((d: any) => d.endLng)
            .arcColor((e: any) => e.color)
            .arcAltitude((e: any) => e.arcAlt)
            .arcStroke(() => [0.32, 0.28, 0.3][Math.round(Math.random() * 2)])
            .arcDashLength(defaultProps.arcLength)
            .arcDashInitialGap((e: any) => e.order)
            .arcDashGap(15)
            .arcDashAnimateTime(() => defaultProps.arcTime);

        globeRef.current
            .pointsData(filteredPoints)
            .pointColor((e: any) => e.color)
            .pointsMerge(true)
            .pointAltitude(0.0)
            .pointRadius(2);

        globeRef.current
            .ringsData([])
            .ringColor(() => defaultProps.polygonColor)
            .ringMaxRadius(defaultProps.maxRings)
            .ringPropagationSpeed(RING_PROPAGATION_SPEED)
            .ringRepeatPeriod(
                (defaultProps.arcTime * defaultProps.arcLength) / defaultProps.rings
            );
    }, [isInitialized, data, defaultProps]);

    useEffect(() => {
        if (!globeRef.current || !isInitialized || !data) return;

        const interval = setInterval(() => {
            if (!globeRef.current) return;

            const newNumbersOfRings = genRandomNumbers(
                0,
                data.length,
                Math.floor((data.length * 4) / 5)
            );

            const ringsData = data
                .filter((_, i) => newNumbersOfRings.includes(i))
                .map((d) => ({
                    lat: d.startLat,
                    lng: d.startLng,
                    color: d.color,
                }));

            globeRef.current.ringsData(ringsData);
        }, 2000);

        return () => clearInterval(interval);
    }, [isInitialized, data]);

    // Auto-rotate the globe
    useFrame(() => {
        if (groupRef.current) {
            groupRef.current.rotation.y += 0.002;
        }
    });

    return <group ref={groupRef} />;
}

export function World(props: WorldProps) {
    const { globeConfig } = props;

    return (
        <Canvas
            camera={{ position: [0, 0, 300], fov: 50, near: 1, far: 1000 }}
            style={{ background: '#000000' }}
            gl={{
                antialias: true,
                alpha: false,
                powerPreference: 'high-performance'
            }}
        >
            <color attach="background" args={['#000000']} />
            <fog attach="fog" args={['#000000', 400, 2000]} />
            <ambientLight color={globeConfig.ambientLight || "#10b981"} intensity={0.8} />
            <directionalLight
                color={globeConfig.directionalLeftLight || "#ffffff"}
                position={[-400, 100, 400]}
                intensity={1}
            />
            <directionalLight
                color={globeConfig.directionalTopLight || "#10b981"}
                position={[-200, 500, 200]}
                intensity={0.5}
            />
            <pointLight
                color={globeConfig.pointLight || "#ffffff"}
                position={[-200, 500, 200]}
                intensity={0.8}
            />
            <Globe {...props} />
            <OrbitControls
                enablePan={false}
                enableZoom={false}
                minDistance={300}
                maxDistance={300}
                autoRotateSpeed={0.5}
                autoRotate={false}
                minPolarAngle={Math.PI / 3.5}
                maxPolarAngle={Math.PI - Math.PI / 3}
            />
        </Canvas>
    );
}
