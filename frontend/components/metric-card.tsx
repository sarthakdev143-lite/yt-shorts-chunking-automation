import { ArrowUpRight } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
};

export function MetricCard({ label, value, detail }: MetricCardProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-foreground)]">{label}</p>
            <CardTitle className="mt-4 text-4xl">{value}</CardTitle>
          </div>
          <ArrowUpRight className="h-5 w-5 text-[color:var(--accent)]" />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm leading-6 text-[color:var(--muted-foreground)]">{detail}</p>
      </CardContent>
    </Card>
  );
}
