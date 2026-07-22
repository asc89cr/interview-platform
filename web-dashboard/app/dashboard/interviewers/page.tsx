"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Plus, Pencil, Trash2, Building2 } from "lucide-react";
import { useState } from "react";

export default function InterviewersPage() {
  const qc = useQueryClient();
  const { data: interviewers = [], isLoading } = useQuery({
    queryKey: ["interviewers"],
    queryFn: profileApi.listInterviewers,
  });

  const deleteMutation = useMutation({
    mutationFn: profileApi.deleteInterviewer,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interviewers"] }),
  });

  const [confirmId, setConfirmId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Interviewer Profiles</h1>
          <p className="text-muted-foreground mt-1">Save profiles to get tailored coaching per interviewer.</p>
        </div>
        <Button asChild>
          <Link href="/dashboard/interviewers/new">
            <Plus size={16} /> New Profile
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => <div key={i} className="h-28 rounded-lg bg-muted animate-pulse" />)}
        </div>
      ) : interviewers.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-4 text-center">
            <Building2 size={40} className="text-muted-foreground" />
            <p className="text-muted-foreground">No interviewer profiles yet.</p>
            <Button asChild size="sm">
              <Link href="/dashboard/interviewers/new">Add your first interviewer</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {interviewers.map((iv) => (
            <Card key={iv.id}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{iv.name}</CardTitle>
                    {iv.company && (
                      <p className="text-sm text-muted-foreground mt-0.5">
                        {iv.role ? `${iv.role} at ` : ""}{iv.company}
                      </p>
                    )}
                  </div>
                  <Badge variant="secondary" className="capitalize">{iv.interview_style}</Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                {iv.known_questions.length > 0 && (
                  <p className="text-xs text-muted-foreground mb-3">
                    {iv.known_questions.length} known question{iv.known_questions.length !== 1 ? "s" : ""}
                  </p>
                )}
                <div className="flex gap-2">
                  <Button asChild size="sm" variant="outline">
                    <Link href={`/dashboard/interviewers/${iv.id}`}>
                      <Pencil size={14} /> Edit
                    </Link>
                  </Button>
                  {confirmId === iv.id ? (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => { deleteMutation.mutate(iv.id); setConfirmId(null); }}
                      >
                        Confirm delete
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setConfirmId(null)}>Cancel</Button>
                    </div>
                  ) : (
                    <Button size="sm" variant="ghost" onClick={() => setConfirmId(iv.id)}>
                      <Trash2 size={14} />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
