"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { profileApi, sessionApi } from "@/lib/api";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, ChevronRight, MonitorDown } from "lucide-react";
import Link from "next/link";

const STEPS = ["Candidate Profile", "Interviewer", "Files & Launch"];

export default function NewSessionPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [candidateId, setCandidateId] = useState<string | undefined>();
  const [interviewerId, setInterviewerId] = useState<string | undefined>();
  const [createdSessionId, setCreatedSessionId] = useState<string | null>(null);

  const { data: candidate } = useQuery({
    queryKey: ["candidate-profile"],
    queryFn: profileApi.getCandidate,
  });

  const { data: interviewers = [] } = useQuery({
    queryKey: ["interviewers"],
    queryFn: profileApi.listInterviewers,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      sessionApi.create({
        candidate_profile_id: candidateId,
        interviewer_profile_id: interviewerId,
      }),
    onSuccess: (session) => {
      setCreatedSessionId(session.id);
      setStep(2);
    },
  });

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold">New Interview Session</h1>
        <p className="text-muted-foreground mt-1">Set up your session in 3 steps.</p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <div className={`flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold
              ${i < step ? "bg-green-500 text-white" : i === step ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
              {i < step ? <Check size={14} /> : i + 1}
            </div>
            <span className={`text-sm ${i === step ? "font-semibold" : "text-muted-foreground"}`}>{label}</span>
            {i < STEPS.length - 1 && <ChevronRight size={14} className="text-muted-foreground" />}
          </div>
        ))}
      </div>

      {/* Step 0: Candidate */}
      {step === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Candidate Profile</CardTitle>
            <CardDescription>Confirm which profile to use for coaching context.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {candidate ? (
              <div
                onClick={() => setCandidateId(candidate.id)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-colors
                  ${candidateId === candidate.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
              >
                <p className="font-medium">{candidate.target_role ?? "No role set"}</p>
                <p className="text-sm text-muted-foreground">
                  {candidate.skills.length} skills · {candidate.weak_areas.length} weak areas
                </p>
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">
                No candidate profile.{" "}
                <Link href="/dashboard/profile" className="text-primary hover:underline">Set one up</Link>
              </div>
            )}
            <Button onClick={() => setStep(1)} disabled={!candidate} className="w-full">
              Continue
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 1: Interviewer */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Select Interviewer</CardTitle>
            <CardDescription>Choose who you&apos;re interviewing with.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {interviewers.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No interviewer profiles.{" "}
                <Link href="/dashboard/interviewers/new" className="text-primary hover:underline">Add one</Link>
              </div>
            ) : (
              <div className="space-y-2">
                {interviewers.map((iv) => (
                  <div
                    key={iv.id}
                    onClick={() => setInterviewerId(iv.id)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-colors
                      ${interviewerId === iv.id ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{iv.name}</p>
                        {iv.company && <p className="text-sm text-muted-foreground">{iv.role} · {iv.company}</p>}
                      </div>
                      <Badge variant="secondary" className="capitalize">{iv.interview_style}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setStep(0)} className="flex-1">Back</Button>
              <Button
                onClick={() => createMutation.mutate()}
                disabled={createMutation.isPending}
                className="flex-1"
              >
                {createMutation.isPending ? "Creating…" : "Create Session"}
              </Button>
            </div>
            {createMutation.isError && (
              <p className="text-sm text-destructive">{(createMutation.error as Error).message}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 2: Launch */}
      {step === 2 && createdSessionId && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MonitorDown className="text-primary" /> Session Created!
            </CardTitle>
            <CardDescription>Open the desktop app to start your live session.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-muted rounded-lg p-4 space-y-1">
              <p className="text-xs text-muted-foreground font-mono">Session ID</p>
              <p className="font-mono text-sm break-all">{createdSessionId}</p>
            </div>
            <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
              <li>Open the InterviewAI desktop app</li>
              <li>Paste the session ID above</li>
              <li>Start speaking — coaching appears in real time</li>
            </ol>
            <div className="flex gap-3">
              <Button asChild variant="outline" className="flex-1">
                <Link href={`/dashboard/sessions/${createdSessionId}`}>View session</Link>
              </Button>
              <Button asChild className="flex-1">
                <Link href="/dashboard/sessions">All sessions</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
