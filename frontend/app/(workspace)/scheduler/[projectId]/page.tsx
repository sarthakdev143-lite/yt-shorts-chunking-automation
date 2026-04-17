import { notFound } from "next/navigation";

import { SchedulerBoard } from "@/components/scheduler-board";
import { getProjectSnapshot } from "@/lib/api";

export default async function SchedulerPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const project = await getProjectSnapshot(projectId);

  if (!project) {
    notFound();
  }

  return <SchedulerBoard project={project} />;
}
