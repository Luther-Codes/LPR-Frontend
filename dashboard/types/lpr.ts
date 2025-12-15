export interface BoundingBox {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
}

export interface PlateResult {
    plate_number: string;
    plate_confidence?: number;
    confidence?: number;
    plate_box?: BoundingBox;
    char_boxes?: BoundingBox[];
}

export interface MultiPlateResponse {
    plates: PlateResult[];
    time_taken_ms?: number;
}

export interface SupabaseDetection {
    id: number;
    created_at: string;
    plate_number: string;
    confidence: number;
    status: string;
    time_ms: number;
    user_id?: string;
}

export interface DetectedPlateState {
    plate: string;
    confidence: number;
    status: string;
    time_taken_ms?: number;
    plate_box?: BoundingBox;
    char_boxes?: BoundingBox[];
}
