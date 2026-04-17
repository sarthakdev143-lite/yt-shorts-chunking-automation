import { notFound } from "next/navigation";

import { ReviewDashboard } from "@/components/review-dashboard";
import { getProjectSnapshot } from "@/lib/api";

export default async function ReviewPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await getProjectSnapshot(projectId);

  if (!project) {
    notFound();
  }

  return <ReviewDashboard project={project} />;
}
