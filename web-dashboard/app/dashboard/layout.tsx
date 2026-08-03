"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  User,
  Users,
  CalendarDays,
  CreditCard,
  LogOut,
  Mic,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { label: "Dashboard",   href: "/dashboard",                icon: LayoutDashboard },
  { label: "Profile",     href: "/dashboard/profile",        icon: User },
  { label: "Interviewers",href: "/dashboard/interviewers",   icon: Users },
  { label: "Sessions",    href: "/dashboard/sessions",       icon: CalendarDays },
  { label: "Billing",     href: "/dashboard/billing",        icon: CreditCard },
];

function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const logout = () => {
    const rt = auth.getRefreshToken() ?? "";
    fetch("/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: rt }) }).catch(() => {});
    auth.clear();
    router.push("/login");
  };

  return (
    <aside className="flex flex-col w-64 min-h-screen border-r bg-card">
      <div className="flex items-center gap-2 px-6 py-5 border-b">
        <Mic className="text-primary" size={22} />
        <span className="font-bold text-lg tracking-tight">InterviewAI</span>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1">
        {nav.map(({ label, href, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              pathname === href || (href !== "/dashboard" && pathname.startsWith(href))
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="px-3 py-4 border-t">
        <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground" onClick={logout}>
          <LogOut size={16} /> Sign out
        </Button>
      </div>
    </aside>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [authed, setAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    if (auth.isLoggedIn()) {
      setAuthed(true);
    } else {
      router.replace("/login");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // null = still checking (avoids SSR mismatch flash)
  if (authed === null) return null;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto bg-muted/20">
        <div className="max-w-5xl mx-auto p-8">{children}</div>
      </main>
    </div>
  );
}
