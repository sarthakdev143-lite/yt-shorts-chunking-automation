import { getPlatformHealth } from "@/lib/api";

export async function GET() {
  const health = await getPlatformHealth();
  return Response.json(health);
}
