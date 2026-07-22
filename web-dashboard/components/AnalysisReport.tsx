"use client";

import { type AnalysisReport } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScoreRadar } from "@/components/ScoreRadar";
import { Download, Lock } from "lucide-react";

const scoreColor = (s: number) =>
  s >= 8 ? "text-green-600" : s >= 6 ? "text-yellow-600" : "text-red-500";

interface Props {
  report: AnalysisReport;
  sessionId: string;
}

export function AnalysisReportView({ report, sessionId }: Props) {
  const hasPdf = Boolean(report.pdf_report_url);

  const downloadPdf = () => {
    window.location.href = `${process.env.NEXT_PUBLIC_API_BASE_URL}/sessions/${sessionId}/report/pdf`;
  };

  return (
    <div className="space-y-6">
      {/* Overall score */}
      <Card>
        <CardContent className="flex items-center justify-between py-6">
          <div>
            <p className="text-sm text-muted-foreground">Overall Score</p>
            <p className={`text-6xl font-bold ${scoreColor(report.overall_score)}`}>
              {report.overall_score.toFixed(1)}
              <span className="text-2xl text-muted-foreground">/10</span>
            </p>
          </div>
          {hasPdf ? (
            <Button onClick={downloadPdf} className="gap-2">
              <Download size={16} /> Download PDF
            </Button>
          ) : (
            <div className="relative">
              <Button disabled className="gap-2 blur-[1px] pointer-events-none">
                <Download size={16} /> Download PDF
              </Button>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="bg-card border rounded-md px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 shadow-sm">
                  <Lock size={12} /> Pro required
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Radar chart */}
      <Card>
        <CardHeader><CardTitle>Category Scores</CardTitle></CardHeader>
        <CardContent>
          <ScoreRadar scores={report.category_scores} />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
            {Object.entries(report.category_scores).map(([key, val]) => (
              <div key={key} className="text-center">
                <p className={`text-2xl font-bold ${scoreColor(val)}`}>{val.toFixed(1)}</p>
                <p className="text-xs text-muted-foreground capitalize">{key}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Strengths */}
      <Card>
        <CardHeader><CardTitle className="text-green-700">Strengths</CardTitle></CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {report.strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-green-500 mt-0.5">✓</span>
                {s}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Weaknesses */}
      <Card>
        <CardHeader><CardTitle className="text-yellow-700">Areas to Improve</CardTitle></CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {report.weaknesses.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-yellow-500 mt-0.5">△</span>
                {w}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Interviewer intent */}
      {report.interviewer_intent_summary && (
        <Card>
          <CardHeader><CardTitle>Interviewer Intent</CardTitle></CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{report.interviewer_intent_summary}</p>
          </CardContent>
        </Card>
      )}

      {/* Recommended practice */}
      {report.recommended_practice.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Recommended Practice</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {report.recommended_practice.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-primary mt-0.5">→</span>
                  {r}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
