export interface TelemetryData {
  ear_left: number;
  ear_right: number;
  ear_avg: number;
  eyes_closed: boolean;
  closed_duration: number;
  is_drowsy: boolean;
  face_detected: boolean;
  left_eye_coords: [number, number][];
  right_eye_coords: [number, number][];
}

export type Language = 'VI' | 'EN';
