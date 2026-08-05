"use client";

import { useRef, useState } from "react";
import { profileApi, uploadToS3 } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Upload, FileText, CheckCircle } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

interface Props {
  currentUrl: string | null;
}

export function ResumeUpload({ currentUrl }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const qc = useQueryClient();

  const handleFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      setError("Only PDF files are accepted.");
      return;
    }
    setStatus("uploading");
    setError(null);
    try {
      const presigned = await profileApi.getResumeUploadUrl();
      await uploadToS3(presigned, file);
      const resumeUrl = `${presigned.url}${presigned.key}`;
      await profileApi.updateCandidate({ resume_url: resumeUrl });
      qc.invalidateQueries({ queryKey: ["candidate-profile"] });
      setStatus("done");
    } catch (e) {
      setError((e as Error).message);
      setStatus("error");
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resume</CardTitle>
        <CardDescription>Upload a PDF resume for the AI to reference during coaching.</CardDescription>
      </CardHeader>
      <CardContent>
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/50"}`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
          />
          {status === "uploading" ? (
            <div className="space-y-2">
              <div className="animate-spin mx-auto w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
              <p className="text-sm text-muted-foreground">Uploading…</p>
            </div>
          ) : status === "done" ? (
            <div className="space-y-2 text-green-600">
              <CheckCircle className="mx-auto" size={32} />
              <p className="text-sm font-medium">Resume uploaded successfully</p>
            </div>
          ) : currentUrl ? (
            <div className="space-y-2">
              <FileText className="mx-auto text-primary" size={32} />
              <p className="text-sm font-medium">Resume on file</p>
              <p className="text-xs text-muted-foreground">Click or drag to replace</p>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="mx-auto text-muted-foreground" size={32} />
              <p className="text-sm font-medium">Drag & drop or click to upload</p>
              <p className="text-xs text-muted-foreground">PDF only</p>
            </div>
          )}
        </div>
        {error && <p className="text-sm text-destructive mt-2">{error}</p>}
        {currentUrl && (
          <p className="text-xs text-muted-foreground mt-2">
            Current:{" "}
            <a href={currentUrl} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
              View resume
            </a>
          </p>
        )}
      </CardContent>
    </Card>
  );
}
