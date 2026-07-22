"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface Props {
  scores: Record<string, number>;
}

export function ScoreRadar({ scores }: Props) {
  const data = Object.entries(scores).map(([key, value]) => ({
    subject: key.charAt(0).toUpperCase() + key.slice(1),
    score: value,
    fullMark: 10,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
        <Radar
          name="Score"
          dataKey="score"
          stroke="hsl(221.2 83.2% 53.3%)"
          fill="hsl(221.2 83.2% 53.3%)"
          fillOpacity={0.25}
        />
        <Tooltip formatter={(v) => [`${v}/10`, "Score"]} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
