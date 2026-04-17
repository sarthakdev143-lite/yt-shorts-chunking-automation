import { SidebarNav } from "@/components/sidebar-nav";
import { Topbar } from "@/components/topbar";

type AppShellProps = {
  children: React.ReactNode;
  userName?: string | null;
  userEmail?: string | null;
};

export function AppShell({ children, userName, userEmail }: AppShellProps) {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[280px_minmax(0,1fr)]">
      <SidebarNav />
      <div className="min-h-screen bg-transparent">
        <Topbar userEmail={userEmail} userName={userName} />
        <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
