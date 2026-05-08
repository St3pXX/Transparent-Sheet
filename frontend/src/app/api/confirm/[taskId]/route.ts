import { NextRequest } from "next/server";
import { Readable } from "stream";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ taskId: string }> }
) {
  const { taskId } = await context.params;
  const { searchParams } = request.nextUrl;
  const action = searchParams.get("action") || "confirm";
  const modifications = searchParams.get("modifications") || "[]";

  const response = await fetch(
    `${BACKEND_URL}/confirm/${taskId}?action=${action}&modifications=${encodeURIComponent(modifications)}`
  );

  const stream = new ReadableStream({
    async start(controller) {
      const reader = response.body?.getReader();
      if (!reader) {
        controller.close();
        return;
      }
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(value);
        }
      } finally {
        reader.releaseLock();
      }
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive",
    },
  });
}
