"use client";

import { useEffect, useRef, useState } from "react";
import { LoaderCircle, RadioTower, ServerCrash } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { appConfig } from "@/lib/config";
import type { PlatformHealth } from "@/lib/types";

export function ServerWakeIndicator() {
  const [state, setState] = useState<"idle" | "waking" | "ready" | "error">("idle");
  const [health, setHealth] = useState<PlatformHealth | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    timeoutRef.current = setTimeout(() => {
      if (active) {
        setState("waking");
      }
    }, appConfig.wakingThresholdMs);

    fetch("/api/health", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Health request failed: ${response.status}`);
        }

        return (await response.json()) as PlatformHealth;
      })
      .then((payload) => {
        if (!active) {
          return;
        }

        setHealth(payload);
        setState("ready");
      })
      .catch(() => {
        if (active) {
          setState("error");
        }
      })
      .finally(() => {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
      });

    return () => {
      active = false;
      controller.abort();
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  if (state === "error") {
    return (
      <Badge className="gap-2" variant="danger">
        <ServerCrash className="h-3.5 w-3.5" />
        Health check failed
      </Badge>
    );
  }

  if (state === "waking") {
    return (
      <Badge className="gap-2" variant="warning">
        <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
        Waking up server...
      </Badge>
    );
  }

  if (state === "ready") {
    return (
      <Badge className="gap-2" variant={health?.mode === "demo" ? "accent" : "success"}>
        <RadioTower className="h-3.5 w-3.5" />
        {health?.mode === "demo" ? "Demo mode" : "Backend live"}
      </Badge>
    );
  }

  return (
    <Badge className="gap-2" variant="neutral">
      <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
      Checking backend
    </Badge>
  );
}
