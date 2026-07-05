import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import ResumeMaker from "@/components/resume/ResumeMaker";

export default function ResumePage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          className="h-auto p-1"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
            Resume Maker
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Build a professional resume tailored for Canadian employers. 
            Choose your template and export to PDF.
          </p>
        </div>
      </div>

      <ResumeMaker />
    </div>
  );
}
