import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import ResumeStudio from "./ResumeStudio";

export default function ResumePage() {
  const navigate = useNavigate();

  return (
    <div className="mx-auto w-full max-w-7xl px-0">
      <div className="flex items-center gap-3 px-4 py-4 sm:px-6 sm:py-6">
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
            Maple Resume Studio
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Professional template-based resume builder for Canadian employers. 
            Pick a design, customize in real-time, and export to PDF.
          </p>
        </div>
      </div>

      <div className="px-4 sm:px-6">
        <ResumeStudio />
      </div>
    </div>
  );
}

