import { Component } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Top-level error boundary. Catches render crashes and shows a
 * trustworthy, jargon-free recovery UI instead of a white screen.
 */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error("Unhandled UI error:", error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false });
    window.location.assign("/");
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="grid min-h-screen place-items-center bg-background px-6" data-testid="error-boundary">
          <div className="max-w-md text-center">
            <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-maple/10 text-maple">
              <AlertTriangle className="h-7 w-7" />
            </div>
            <h1 className="mt-5 font-display text-2xl font-bold tracking-tight">Something went off track</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              We hit an unexpected snag. Your data is safe — let's get you back on your journey.
            </p>
            <Button onClick={this.handleReset} className="mt-6 rounded-full" data-testid="error-boundary-reset">
              Back to home
            </Button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
