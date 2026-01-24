"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatCurrency } from "@/lib/utils";

const data = [
    { time: "09:30", value: 1000 },
    { time: "10:00", value: 1020 },
    { time: "10:30", value: 1015 },
    { time: "11:00", value: 1040 },
    { time: "11:30", value: 1055 },
    { time: "12:00", value: 1050 },
    { time: "12:30", value: 1080 },
    { time: "13:00", value: 1095 },
    { time: "13:30", value: 1120 },
    { time: "14:00", value: 1110 },
    { time: "14:30", value: 1140 },
    { time: "15:00", value: 1160 },
];

export function ProfitChart() {
    return (
        <div className="h-[300px] w-full bg-[#050505] border border-white/5 p-2 relative">
            <div className="absolute top-2 left-2 z-10">
                <h3 className="text-xs uppercase font-bold text-neutral-500 tracking-wider">Equity Curve (24H)</h3>
                <p className="text-xl font-mono text-emerald-500 font-bold">$12,450.20</p>
            </div>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10B981" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis
                        dataKey="time"
                        stroke="#555"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                    />
                    <YAxis
                        stroke="#555"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `$${value}`}
                        domain={['auto', 'auto']}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#000', borderColor: '#333', fontSize: '12px' }}
                        itemStyle={{ color: '#fff' }}
                        labelStyle={{ display: 'none' }}
                    />
                    <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#10B981"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorValue)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
