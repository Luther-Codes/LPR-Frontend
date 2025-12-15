// /src/hooks/useCanvasDrawing.ts
"use client";

import { useCallback } from "react";
import type { PlateResult, BoundingBox } from "@/types/lpr";

/**
 * drawMultiPlateResults:
 * - canvas: the canvas element
 * - imageEl: the displayed image element (used to compute scaling)
 * - plates: array of PlateResult from backend
 *
 * Important: char_boxes are relative to plate crop (top-left (0,0) is plate crop origin).
 * This function maps char boxes back to the full image coordinates and scales to displayed size.
 */
export function useCanvasDrawing() {
  const drawMultiPlateResults = useCallback(
    (canvas: HTMLCanvasElement | null, imageEl: HTMLImageElement | HTMLVideoElement | null, plates: PlateResult[] | null) => {
      if (!canvas || !imageEl) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // Use displayed dimensions for canvas (so overlay matches CSS layout)
      const displayW = imageEl.clientWidth;
      const displayH = imageEl.clientHeight;

      canvas.width = displayW;
      canvas.height = displayH;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (!plates || plates.length === 0) return;

      // We assume backend coordinates are in image-original pixel space.
      // To scale, we need original image natural size
      let origW = 0;
      let origH = 0;

      if (imageEl instanceof HTMLImageElement) {
        origW = imageEl.naturalWidth;
        origH = imageEl.naturalHeight;
      } else if (imageEl instanceof HTMLVideoElement) {
        origW = imageEl.videoWidth;
        origH = imageEl.videoHeight;
      }

      if (!origW || !origH) return;

      const scaleX = displayW / origW;
      const scaleY = displayH / origH;

      plates.forEach((plate, pIndex) => {
        const pb = plate.plate_box;
        if (!pb) return;

        // draw plate outer box
        ctx.lineWidth = 3;
        ctx.strokeStyle = "#00FF88";
        const px = pb.x1 * scaleX;
        const py = pb.y1 * scaleY;
        const pw = (pb.x2 - pb.x1) * scaleX;
        const ph = (pb.y2 - pb.y1) * scaleY;
        ctx.strokeRect(px, py, pw, ph);

        // plate label
        ctx.fillStyle = "#00FF88";
        ctx.font = "14px Arial";
        ctx.fillText(`${pIndex + 1}: ${plate.plate_number}`, px + 4, py + 16);

        // draw char boxes: they are relative to crop; map to full image then scale
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = "#FF66CC";
        plate.char_boxes?.forEach((cb: BoundingBox) => {
          // char coords relative to plate crop; convert to full-image coords
          const cx = (pb.x1 + cb.x1) * scaleX;
          const cy = (pb.y1 + cb.y1) * scaleY;
          const cw = (cb.x2 - cb.x1) * scaleX;
          const ch = (cb.y2 - cb.y1) * scaleY;
          ctx.strokeRect(cx, cy, cw, ch);
        });
      });
    },
    []
  );

  return { drawMultiPlateResults };
}
