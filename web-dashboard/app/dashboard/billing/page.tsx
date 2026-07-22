"use client";

import { useQuery } from "@tanstack/react-query";
import { billingApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CreditCard, Zap, Crown } from "lucide-react";

const PLANS = [
  { id: "free",  label: "Free",  sessions: 3,  features: ["3 sessions/mo", "Basic coaching"], price: "$0" },
  { id: "pro",   label: "Pro",   sessions: 30, features: ["30 sessions/mo", "Analysis reports", "PDF export"], price: "$19/mo", priceId: "price_pro" },
  { id: "teams", label: "Teams", sessions: -1, features: ["Unlimited sessions", "All Pro features", "Team management"], price: "$49/mo", priceId: "price_teams" },
];

export default function BillingPage() {
  const { data: sub, isLoading } = useQuery({
    queryKey: ["subscription"],
    queryFn: billingApi.getSubscription,
  });

  const handleUpgrade = async (priceId: string) => {
    try {
      const { url } = await billingApi.createCheckout(priceId);
      window.location.href = url;
    } catch (e) {
      alert((e as Error).message);
    }
  };

  const handlePortal = async () => {
    try {
      const { url } = await billingApi.createPortal();
      window.location.href = url;
    } catch (e) {
      alert((e as Error).message);
    }
  };

  const currentTier = sub?.tier ?? "free";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Billing</h1>
        <p className="text-muted-foreground mt-1">Manage your plan and usage.</p>
      </div>

      {/* Current usage */}
      {!isLoading && sub && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard size={18} /> Current Plan
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-3">
              <Badge variant="secondary" className="capitalize text-sm px-3 py-1">{currentTier}</Badge>
              {currentTier !== "free" && (
                <Button size="sm" variant="outline" onClick={handlePortal}>
                  Manage subscription
                </Button>
              )}
            </div>
            <div className="text-sm text-muted-foreground">
              <span className="font-semibold text-foreground">{sub.sessions_used}</span> of{" "}
              <span className="font-semibold text-foreground">
                {sub.sessions_limit === null ? "∞" : sub.sessions_limit}
              </span>{" "}
              sessions used this month
            </div>
            {sub.sessions_limit !== null && (
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${Math.min(100, (sub.sessions_used / sub.sessions_limit) * 100)}%` }}
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Plan cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {PLANS.map((plan) => {
          const isCurrent = currentTier === plan.id;
          return (
            <Card key={plan.id} className={isCurrent ? "border-primary ring-1 ring-primary" : ""}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    {plan.id === "teams" ? <Crown size={16} className="text-yellow-500" /> :
                     plan.id === "pro"   ? <Zap size={16} className="text-primary" /> : null}
                    {plan.label}
                  </CardTitle>
                  {isCurrent && <Badge variant="secondary">Current</Badge>}
                </div>
                <CardDescription className="text-2xl font-bold text-foreground">{plan.price}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-1 text-sm text-muted-foreground">
                  {plan.features.map((f) => <li key={f}>✓ {f}</li>)}
                </ul>
                {!isCurrent && plan.priceId && (
                  <Button className="w-full" onClick={() => handleUpgrade(plan.priceId!)}>
                    Upgrade to {plan.label}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
