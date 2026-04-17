import { AppShell } from "@/components/app-shell";
import { auth } from "@/lib/auth";

export default async function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  return (
    <AppShell userEmail={session?.user?.email} userName={session?.user?.name}>
      {children}
    </AppShell>
  );
}
