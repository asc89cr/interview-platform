"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { sessionApi } from "@/lib/api";
import { SessionCard } from "@/components/SessionCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";
import { Plus, CalendarDays } from "lucide-react";

export default function SessionsPage() {
  const qc = useQueryClient();
  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: sessionApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: sessionApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sessions"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Sessions</h1>
          <p className="text-muted-foreground mt-1">Your full interview history.</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/sessions/new">
            <Plus size={16} /> New Session
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => <div key={i} className="h-24 rounded-lg bg-muted animate-pulse" />)}
        </div>
      ) : sessions.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-4 text-center">
            <CalendarDays size={40} className="text-muted-foreground" />
            <p className="text-muted-foreground">No sessions yet.</p>
            <Button asChild size="sm">
              <Link href="/dashboard/sessions/new">Start your first session</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {sessions.map((s) => (
            <SessionCard
              key={s.id}
              session={s}
              onDelete={() => deleteMutation.mutate(s.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
