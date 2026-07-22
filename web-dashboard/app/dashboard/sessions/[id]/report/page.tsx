"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { sessionApi } from "@/lib/api";
import { AnalysisReportView } from "@/components/AnalysisReport";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();

  const { data: report, isLoading, isError } = useQuery({
    queryKey: ["report", id],
    queryFn: () => sessionApi.getReport(id),
    retry: false,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button asChild variant="ghost" size="sm">
          <Link href={`/dashboard/sessions/${id}`}>
            <ArrowLeft size={14} /> Back to session
          </Link>
        </Button>
        <h1 className="text-3xl font-bold">Analysis Report</h1>
      </div>

      {isLoading && <div className="animate-pulse h-96 rounded-lg bg-muted" />}

      {isError && (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-lg">Report not ready yet.</p>
          <p className="text-sm mt-1">The AI is still analysing your session. Check back in a minute.</p>
        </div>
      )}

      {report && <AnalysisReportView report={report} sessionId={id} />}
    </div>
  );
}
