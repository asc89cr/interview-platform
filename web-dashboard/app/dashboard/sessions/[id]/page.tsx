"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { sessionApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { FileText, MessageSquare } from "lucide-react";

const statusVariant: Record<string, "default" | "secondary" | "success" | "warning" | "outline"> = {
  active: "default",
  completed: "secondary",
  analysing: "warning",
  analysed: "success",
};

export default function SessionDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: session, isLoading } = useQuery({
    queryKey: ["session", id],
    queryFn: () => sessionApi.get(id),
  });

  if (isLoading) return <div className="animate-pulse h-96 rounded-lg bg-muted" />;
  if (!session) return <p className="text-muted-foreground">Session not found.</p>;

  const interviewerTurns = session.turns.filter((t) => t.speaker === "Interviewer");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Session Detail</h1>
          <p className="text-muted-foreground mt-1 font-mono text-sm">{session.id}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={statusVariant[session.status] ?? "secondary"} className="capitalize">
            {session.status}
          </Badge>
          {session.status === "analysed" && (
            <Button asChild size="sm">
              <Link href={`/dashboard/sessions/${id}/report`}>
                <FileText size={14} /> View Report
              </Link>
            </Button>
          )}
        </div>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
        <div><p className="text-muted-foreground">Started</p><p className="font-medium">{session.started_at ? new Date(session.started_at).toLocaleString() : "–"}</p></div>
        <div><p className="text-muted-foreground">Ended</p><p className="font-medium">{session.ended_at ? new Date(session.ended_at).toLocaleString() : "–"}</p></div>
        <div><p className="text-muted-foreground">Turns</p><p className="font-medium">{session.turns.length}</p></div>
        <div><p className="text-muted-foreground">Files</p><p className="font-medium">{session.attached_files.length}</p></div>
      </div>

      {/* Transcript */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><MessageSquare size={18} /> Transcript</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {session.turns.length === 0 ? (
            <p className="text-muted-foreground text-sm">No transcript yet.</p>
          ) : (
            session.turns.map((turn) => (
              <div key={turn.id} className={`space-y-1 ${turn.speaker === "Candidate" ? "pl-8" : ""}`}>
                <p className={`text-xs font-semibold ${turn.speaker === "Interviewer" ? "text-primary" : "text-muted-foreground"}`}>
                  {turn.speaker}
                </p>
                <div className={`rounded-lg p-3 text-sm ${turn.speaker === "Interviewer" ? "bg-primary/5 border border-primary/20" : "bg-muted"}`}>
                  <p>{turn.text}</p>
                  {turn.generated_answer && (
                    <div className="mt-2 pt-2 border-t border-dashed">
                      <p className="text-xs text-primary font-medium mb-1">AI Suggestion</p>
                      <p className="text-muted-foreground">{turn.generated_answer}</p>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {/* Attached files */}
      {session.attached_files.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Attached Files</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {session.attached_files.map((f) => (
              <div key={f.id} className="flex items-center justify-between text-sm">
                <span>{f.label}</span>
                <a href={f.file_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  Download
                </a>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
