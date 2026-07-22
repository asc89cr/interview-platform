"use client";

import { type Session } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { CalendarDays, FileText, Trash2 } from "lucide-react";
import { useState } from "react";

const statusVariant: Record<string, "default" | "secondary" | "success" | "warning" | "outline"> = {
  active:    "default",
  completed: "secondary",
  analysing: "warning",
  analysed:  "success",
};

interface Props {
  session: Session;
  onDelete?: () => void;
}

export function SessionCard({ session, onDelete }: Props) {
  const [confirming, setConfirming] = useState(false);

  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-4 py-4">
        <div className="flex items-center gap-4 min-w-0">
          <CalendarDays size={18} className="text-muted-foreground shrink-0" />
          <div className="min-w-0">
            <p className="font-medium text-sm truncate">
              {session.started_at
                ? new Date(session.started_at).toLocaleDateString(undefined, {
                    weekday: "short", year: "numeric", month: "short", day: "numeric",
                  })
                : new Date(session.created_at).toLocaleDateString()}
            </p>
            <p className="text-xs text-muted-foreground font-mono truncate">{session.id}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge variant={statusVariant[session.status] ?? "secondary"} className="capitalize">
            {session.status}
          </Badge>

          <Button asChild size="sm" variant="ghost">
            <Link href={`/dashboard/sessions/${session.id}`}>
              <FileText size={14} />
            </Link>
          </Button>

          {session.status === "analysed" && (
            <Button asChild size="sm" variant="ghost">
              <Link href={`/dashboard/sessions/${session.id}/report`}>Report</Link>
            </Button>
          )}

          {onDelete && (
            confirming ? (
              <div className="flex gap-1">
                <Button size="sm" variant="destructive" onClick={() => { onDelete(); setConfirming(false); }}>
                  Delete
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setConfirming(false)}>Cancel</Button>
              </div>
            ) : (
              <Button size="sm" variant="ghost" onClick={() => setConfirming(true)}>
                <Trash2 size={14} className="text-muted-foreground" />
              </Button>
            )
          )}
        </div>
      </CardContent>
    </Card>
  );
}
