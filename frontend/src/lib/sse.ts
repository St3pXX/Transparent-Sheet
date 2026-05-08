"use client";

import { useCallback, useRef } from "react";
import { useConsoleStore } from "./store";
import type { SSEEvent } from "@/types";

const SSE_URL = "/stream";
const CONFIRM_URL = "/confirm";

export function useTaskStream() {
  const esRef = useRef<EventSource | null>(null);
  const { startTask, updateState, setTaskStatus, addHistoryItem } =
    useConsoleStore();

  const startStream = useCallback(
    (taskId: string, input: string) => {
      // 关闭已有连接
      if (esRef.current) {
        esRef.current.close();
      }

      startTask(taskId, input);
      addHistoryItem({
        id: taskId,
        task: input,
        time: new Date().toLocaleTimeString("zh-CN", {
          hour: "2-digit",
          minute: "2-digit",
        }),
        status: "running",
      });

      const url = `${SSE_URL}/${taskId}?input=${encodeURIComponent(input)}`;
      const es = new EventSource(url);
      esRef.current = es;

      es.onmessage = (e) => {
        const event: SSEEvent = JSON.parse(e.data);

        switch (event.type) {
          case "state":
            if (event.data) {
              updateState(event.data as Partial<import("@/types").TaskState>);
            }
            break;

          case "confirm_required":
            setTaskStatus("confirming");
            break;

          case "waiting_confirm":
            setTaskStatus("confirming");
            break;

          case "continuation":
            if (event.data) {
              updateState(event.data as Partial<import("@/types").TaskState>);
            }
            break;

          case "done":
            setTaskStatus("done");
            es.close();
            break;

          case "error":
            console.error("SSE error:", event.data);
            setTaskStatus("error");
            es.close();
            break;
        }
      };

      es.onerror = () => {
        console.error("EventSource failed");
        setTaskStatus("error");
        es.close();
      };
    },
    [startTask, updateState, setTaskStatus, addHistoryItem]
  );

  const confirmTask = useCallback(
    async (taskId: string, action: "confirm" | "revise", modifications: unknown[] = []) => {
      const res = await fetch(`${CONFIRM_URL}/${taskId}?action=${action}&modifications=${encodeURIComponent(JSON.stringify(modifications))}`);
      const reader = res.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event: SSEEvent = JSON.parse(line.slice(6));
            if (event.type === "state" || event.type === "continuation") {
              if (event.data) {
                updateState(event.data as Partial<import("@/types").TaskState>);
              }
            } else if (event.type === "done") {
              setTaskStatus("done");
            }
          } catch {}
        }
      }
    },
    [updateState, setTaskStatus]
  );

  const stopStream = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
  }, []);

  return { startStream, stopStream, confirmTask };
}
