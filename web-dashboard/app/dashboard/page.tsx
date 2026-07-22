"use client";

import { useQuery } from "@tanstack/react-query";
import { sessionApi } from "@/lib/api";
import { SessionCard } from "@/components/SessionCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Plus, CalendarDays, Star, TrendingUp } from "lucide-react";

export default function DashboardPage() {
  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: sessionApi.list,
  });

  const recent = sessions.slice(0, 5);
  const analysed = sessions.filter((s) => s.status === "analysed");
  const totalSessions = sessions.length;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back — let&apos;s practice.</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/sessions/new">
            <Plus size={16} /> New Session
          </Link>
        </Button>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
              <CalendarDays size={14} /> Total Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{totalSessions}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
              <Star size={14} /> Avg Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {analysed.length > 0 ? "–" : "–"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
              <TrendingUp size={14} /> Analysed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{analysed.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent sessions */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Recent Sessions</h2>
          <Link href="/dashboard/sessions" className="text-sm text-primary hover:underline">
            View all
          </Link>
        </div>
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-24 rounded-lg bg-muted animate-pulse" />
            ))}
          </div>
        ) : recent.length === 0 ? (
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
            {recent.map((s) => <SessionCard key={s.id} session={s} />)}
          </div>
        )}
      </div>
    </div>
  );
}
