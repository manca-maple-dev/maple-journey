import { useNavigate } from "react-router-dom";
import { CreditCard, Check, Clock, AlertCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/context/AuthContext";

const STATUS_CONFIG = {
  completed: { label: "Paid", icon: Check, color: "bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200" },
  pending: { label: "Pending", icon: Clock, color: "bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-200" },
  failed: { label: "Failed", icon: AlertCircle, color: "bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200" },
  refunded: { label: "Refunded", icon: Check, color: "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200" },
};

export default function BillingHistory() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const { data: txns = [], isLoading } = useQuery({
    queryKey: ["billing"],
    queryFn: () => api.get("/billing/history").then((r) => (Array.isArray(r.data) ? r.data : [])),
  });

  const invoices = txns.map((t, idx) => ({
    id: `${t.created_at || ""}-${idx}`,
    invoice_number: String(idx + 1).padStart(4, "0"),
    created_at: t.created_at,
    amount: Math.round(Number(t.amount || 0) * 100),
    description: (t.plan_id || "plan").replace(/_/g, " "),
    status: t.status === "paid" ? "completed" : t.status,
  }));

  const subscriptions = user?.tier && user.tier !== "free"
    ? [{
        id: user.tier,
        plan_name: user.tier === "plus" ? "Plus" : "Family",
        status: "active",
        amount: user.tier === "plus" ? 299 : 499,
        billing_period: "month",
        next_billing_date: user?.tier_expires_at || new Date().toISOString(),
      }]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold flex items-center gap-2">
          <CreditCard className="h-8 w-8 text-maple-red" />
          Billing & Payments
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          View your subscription, invoices, and payment history.
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="invoices" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
          <TabsTrigger value="subscriptions">Subscriptions</TabsTrigger>
        </TabsList>

        {/* Invoices Tab */}
        <TabsContent value="invoices" className="space-y-4 mt-6">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 rounded-2xl bg-card border border-border mj-shimmer" />
              ))}
            </div>
          ) : invoices.length === 0 ? (
            <div className="rounded-2xl border border-border bg-card p-8 text-center">
              <CreditCard className="h-12 w-12 mx-auto opacity-20 mb-3" />
              <p className="text-muted-foreground">No invoices are available at the moment.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {invoices.map((inv) => {
                const status = STATUS_CONFIG[inv.status] || STATUS_CONFIG.pending;
                return (
                  <div key={inv.id} className="rounded-2xl border border-border bg-card p-5 hover:shadow-md transition-shadow">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold">Invoice #{inv.invoice_number}</h3>
                          <Badge variant="outline" className={status.color}>
                            {status.label}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {new Date(inv.created_at).toLocaleDateString("en-CA", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </p>
                      </div>

                      <div className="text-right">
                        <p className="font-semibold text-lg">${(inv.amount / 100).toFixed(2)}</p>
                        <p className="text-xs text-muted-foreground">{inv.description}</p>
                      </div>

                      <span className="text-xs text-muted-foreground">Receipt available in transaction history</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Subscriptions Tab */}
        <TabsContent value="subscriptions" className="space-y-4 mt-6">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-32 rounded-2xl bg-card border border-border mj-shimmer" />
              ))}
            </div>
          ) : subscriptions.length === 0 ? (
            <div className="rounded-2xl border border-border bg-card p-8 text-center">
              <CreditCard className="h-12 w-12 mx-auto opacity-20 mb-3" />
              <p className="text-muted-foreground">No active subscriptions at the moment.</p>
              <Button className="mt-4" onClick={() => navigate("/app/plans")}>
                Browse Plans
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {subscriptions.map((sub) => (
                <div key={sub.id} className="rounded-2xl border border-border bg-card p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                    <div>
                      <h3 className="font-semibold text-lg">{sub.plan_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {sub.status === "active" ? "Active subscription" : `Status: ${sub.status}`}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-2xl">
                        ${(sub.amount / 100).toFixed(2)}
                        <span className="text-xs font-normal text-muted-foreground ml-1">/{sub.billing_period}</span>
                      </p>
                    </div>
                  </div>

                  {/* Details */}
                  <div className="grid gap-3 mb-4 text-sm border-t border-border pt-4">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Billing Date:</span>
                      <span className="font-medium">
                        {new Date(sub.next_billing_date).toLocaleDateString()}
                      </span>
                    </div>
                    {sub.cancel_at && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Cancels on:</span>
                        <span className="font-medium text-red-600">
                          {new Date(sub.cancel_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    {sub.status === "active" && !sub.cancel_at && (
                      <Button variant="outline" size="sm" className="text-red-600">
                        Cancel Subscription
                      </Button>
                    )}
                    {sub.cancel_at && sub.status === "active" && (
                      <Button variant="outline" size="sm">
                        Reactivate
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
