"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileApi } from "@/lib/api";
import { InterviewerProfileForm } from "@/components/InterviewerProfileForm";

export default function InterviewerEditPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const isNew = id === "new";

  const { data: interviewer, isLoading } = useQuery({
    queryKey: ["interviewer", id],
    queryFn: () => profileApi.listInterviewers().then((list) => list.find((iv) => iv.id === id)),
    enabled: !isNew,
  });

  const createMutation = useMutation({
    mutationFn: (data: Parameters<typeof profileApi.createInterviewer>[0]) =>
      profileApi.createInterviewer(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interviewers"] });
      router.push("/dashboard/interviewers");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: Parameters<typeof profileApi.updateInterviewer>[1]) =>
      profileApi.updateInterviewer(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interviewers"] });
      qc.invalidateQueries({ queryKey: ["interviewer", id] });
      router.push("/dashboard/interviewers");
    },
  });

  if (!isNew && isLoading) return <div className="animate-pulse h-96 rounded-lg bg-muted" />;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">
        {isNew ? "New Interviewer Profile" : "Edit Interviewer Profile"}
      </h1>
      <InterviewerProfileForm
        defaultValues={interviewer}
        onSubmit={async (data) => {
          if (isNew) await createMutation.mutateAsync(data);
          else await updateMutation.mutateAsync(data);
        }}
        isLoading={createMutation.isPending || updateMutation.isPending}
        error={
          ((createMutation.error || updateMutation.error) as Error | null)?.message
        }
      />
    </div>
  );
}
