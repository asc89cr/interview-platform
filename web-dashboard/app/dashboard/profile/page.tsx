"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profileApi, uploadToS3 } from "@/lib/api";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ResumeUpload } from "@/components/ResumeUpload";
import { TagInput } from "@/components/TagInput";
import { useEffect, useState } from "react";

const schema = z.object({
  target_role: z.string().optional(),
  target_salary_usd: z.coerce.number().optional(),
  custom_notes: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export default function ProfilePage() {
  const qc = useQueryClient();
  const { data: profile, isLoading } = useQuery({
    queryKey: ["candidate-profile"],
    queryFn: profileApi.getCandidate,
  });

  const [skills, setSkills] = useState<string[]>([]);
  const [weakAreas, setWeakAreas] = useState<string[]>([]);

  const { register, handleSubmit, reset, formState: { isSubmitting, isDirty } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (profile) {
      reset({
        target_role: profile.target_role ?? "",
        target_salary_usd: profile.target_salary_usd ?? undefined,
        custom_notes: profile.custom_notes ?? "",
      });
      setSkills(profile.skills);
      setWeakAreas(profile.weak_areas);
    }
  }, [profile, reset]);

  const mutation = useMutation({
    mutationFn: (data: FormValues) =>
      profileApi.updateCandidate({ ...data, skills, weak_areas: weakAreas }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["candidate-profile"] }),
  });

  const [saved, setSaved] = useState(false);
  const onSubmit = async (values: FormValues) => {
    await mutation.mutateAsync(values);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (isLoading) return <div className="animate-pulse h-96 rounded-lg bg-muted" />;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Candidate Profile</h1>
        <p className="text-muted-foreground mt-1">Your profile is used to tailor coaching suggestions.</p>
      </div>

      <ResumeUpload currentUrl={profile?.resume_url ?? null} />

      <Card>
        <CardHeader>
          <CardTitle>Profile Details</CardTitle>
          <CardDescription>Describe your target role and coaching preferences.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label>Target Role</Label>
                <Input placeholder="e.g. Senior Software Engineer" {...register("target_role")} />
              </div>
              <div className="space-y-1">
                <Label>Target Salary (USD)</Label>
                <Input type="number" placeholder="150000" {...register("target_salary_usd")} />
              </div>
            </div>

            <div className="space-y-1">
              <Label>Skills</Label>
              <TagInput tags={skills} onChange={setSkills} placeholder="Add a skill…" />
            </div>

            <div className="space-y-1">
              <Label>Weak Areas</Label>
              <TagInput tags={weakAreas} onChange={setWeakAreas} placeholder="Add a weak area…" />
            </div>

            <div className="space-y-1">
              <Label>Notes</Label>
              <Textarea placeholder="Any additional context for the AI coach…" rows={4} {...register("custom_notes")} />
            </div>

            <div className="flex items-center gap-3">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Saving…" : "Save changes"}
              </Button>
              {saved && <span className="text-sm text-green-600">Saved ✓</span>}
              {mutation.isError && (
                <span className="text-sm text-destructive">
                  {(mutation.error as Error).message}
                </span>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
