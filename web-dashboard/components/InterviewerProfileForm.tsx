"use client";

import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useEffect } from "react";
import { type InterviewerProfile } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Trash2 } from "lucide-react";
import Link from "next/link";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  company: z.string().optional(),
  role: z.string().optional(),
  interview_style: z.enum(["behavioral", "technical", "mixed"]),
  known_questions: z.array(z.object({ value: z.string() })),
  notes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

interface Props {
  defaultValues?: Partial<InterviewerProfile>;
  onSubmit: (data: Partial<InterviewerProfile>) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
}

export function InterviewerProfileForm({ defaultValues, onSubmit, isLoading, error }: Props) {
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      company: "",
      role: "",
      interview_style: "mixed",
      known_questions: [],
      notes: "",
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "known_questions" });

  useEffect(() => {
    if (defaultValues) {
      reset({
        name: defaultValues.name ?? "",
        company: defaultValues.company ?? "",
        role: defaultValues.role ?? "",
        interview_style: (defaultValues.interview_style as FormValues["interview_style"]) ?? "mixed",
        known_questions: (defaultValues.known_questions ?? []).map((v) => ({ value: v })),
        notes: defaultValues.notes ?? "",
      });
    }
  }, [defaultValues, reset]);

  const handleSubmitForm = async (values: FormValues) => {
    await onSubmit({
      name: values.name,
      company: values.company,
      role: values.role,
      interview_style: values.interview_style,
      known_questions: values.known_questions.map((q) => q.value).filter(Boolean),
      notes: values.notes,
    });
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit(handleSubmitForm)} className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label>Name *</Label>
              <Input placeholder="Jane Smith" {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="space-y-1">
              <Label>Company</Label>
              <Input placeholder="Acme Corp" {...register("company")} />
            </div>
            <div className="space-y-1">
              <Label>Role</Label>
              <Input placeholder="Engineering Manager" {...register("role")} />
            </div>
            <div className="space-y-1">
              <Label>Interview Style</Label>
              <select
                {...register("interview_style")}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="behavioral">Behavioral</option>
                <option value="technical">Technical</option>
                <option value="mixed">Mixed</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Known Questions</Label>
            {fields.map((field, i) => (
              <div key={field.id} className="flex gap-2">
                <Input placeholder={`Question ${i + 1}`} {...register(`known_questions.${i}.value`)} />
                <Button type="button" size="icon" variant="ghost" onClick={() => remove(i)}>
                  <Trash2 size={14} />
                </Button>
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" onClick={() => append({ value: "" })}>
              <Plus size={14} /> Add question
            </Button>
          </div>

          <div className="space-y-1">
            <Label>Notes</Label>
            <Textarea placeholder="Any additional context about this interviewer…" rows={3} {...register("notes")} />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="flex gap-3">
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Saving…" : "Save Profile"}
            </Button>
            <Button type="button" variant="outline" asChild>
              <Link href="/dashboard/interviewers">Cancel</Link>
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
