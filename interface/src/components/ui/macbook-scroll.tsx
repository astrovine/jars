"use client";
import React, { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";
import Image from "next/image";

export const MacbookScroll = ({
    children,
    showGradient,
    title,
    badge,
}: {
    children?: React.ReactNode;
    showGradient?: boolean;
    title?: string | React.ReactNode;
    badge?: React.ReactNode;
}) => {
    const ref = useRef<HTMLDivElement>(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ["start start", "end start"],
    });

    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        if (window && window.innerWidth < 768) {
            setIsMobile(true);
        }
    }, []);

    const scaleX = useTransform(
        scrollYProgress,
        [0, 0.3],
        [1.2, isMobile ? 1 : 1.5]
    );
    const scaleY = useTransform(
        scrollYProgress,
        [0, 0.3],
        [0.6, isMobile ? 1 : 1.5]
    );
    const translate = useTransform(scrollYProgress, [0, 1], [0, 1500]);
    const rotate = useTransform(scrollYProgress, [0.1, 0.12, 0.3], [-28, -28, 0]);
    const textTransform = useTransform(scrollYProgress, [0, 0.3], [0, 100]);
    const textOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);

    return (
        <div
            ref={ref}
            className="min-h-[200vh] flex flex-col items-center py-0 md:py-40 justify-start flex-shrink-0 [perspective:800px] transform md:scale-100 scale-[0.35] sm:scale-50"
        >
            <motion.h2
                style={{
                    translateY: textTransform,
                    opacity: textOpacity,
                }}
                className="dark:text-white text-neutral-800 text-3xl font-bold mb-20 text-center"
            >
                {title || (
                    <span>
                        Trade anywhere, anytime. <br /> Right from your device.
                    </span>
                )}
            </motion.h2>
            {/* Lid */}
            <Lid
                scaleX={scaleX}
                scaleY={scaleY}
                rotate={rotate}
                translate={translate}
            >
                {children}
            </Lid>
            {/* Base area */}
            <div className="h-[22rem] w-[32rem] bg-gray-200 dark:bg-[#272729] rounded-2xl overflow-hidden relative -z-10">
                {/* Above top bar */}
                <div className="h-10 w-full relative">
                    <div className="absolute inset-x-0 mx-auto w-[80%] h-4 bg-[#050505]" />
                </div>
                <div className="flex relative">
                    <div className="mx-auto w-[10%] overflow-hidden  h-full">
                        <SpeakerGrid />
                    </div>
                    <div className="mx-auto w-[80%] h-full">
                        <Keypad />
                    </div>
                    <div className="mx-auto w-[10%] overflow-hidden  h-full">
                        <SpeakerGrid />
                    </div>
                </div>
                <Trackpad />
                <div className="h-2 w-20 mx-auto inset-x-0 absolute bottom-0 bg-gradient-to-t from-[#272729] to-[#050505] rounded-tr-3xl rounded-tl-3xl" />
                {showGradient && (
                    <div className="h-40 w-full absolute bottom-0 inset-x-0 bg-gradient-to-t dark:from-black from-white via-white dark:via-black to-transparent z-50"></div>
                )}
                {badge && <div className="absolute bottom-4 left-4">{badge}</div>}
            </div>
        </div>
    );
};

export const Lid = ({
    scaleX,
    scaleY,
    rotate,
    translate,
    children,
}: {
    scaleX: any;
    scaleY: any;
    rotate: any;
    translate: any;
    children?: React.ReactNode;
}) => {
    return (
        <div className="relative [perspective:800px]">
            <div
                style={{
                    transform: "perspective(800px) rotateX(-25deg) translateZ(0px)",
                    transformOrigin: "bottom",
                    transformStyle: "preserve-3d",
                }}
                className="h-[12rem] w-[32rem] bg-[#010101] rounded-2xl p-2 relative"
            >
                <div
                    style={{
                        boxShadow: "0px 2px 0px 2px var(--neutral-900) inset",
                    }}
                    className="absolute inset-0 bg-[#010101] rounded-lg flex items-center justify-center"
                >
                    <span className="text-white">
                        <AcesLogo />
                    </span>
                </div>
            </div>
            <motion.div
                style={{
                    scaleX: scaleX,
                    scaleY: scaleY,
                    rotateX: rotate,
                    translateY: translate,
                    transformStyle: "preserve-3d",
                    transformOrigin: "top",
                }}
                className="h-96 w-[32rem] absolute inset-0 bg-[#010101] rounded-2xl p-2 overflow-hidden"
            >
                <div className="absolute inset-0 bg-[#0a0a0a] rounded-lg overflow-hidden">
                    {children}
                </div>
            </motion.div>
        </div>
    );
};

export const Trackpad = () => {
    return (
        <div
            className="w-[40%] mx-auto h-32  rounded-xl my-1"
            style={{
                boxShadow: "0px 0px 1px 1px #00000020 inset",
            }}
        ></div>
    );
};

export const Keypad = () => {
    return (
        <div className="h-full rounded-md bg-[#050505] mx-1 p-1">
            {/* First Row */}
            <Row>
                <KBtn
                    className="w-10 items-end justify-start pl-[4px] pb-[2px]"
                    childrenClassName="items-start"
                >
                    esc
                </KBtn>

                <KBtn>
                    <IconBrightnessDown className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F1</span>
                </KBtn>

                <KBtn>
                    <IconBrightnessUp className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F2</span>
                </KBtn>
                <KBtn>
                    <IconTable className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F3</span>
                </KBtn>
                <KBtn>
                    <IconSearch className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F4</span>
                </KBtn>
                <KBtn>
                    <IconMicrophone className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F5</span>
                </KBtn>
                <KBtn>
                    <IconMoon className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F6</span>
                </KBtn>
                <KBtn>
                    <IconPlayerTrackPrev className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F7</span>
                </KBtn>
                <KBtn>
                    <IconPlayerSkipForward className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F8</span>
                </KBtn>
                <KBtn>
                    <IconPlayerTrackNext className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F9</span>
                </KBtn>
                <KBtn>
                    <IconVolume3 className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F10</span>
                </KBtn>
                <KBtn>
                    <IconVolume2 className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F11</span>
                </KBtn>
                <KBtn>
                    <IconVolume className="h-[6px] w-[6px]" />
                    <span className="inline-block mt-1">F12</span>
                </KBtn>
                <KBtn>
                    <div className="h-4 w-4 rounded-full  bg-gradient-to-b from-20% from-neutral-900 via-black via-50% to-neutral-900 to-95% p-px">
                        <div className="bg-black h-full w-full rounded-full" />
                    </div>
                </KBtn>
            </Row>

            {/* Second row */}
            <Row>
                <KBtn>
                    <span className="block">~</span>
                    <span className="block mt-1">`</span>
                </KBtn>

                <KBtn>
                    <span className="block">!</span>
                    <span className="block">1</span>
                </KBtn>
                <KBtn>
                    <span className="block">@</span>
                    <span className="block">2</span>
                </KBtn>
                <KBtn>
                    <span className="block">#</span>
                    <span className="block">3</span>
                </KBtn>
                <KBtn>
                    <span className="block">$</span>
                    <span className="block">4</span>
                </KBtn>
                <KBtn>
                    <span className="block">%</span>
                    <span className="block">5</span>
                </KBtn>
                <KBtn>
                    <span className="block">^</span>
                    <span className="block">6</span>
                </KBtn>
                <KBtn>
                    <span className="block">&</span>
                    <span className="block">7</span>
                </KBtn>
                <KBtn>
                    <span className="block">*</span>
                    <span className="block">8</span>
                </KBtn>
                <KBtn>
                    <span className="block">(</span>
                    <span className="block">9</span>
                </KBtn>
                <KBtn>
                    <span className="block">)</span>
                    <span className="block">0</span>
                </KBtn>
                <KBtn>
                    <span className="block">&mdash;</span>
                    <span className="block">_</span>
                </KBtn>
                <KBtn>
                    <span className="block">+</span>
                    <span className="block">=</span>
                </KBtn>
                <KBtn
                    className="w-10 items-end justify-end pr-[4px] pb-[2px]"
                    childrenClassName="items-end"
                >
                    delete
                </KBtn>
            </Row>

            {/* Third row */}
            <Row>
                <KBtn
                    className="w-10 items-end justify-start pl-[4px] pb-[2px]"
                    childrenClassName="items-start"
                >
                    tab
                </KBtn>
                <KBtn>
                    <span className="block">Q</span>
                </KBtn>

                <KBtn>
                    <span className="block">W</span>
                </KBtn>
                <KBtn>
                    <span className="block">E</span>
                </KBtn>
                <KBtn>
                    <span className="block">R</span>
                </KBtn>
                <KBtn>
                    <span className="block">T</span>
                </KBtn>
                <KBtn>
                    <span className="block">Y</span>
                </KBtn>
                <KBtn>
                    <span className="block">U</span>
                </KBtn>
                <KBtn>
                    <span className="block">I</span>
                </KBtn>
                <KBtn>
                    <span className="block">O</span>
                </KBtn>
                <KBtn>
                    <span className="block">P</span>
                </KBtn>
                <KBtn>
                    <span className="block">{`{`}</span>
                    <span className="block">{`[`}</span>
                </KBtn>
                <KBtn>
                    <span className="block">{`}`}</span>
                    <span className="block">{`]`}</span>
                </KBtn>
                <KBtn>
                    <span className="block">{`|`}</span>
                    <span className="block">{`\\`}</span>
                </KBtn>
            </Row>

            {/* Fourth Row */}
            <Row>
                <KBtn
                    className="w-[2.8rem] items-end justify-start pl-[4px] pb-[2px]"
                    childrenClassName="items-start"
                >
                    caps lock
                </KBtn>
                <KBtn>
                    <span className="block">A</span>
                </KBtn>

                <KBtn>
                    <span className="block">S</span>
                </KBtn>
                <KBtn>
                    <span className="block">D</span>
                </KBtn>
                <KBtn>
                    <span className="block">F</span>
                </KBtn>
                <KBtn>
                    <span className="block">G</span>
                </KBtn>
                <KBtn>
                    <span className="block">H</span>
                </KBtn>
                <KBtn>
                    <span className="block">J</span>
                </KBtn>
                <KBtn>
                    <span className="block">K</span>
                </KBtn>
                <KBtn>
                    <span className="block">L</span>
                </KBtn>
                <KBtn>
                    <span className="block">{`:`}</span>
                    <span className="block">{`;`}</span>
                </KBtn>
                <KBtn>
                    <span className="block">{`"`}</span>
                    <span className="block">{`'`}</span>
                </KBtn>
                <KBtn
                    className="w-[2.85rem] items-end justify-end pr-[4px] pb-[2px]"
                    childrenClassName="items-end"
                >
                    return
                </KBtn>
            </Row>

            {/* Fifth Row */}
            <Row>
                <KBtn
                    className="w-[3.65rem] items-end justify-start pl-[4px] pb-[2px]"
                    childrenClassName="items-start"
                >
                    shift
                </KBtn>
                <KBtn>
                    <span className="block">Z</span>
                </KBtn>
                <KBtn>
                    <span className="block">X</span>
                </KBtn>
                <KBtn>
                    <span className="block">C</span>
                </KBtn>
                <KBtn>
                    <span className="block">V</span>
                </KBtn>
                <KBtn>
                    <span className="block">B</span>
                </KBtn>
                <KBtn>
                    <span className="block">N</span>
                </KBtn>
                <KBtn>
                    <span className="block">M</span>
                </KBtn>
                <KBtn>
                    <span className="block">{`<`}</span>
                    <span className="block">{`,`}</span>
                </KBtn>
                <KBtn>
                    <span className="block">{`>`}</span>
                    <span className="block">{`.`}</span>
                </KBtn>
                <KBtn>
                    <span className="block">{`?`}</span>
                    <span className="block">{`/`}</span>
                </KBtn>
                <KBtn
                    className="w-[3.65rem] items-end justify-end pr-[4px] pb-[2px]"
                    childrenClassName="items-end"
                >
                    shift
                </KBtn>
            </Row>

            {/* Sixth Row */}
            <Row>
                <KBtn className="" childrenClassName="h-full justify-between py-[4px]">
                    <div className="flex justify-end w-full pr-1">
                        <span className="block">fn</span>
                    </div>
                    <div className="flex justify-start w-full pl-1">
                        <IconWorld className="h-[6px] w-[6px]" />
                    </div>
                </KBtn>
                <KBtn className="" childrenClassName="h-full justify-between py-[4px]">
                    <div className="flex justify-end w-full pr-1">
                        <IconChevronUp className="h-[6px] w-[6px]" />
                    </div>
                    <div className="flex justify-start w-full pl-1">
                        <span className="block">control</span>
                    </div>
                </KBtn>
                <KBtn className="" childrenClassName="h-full justify-between py-[4px]">
                    <div className="flex justify-end w-full pr-1">
                        <OptionKey className="h-[6px] w-[6px]" />
                    </div>
                    <div className="flex justify-start w-full pl-1">
                        <span className="block">option</span>
                    </div>
                </KBtn>
                <KBtn
                    className="w-8"
                    childrenClassName="h-full justify-between py-[4px]"
                >
                    <div className="flex justify-end w-full pr-1">
                        <IconCommand className="h-[6px] w-[6px]" />
                    </div>
                    <div className="flex justify-start w-full pl-1">
                        <span className="block">command</span>
                    </div>
                </KBtn>
                <KBtn className="w-[8.2rem]"></KBtn>
                <KBtn
                    className="w-8"
                    childrenClassName="h-full justify-between py-[4px]"
                >
                    <div className="flex justify-start w-full pl-1">
                        <IconCommand className="h-[6px] w-[6px]" />
                    </div>
                    <div className="flex justify-start w-full pl-1">
                        <span className="block">command</span>
                    </div>
                </KBtn>
                <KBtn className="" childrenClassName="h-full justify-between py-[4px]">
                    <div className="flex justify-start w-full pl-1">
                        <OptionKey className="h-[6px] w-[6px]" />
                    </div>
                    <div className="flex justify-start w-full pl-1">
                        <span className="block">option</span>
                    </div>
                </KBtn>
                <div className="w-[4.9rem] mt-[2px] h-6 p-[0.5px] rounded-[4px] flex flex-col justify-end items-center">
                    <KBtn className="w-6 h-3">
                        <IconCaretUpFilled className="h-[6px] w-[6px]" />
                    </KBtn>
                    <div className="flex">
                        <KBtn className="w-6 h-3">
                            <IconCaretLeftFilled className="h-[6px] w-[6px]" />
                        </KBtn>
                        <KBtn className="w-6 h-3">
                            <IconCaretDownFilled className="h-[6px] w-[6px]" />
                        </KBtn>
                        <KBtn className="w-6 h-3">
                            <IconCaretRightFilled className="h-[6px] w-[6px]" />
                        </KBtn>
                    </div>
                </div>
            </Row>
        </div>
    );
};

export const KBtn = ({
    className,
    children,
    childrenClassName,
    backlit = true,
}: {
    className?: string;
    children?: React.ReactNode;
    childrenClassName?: string;
    backlit?: boolean;
}) => {
    return (
        <div
            className={cn(
                "p-[0.5px] rounded-[4px]",
                backlit && "bg-white/[0.2] shadow-xl shadow-white"
            )}
        >
            <div
                className={cn(
                    "h-6 bg-[#0A090D] rounded-[3.5px] flex items-center justify-center",
                    className
                )}
                style={{
                    boxShadow:
                        "0px -0.5px 2px 0 #0D0D0F inset, -0.5px 0px 2px 0 #0D0D0F inset",
                }}
            >
                <div
                    className={cn(
                        "text-neutral-200 text-[5px] w-full flex justify-center items-center flex-col",
                        childrenClassName,
                        backlit && "text-white"
                    )}
                >
                    {children}
                </div>
            </div>
        </div>
    );
};

export const Row = ({ children }: { children: React.ReactNode }) => {
    return (
        <div className="flex gap-[2px] mb-[2px] w-full flex-shrink-0">
            {children}
        </div>
    );
};

export const SpeakerGrid = () => {
    return (
        <div
            className="flex px-[0.5px] gap-[2px] mt-2 h-40"
            style={{
                backgroundImage:
                    "radial-gradient(circle, #08080A 0.5px, transparent 0.5px)",
                backgroundSize: "3px 3px",
            }}
        ></div>
    );
};

export const AcesSLogo = () => {
    return (
        <svg
            width="170"
            height="36"
            viewBox="0 0 170 36"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
        >
            <text x="10" y="28" fontFamily="monospace" fontSize="24" fontWeight="bold" fill="white">
                jars_
            </text>
        </svg>
    );
};

export const AceternityLogo = () => {
    return (
        <svg
            width="66"
            height="65"
            viewBox="0 0 66 65"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="h-3 w-3 text-white"
        >
            <path
                d="M8 8.05571C8 8.05571 54.9009 18.1782 57.8687 30.062C60.8365 41.9458 9.05432 57.4696 9.05432 57.4696"
                stroke="currentColor"
                strokeWidth="15"
                strokeMiterlimit="3.86874"
                strokeLinecap="round"
            />
        </svg>
    );
};

// JARS Logo
export const AceaLogo = () => {
    return (
        <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
                <span className="text-black font-bold text-sm">J</span>
            </div>
        </div>
    );
};

export const AcesLogo = () => {
    return (
        <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
                <span className="text-black font-bold text-sm">J</span>
            </div>
        </div>
    );
};

// Simple keyboard icons
const IconBrightnessDown = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="4" /></svg>
);
const IconBrightnessUp = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="5" /></svg>
);
const IconTable = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="18" height="18" rx="2" /></svg>
);
const IconSearch = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><circle cx="10" cy="10" r="6" /><line x1="15" y1="15" x2="20" y2="20" stroke="currentColor" strokeWidth="2" /></svg>
);
const IconMicrophone = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><rect x="9" y="2" width="6" height="12" rx="3" /></svg>
);
const IconMoon = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" /></svg>
);
const IconPlayerTrackPrev = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="11,5 3,12 11,19" /><rect x="14" y="5" width="3" height="14" /></svg>
);
const IconPlayerSkipForward = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="5,5 13,12 5,19" /><polygon points="13,5 21,12 13,19" /></svg>
);
const IconPlayerTrackNext = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="13,5 21,12 13,19" /><rect x="7" y="5" width="3" height="14" /></svg>
);
const IconVolume3 = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="11,5 6,9 2,9 2,15 6,15 11,19" /></svg>
);
const IconVolume2 = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="11,5 6,9 2,9 2,15 6,15 11,19" /><path d="M15,9 Q18,12 15,15" stroke="currentColor" fill="none" /></svg>
);
const IconVolume = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="11,5 6,9 2,9 2,15 6,15 11,19" /><path d="M15,8 Q20,12 15,16" stroke="currentColor" fill="none" /></svg>
);
const IconWorld = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10" strokeWidth="2" /><ellipse cx="12" cy="12" rx="4" ry="10" strokeWidth="1" /></svg>
);
const IconChevronUp = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polyline points="6,15 12,9 18,15" stroke="currentColor" strokeWidth="2" fill="none" /></svg>
);
const OptionKey = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polyline points="3,6 10,6 18,18 21,18" stroke="currentColor" strokeWidth="2" fill="none" /><line x1="14" y1="6" x2="21" y2="6" stroke="currentColor" strokeWidth="2" /></svg>
);
const IconCommand = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M6,6 L6,3 Q6,0 9,0 Q12,0 12,3 L12,6 L15,6 L15,3 Q15,0 18,0 Q21,0 21,3 L21,6 Q24,6 24,9 Q24,12 21,12 L18,12 L18,15 L21,15 Q24,15 24,18 Q24,21 21,21 L18,21 L18,24 Q18,24 15,24 Q12,24 12,21 L12,18 L9,18 L9,21 Q9,24 6,24 Q3,24 3,21 L3,18 Q0,18 0,15 Q0,12 3,12 L6,12 L6,9 Q3,9 3,6 Q3,3 6,3 Q9,3 9,6 L9,9 L12,9 L12,12 L9,12 L9,15 L12,15 L15,15 L15,12 L18,12 L18,9 L15,9 L15,6 L12,6 Z" stroke="currentColor" strokeWidth="1" fill="none" /></svg>
);
const IconCaretUpFilled = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="12,8 6,16 18,16" /></svg>
);
const IconCaretDownFilled = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="12,16 6,8 18,8" /></svg>
);
const IconCaretLeftFilled = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="8,12 16,6 16,18" /></svg>
);
const IconCaretRightFilled = ({ className }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor"><polygon points="16,12 8,6 8,18" /></svg>
);
