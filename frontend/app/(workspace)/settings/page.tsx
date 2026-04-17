import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getPlatformHealth, getSettingsSnapshot } from "@/lib/api";

export default async function SettingsPage() {
  const [settings, health] = await Promise.all([getSettingsSnapshot(), getPlatformHealth()]);

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Card>
        <CardHeader>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--accent)]">Auth & YouTube</p>
          <CardTitle className="mt-3 text-3xl">Google OAuth and channel access</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium text-[color:var(--foreground)]">Google OAuth credentials</p>
              <Badge variant={settings.auth.googleConfigured ? "success" : "warning"}>
                {settings.auth.googleConfigured ? "ready" : "missing"}
              </Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-[color:var(--muted-foreground)]">Scope: {settings.auth.youtubeScope}</p>
          </div>
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium text-[color:var(--foreground)]">NextAuth secret</p>
              <Badge variant={settings.auth.nextAuthSecretConfigured ? "success" : "warning"}>
                {settings.auth.nextAuthSecretConfigured ? "configured" : "missing"}
              </Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-[color:var(--muted-foreground)]">
              Same Google account is intended to handle both app login and YouTube upload authorization.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--accent)]">Storage & processing</p>
          <CardTitle className="mt-3 text-3xl">Temporary transit rules</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium text-[color:var(--foreground)]">Cloudflare R2 bucket</p>
              <Badge variant={settings.storage.r2Configured ? "success" : "warning"}>
                {settings.storage.r2Configured ? settings.storage.bucketName ?? "configured" : "missing env"}
              </Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-[color:var(--muted-foreground)]">{settings.storage.tempRetentionRule}</p>
          </div>
          <div className="rounded-2xl border border-white/6 bg-black/12 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium text-[color:var(--foreground)]">Groq transcription</p>
              <Badge variant={settings.processing.groqConfigured ? "success" : "warning"}>
                {settings.processing.groqConfigured ? "ready" : "missing env"}
              </Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-[color:var(--muted-foreground)]">{settings.processing.ffmpegStrategy}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="xl:col-span-2">
        <CardHeader>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--accent)]">Platform health</p>
          <CardTitle className="mt-3 text-3xl">Service readiness</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {health.services.map((service) => (
            <div className="rounded-[28px] border border-white/6 bg-black/12 p-4" key={service.name}>
              <div className="flex items-center justify-between gap-3">
                <p className="font-medium text-[color:var(--foreground)]">{service.name}</p>
                <Badge variant={service.status === "ready" ? "success" : service.status === "degraded" ? "warning" : "accent"}>
                  {service.status}
                </Badge>
              </div>
              <p className="mt-3 text-sm leading-6 text-[color:var(--muted-foreground)]">{service.detail}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
