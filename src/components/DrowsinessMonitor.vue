<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import type { TelemetryData } from '../types/telemetry';

interface WindowState {
  id: string;
  title: string;
  isOpen: boolean;
  isMinimized: boolean;
  isMaximized: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  prevX: number;
  prevY: number;
  prevWidth: number;
  prevHeight: number;
  zIndex: number;
}

interface DesktopIcon {
  id: string;
  name: string;
  type: 'detector' | 'word' | 'github' | 'folder' | 'pc' | 'trash';
  x: number;
  y: number;
  targetWindow?: string;
}

const activeZIndex = ref(100);
const cameraError = ref<string | null>(null);

async function requestCameraPermission() {
  cameraError.value = null;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    if (videoRef.value) {
      videoRef.value.srcObject = stream;
    }
  } catch (err: any) {
    cameraError.value = `Failed to acquire camera feed: ${err.name || 'NotAllowedError'}: ${err.message || 'The request is not allowed by the user agent or platform context.'}`;
  }
}

const desktopIcons = reactive<DesktopIcon[]>([
  { id: 'icon-detector', name: 'FaceDetector.exe', type: 'detector', x: 20, y: 20, targetWindow: 'detector' },
  { id: 'icon-word', name: 'Sleep_Guide.docx', type: 'word', x: 20, y: 110, targetWindow: 'wordDoc' },
  { id: 'icon-github', name: 'Source Code', type: 'github', x: 20, y: 200, targetWindow: 'githubRepo' },
  { id: 'icon-folder', name: 'Sleep Facts', type: 'folder', x: 20, y: 290, targetWindow: 'sleepFactsFolder' },
  { id: 'icon-pc', name: 'My Computer', type: 'pc', x: 20, y: 380 },
  { id: 'icon-trash', name: 'Recycle Bin', type: 'trash', x: 20, y: 470, targetWindow: 'recycleBin' }
]);

const trashedIcons = reactive<DesktopIcon[]>([]);
const showFunnyTrashDialog = ref(false);

function restoreAllTrashedIcons() {
  trashedIcons.forEach(icon => {
    desktopIcons.push(icon);
  });
  trashedIcons.length = 0;
}

function emptyRecycleBin() {
  trashedIcons.length = 0;
}

const windows = reactive<Record<string, WindowState>>({
  detector: {
    id: 'detector',
    title: 'FaceDetector.exe - Drowsiness Monitor',
    isOpen: true,
    isMinimized: false,
    isMaximized: false,
    x: 160,
    y: 30,
    width: 490,
    height: 610,
    prevX: 160,
    prevY: 30,
    prevWidth: 490,
    prevHeight: 610,
    zIndex: 10
  },
  wordDoc: {
    id: 'wordDoc',
    title: 'Sleep_Guide.docx - Microsoft Word',
    isOpen: false,
    isMinimized: false,
    isMaximized: false,
    x: 220,
    y: 50,
    width: 620,
    height: 520,
    prevX: 220,
    prevY: 50,
    prevWidth: 620,
    prevHeight: 520,
    zIndex: 11
  },
  githubRepo: {
    id: 'githubRepo',
    title: 'Repository - Source Code',
    isOpen: false,
    isMinimized: false,
    isMaximized: false,
    x: 280,
    y: 80,
    width: 540,
    height: 420,
    prevX: 280,
    prevY: 80,
    prevWidth: 540,
    prevHeight: 420,
    zIndex: 12
  },
  sleepFactsFolder: {
    id: 'sleepFactsFolder',
    title: 'C:\\Documents and Settings\\Dev\\Sleep_Facts',
    isOpen: false,
    isMinimized: false,
    isMaximized: false,
    x: 240,
    y: 90,
    width: 520,
    height: 400,
    prevX: 240,
    prevY: 90,
    prevWidth: 520,
    prevHeight: 400,
    zIndex: 13
  },
  recycleBin: {
    id: 'recycleBin',
    title: 'Recycle Bin',
    isOpen: false,
    isMinimized: false,
    isMaximized: false,
    x: 260,
    y: 100,
    width: 520,
    height: 380,
    prevX: 260,
    prevY: 100,
    prevWidth: 520,
    prevHeight: 380,
    zIndex: 14
  }
});

function focusWindow(id: string) {
  activeZIndex.value += 1;
  windows[id].zIndex = activeZIndex.value;
  windows[id].isMinimized = false;
}

function closeWindow(id: string) {
  windows[id].isOpen = false;
  if (id === 'detector') {
    isTracking.value = false;
    stopAlarmSound();
  }
}

function minimizeWindow(id: string) {
  windows[id].isMinimized = true;
}

function toggleMaximizeWindow(id: string) {
  const win = windows[id];
  win.isMaximized = !win.isMaximized;
  if (win.isMaximized) {
    win.prevX = win.x;
    win.prevY = win.y;
    win.prevWidth = win.width;
    win.prevHeight = win.height;
    win.x = 0;
    win.y = 0;
    win.width = window.innerWidth;
    win.height = window.innerHeight - 34;
  } else {
    win.x = win.prevX;
    win.y = win.prevY;
    win.width = win.prevWidth;
    win.height = win.prevHeight;
  }
}

function openWindow(id: string) {
  if (id === 'githubRepo') {
    window.open('https://github.com/whooslizi/DrowsinessDetector', '_blank');
    return;
  }
  if (!windows[id]) return;
  windows[id].isOpen = true;
  windows[id].isMinimized = false;
  focusWindow(id);
  if (id === 'detector') {
    isTracking.value = true;
  }
}

let draggingWindowId: string | null = null;
let dragOffsetX = 0;
let dragOffsetY = 0;

function startWindowDrag(id: string, e: MouseEvent) {
  if (windows[id].isMaximized) return;
  focusWindow(id);
  draggingWindowId = id;
  dragOffsetX = e.clientX - windows[id].x;
  dragOffsetY = e.clientY - windows[id].y;
  window.addEventListener('mousemove', onWindowDrag);
  window.addEventListener('mouseup', stopWindowDrag);
}

function onWindowDrag(e: MouseEvent) {
  if (!draggingWindowId) return;
  windows[draggingWindowId].x = Math.max(0, e.clientX - dragOffsetX);
  windows[draggingWindowId].y = Math.max(0, e.clientY - dragOffsetY);
}

function stopWindowDrag() {
  draggingWindowId = null;
  window.removeEventListener('mousemove', onWindowDrag);
  window.removeEventListener('mouseup', stopWindowDrag);
}

let resizingWindowId: string | null = null;
let resizeStartX = 0;
let resizeStartY = 0;
let resizeStartWidth = 0;
let resizeStartHeight = 0;

function startResize(id: string, e: MouseEvent) {
  if (windows[id].isMaximized) return;
  focusWindow(id);
  resizingWindowId = id;
  resizeStartX = e.clientX;
  resizeStartY = e.clientY;
  resizeStartWidth = windows[id].width;
  resizeStartHeight = windows[id].height;
  window.addEventListener('mousemove', onResize);
  window.addEventListener('mouseup', stopResize);
}

function onResize(e: MouseEvent) {
  if (!resizingWindowId) return;
  const newWidth = Math.max(340, resizeStartWidth + (e.clientX - resizeStartX));
  const newHeight = Math.max(260, resizeStartHeight + (e.clientY - resizeStartY));
  windows[resizingWindowId].width = newWidth;
  windows[resizingWindowId].height = newHeight;
}

function stopResize() {
  resizingWindowId = null;
  window.removeEventListener('mousemove', onResize);
  window.removeEventListener('mouseup', stopResize);
}

let draggingIconId: string | null = null;
let iconDragOffsetX = 0;
let iconDragOffsetY = 0;

function startIconDrag(icon: DesktopIcon, e: MouseEvent) {
  draggingIconId = icon.id;
  iconDragOffsetX = e.clientX - icon.x;
  iconDragOffsetY = e.clientY - icon.y;
  window.addEventListener('mousemove', onIconDrag);
  window.addEventListener('mouseup', stopIconDrag);
}

function onIconDrag(e: MouseEvent) {
  if (!draggingIconId) return;
  const icon = desktopIcons.find(i => i.id === draggingIconId);
  if (icon) {
    icon.x = Math.max(0, Math.min(window.innerWidth - 80, e.clientX - iconDragOffsetX));
    icon.y = Math.max(0, Math.min(window.innerHeight - 100, e.clientY - iconDragOffsetY));
  }
}

function stopIconDrag() {
  if (draggingIconId) {
    const draggedIcon = desktopIcons.find(i => i.id === draggingIconId);
    const trashIcon = desktopIcons.find(i => i.type === 'trash');

    if (draggedIcon && trashIcon && draggedIcon.id !== trashIcon.id) {
      const dist = Math.hypot(draggedIcon.x - trashIcon.x, draggedIcon.y - trashIcon.y);
      if (dist < 65) {
        if (draggedIcon.type === 'detector') {
          showFunnyTrashDialog.value = true;
          draggedIcon.x = 20;
          draggedIcon.y = 20;
        } else {
          trashedIcons.push({ ...draggedIcon });
          const index = desktopIcons.findIndex(i => i.id === draggedIcon.id);
          if (index !== -1) {
            desktopIcons.splice(index, 1);
          }
        }
      }
    }
  }

  draggingIconId = null;
  window.removeEventListener('mousemove', onIconDrag);
  window.removeEventListener('mouseup', stopIconDrag);
}

const isStartMenuOpen = ref(false);
const currentTime = ref('');

function updateClock() {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const videoRef = ref<HTMLVideoElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);

const isTracking = ref(true);
const earThreshold = ref(0.18);
const drowsyTimeout = ref(2.0);

const telemetry = ref<TelemetryData>({
  ear_left: 0.0,
  ear_right: 0.0,
  ear_avg: 0.0,
  eyes_closed: false,
  closed_duration: 0.0,
  is_drowsy: false,
  face_detected: false,
  left_eye_coords: [],
  right_eye_coords: []
});

const progressPercent = computed(() => {
  return Math.min(100, (telemetry.value.closed_duration / drowsyTimeout.value) * 100);
});

const TENOR_BABY_MEME = "https://media.tenor.com/yHV9VvH2hZkAAAAC/crying-baby.gif";

let audioCtx: AudioContext | null = null;
let alarmOscillator: OscillatorNode | null = null;

function playAlarmSound() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  if (alarmOscillator) return;

  alarmOscillator = audioCtx.createOscillator();
  const gainNode = audioCtx.createGain();
  alarmOscillator.type = 'sawtooth';
  alarmOscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
  alarmOscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.3);
  gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);

  alarmOscillator.connect(gainNode);
  gainNode.connect(audioCtx.destination);
  alarmOscillator.start();
}

function stopAlarmSound() {
  if (alarmOscillator) {
    try {
      alarmOscillator.stop();
      alarmOscillator.disconnect();
    } catch (e) {}
    alarmOscillator = null;
  }
}

const LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380];
const RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144];

function getEyeEAR(landmarks: any[], indices: number[], w: number, h: number): [number, [number, number][]] {
  const coords: [number, number][] = indices.map((idx) => [
    landmarks[idx].x * w,
    landmarks[idx].y * h
  ]);
  const [p1, p2, p3, p4, p5, p6] = coords;
  const v1 = Math.hypot(p2[0] - p6[0], p2[1] - p6[1]);
  const v2 = Math.hypot(p3[0] - p5[0], p3[1] - p5[1]);
  const horizontal = Math.hypot(p1[0] - p4[0], p1[1] - p4[1]);

  if (horizontal < 1e-6) return [0, coords];
  const ear = (v1 + v2) / (2.0 * horizontal);
  return [ear, coords];
}

let eyesClosedStartTime: number | null = null;
let smoothedEar = 0;

function onFaceMeshResults(results: any) {
  if (!canvasRef.value || !isTracking.value) return;
  const w = canvasRef.value.width;
  const h = canvasRef.value.height;
  const ctx = canvasRef.value.getContext('2d');
  if (!ctx) return;

  ctx.clearRect(0, 0, w, h);

  if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
    telemetry.value.face_detected = false;
    eyesClosedStartTime = null;
    telemetry.value.eyes_closed = false;
    telemetry.value.closed_duration = 0.0;
    telemetry.value.is_drowsy = false;
    stopAlarmSound();
    return;
  }

  telemetry.value.face_detected = true;
  const landmarks = results.multiFaceLandmarks[0];

  const [earL, leftCoords] = getEyeEAR(landmarks, LEFT_EYE_INDICES, w, h);
  const [earR, rightCoords] = getEyeEAR(landmarks, RIGHT_EYE_INDICES, w, h);
  const rawEarAvg = (earL + earR) / 2.0;

  if (smoothedEar === 0) smoothedEar = rawEarAvg;
  else smoothedEar = smoothedEar * 0.65 + rawEarAvg * 0.35;

  telemetry.value.ear_left = earL;
  telemetry.value.ear_right = earR;
  telemetry.value.ear_avg = smoothedEar;
  telemetry.value.left_eye_coords = leftCoords;
  telemetry.value.right_eye_coords = rightCoords;

  ctx.fillStyle = '#00FF66';
  ctx.strokeStyle = '#00FF66';
  ctx.lineWidth = 1.5;

  [leftCoords, rightCoords].forEach((pts) => {
    ctx.beginPath();
    pts.forEach(([x, y], i) => {
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      ctx.fillRect(x - 2, y - 2, 4, 4);
    });
    ctx.closePath();
    ctx.stroke();
  });

  const now = performance.now();
  if (smoothedEar < earThreshold.value) {
    telemetry.value.eyes_closed = true;
    if (eyesClosedStartTime === null) {
      eyesClosedStartTime = now;
    }
    const duration = (now - eyesClosedStartTime) / 1000.0;
    telemetry.value.closed_duration = duration;

    if (duration >= drowsyTimeout.value) {
      telemetry.value.is_drowsy = true;
      playAlarmSound();
    }
  } else {
    eyesClosedStartTime = null;
    telemetry.value.eyes_closed = false;
    telemetry.value.closed_duration = 0.0;
    telemetry.value.is_drowsy = false;
    stopAlarmSound();
  }
}

onMounted(() => {
  updateClock();
  setInterval(updateClock, 1000);

  const setupMediaPipe = async () => {
    const FaceMesh = (window as any).FaceMesh;
    const Camera = (window as any).Camera;

    if (!FaceMesh || !Camera || !videoRef.value) {
      setTimeout(setupMediaPipe, 300);
      return;
    }

    const faceMesh = new FaceMesh({
      locateFile: (file: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
    });

    faceMesh.setOptions({
      maxNumFaces: 1,
      refineLandmarks: true,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });

    faceMesh.onResults(onFaceMeshResults);

    const camera = new Camera(videoRef.value, {
      onFrame: async () => {
        if (videoRef.value && isTracking.value) {
          try {
            await faceMesh.send({ image: videoRef.value });
          } catch (_) {}
        }
      },
      width: 640,
      height: 480
    });

    try {
      const p = camera.start();
      if (p && typeof p.catch === 'function') {
        p.catch((err: any) => {
          cameraError.value = `Failed to acquire camera feed: ${err.name || 'NotAllowedError'}: ${err.message || 'The request is not allowed by the user agent or platform context.'}`;
        });
      }
      cameraError.value = null;
    } catch (err: any) {
      cameraError.value = `Failed to acquire camera feed: ${err.name || 'NotAllowedError'}: ${err.message || 'The request is not allowed by the user agent or platform context.'}`;
    }

    videoRef.value.onloadedmetadata = () => {
      if (canvasRef.value && videoRef.value) {
        canvasRef.value.width = videoRef.value.videoWidth;
        canvasRef.value.height = videoRef.value.videoHeight;
      }
    };
  };

  setupMediaPipe();
});

function toggleTracking() {
  isTracking.value = !isTracking.value;
  if (!isTracking.value) {
    stopAlarmSound();
    telemetry.value.is_drowsy = false;
  }
}

function onEarInput(e: Event) {
  earThreshold.value = parseFloat((e.target as HTMLInputElement).value);
}

function onTimeInput(e: Event) {
  drowsyTimeout.value = parseFloat((e.target as HTMLInputElement).value);
}
</script>

<template>
  <div class="xp-desktop" @click="isStartMenuOpen = false">

    <!-- DRAGGABLE DESKTOP ICONS WITH CLEAN SVG GRAPHICS -->
    <div
      v-for="icon in desktopIcons"
      :key="icon.id"
      class="xp-icon"
      :style="{ left: icon.x + 'px', top: icon.y + 'px' }"
      @mousedown.prevent="startIconDrag(icon, $event)"
      @dblclick="icon.targetWindow && openWindow(icon.targetWindow)"
    >
      <!-- 1. Authentic 3D Webcam / Eye Icon for FaceDetector -->
      <svg v-if="icon.type === 'detector'" viewBox="0 0 48 48" width="48" height="48">
        <ellipse cx="24" cy="40" rx="14" ry="4" fill="#37474F"/>
        <rect x="22" y="28" width="4" height="10" fill="#546E7A"/>
        <circle cx="24" cy="20" r="14" fill="url(#camSphereGrad)" stroke="#37474F" stroke-width="1.5"/>
        <circle cx="24" cy="20" r="8" fill="#1A237E" stroke="#0D47A1" stroke-width="1"/>
        <circle cx="24" cy="20" r="5" fill="#000000"/>
        <circle cx="21" cy="17" r="2.5" fill="#FFFFFF" opacity="0.8"/>
        <circle cx="30" cy="12" r="1.5" fill="#4CAF50"/>
        <defs>
          <linearGradient id="camSphereGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#ECEFF1"/>
            <stop offset="50%" stop-color="#90A4AE"/>
            <stop offset="100%" stop-color="#37474F"/>
          </linearGradient>
        </defs>
      </svg>

      <!-- 2. Authentic 3D MS Word Document Icon -->
      <svg v-else-if="icon.type === 'word'" viewBox="0 0 48 48" width="48" height="48">
        <path d="M 10 4 L 32 4 L 42 14 L 42 42 C 42 44, 40 46, 38 46 L 10 46 C 8 46, 6 44, 6 42 L 6 8 C 6 6, 8 4, 10 4 Z" fill="#FFFFFF" stroke="#78909C" stroke-width="1.5"/>
        <path d="M 32 4 L 32 14 L 42 14 Z" fill="#CFD8DC" stroke="#78909C" stroke-width="1"/>
        <rect x="4" y="14" width="24" height="26" rx="2" fill="#1565C0" stroke="#0D47A1" stroke-width="1.5"/>
        <text x="8" y="34" fill="#FFFFFF" font-family="Georgia, serif" font-size="20" font-weight="bold">W</text>
        <line x1="30" y1="20" x2="38" y2="20" stroke="#90A4AE" stroke-width="2" stroke-linecap="round"/>
        <line x1="30" y1="26" x2="38" y2="26" stroke="#90A4AE" stroke-width="2" stroke-linecap="round"/>
        <line x1="30" y1="32" x2="36" y2="32" stroke="#90A4AE" stroke-width="2" stroke-linecap="round"/>
      </svg>

      <!-- 3. Authentic 3D GitHub Source Code Icon -->
      <svg v-else-if="icon.type === 'github'" viewBox="0 0 48 48" width="48" height="48">
        <path d="M 10 4 L 32 4 L 42 14 L 42 42 C 42 44, 40 46, 38 46 L 10 46 C 8 46, 6 44, 6 42 L 6 8 C 6 6, 8 4, 10 4 Z" fill="#FFFFFF" stroke="#78909C" stroke-width="1.5"/>
        <path d="M 32 4 L 32 14 L 42 14 Z" fill="#CFD8DC" stroke="#78909C" stroke-width="1"/>
        <circle cx="24" cy="28" r="12" fill="#161B22"/>
        <path d="M 24 19 C 19 19 15 23 15 28 C 15 32 17.5 35.3 21 36.5 C 21.5 36.6 21.7 36.4 21.7 36.1 C 21.7 35.9 21.7 35.1 21.7 34.3 C 19.5 34.8 18.8 33.9 18.6 33.3 C 18.5 33 18 32.2 17.6 32 C 17.3 31.8 16.8 31.4 17.6 31.4 C 18.3 31.4 18.8 32 19 32.3 C 19.8 33.6 21 33.3 21.5 33 C 21.6 32.5 21.8 32.1 22 31.8 C 20 31.6 18 30.8 18 27.4 C 18 26.4 18.4 25.6 19 25 C 18.9 24.7 18.6 23.8 19.1 22.5 C 19.1 22.5 20 22.2 22 23.5 C 22.9 23.3 23.9 23.2 24.9 23.2 C 25.9 23.2 26.9 23.3 27.8 23.5 C 29.8 22.2 30.7 22.5 30.7 22.5 C 31.2 23.8 30.9 24.7 30.8 25 C 31.4 25.6 31.8 26.4 31.8 27.4 C 31.8 30.8 29.8 31.6 27.8 31.8 C 28.1 32.1 28.4 32.6 28.4 33.5 C 28.4 34.8 28.4 35.8 28.4 36.1 C 28.4 36.4 28.6 36.6 29.1 36.5 C 32.6 35.3 35.1 32 35.1 28 C 35.1 23 31.1 19 24.9 19 Z" fill="#FFFFFF"/>
      </svg>

      <!-- 4. Authentic 3D Windows Explorer Folder Icon -->
      <svg v-else-if="icon.type === 'folder'" viewBox="0 0 48 48" width="48" height="48">
        <path d="M 6 12 C 6 10, 8 8, 10 8 L 20 8 L 24 12 L 38 12 C 40 12, 42 14, 42 16 L 42 36 C 42 38, 40 40, 38 40 L 10 40 C 8 40, 6 38, 6 36 Z" fill="#E65100" stroke="#BF360C" stroke-width="1"/>
        <path d="M 8 14 C 8 12, 10 10, 12 10 L 19 10 L 23 14 L 38 14 C 40 14, 40 16, 40 16 L 40 36 C 40 37, 39 38, 38 38 L 10 38 C 9 38, 8 37, 8 36 Z" fill="#F57C00"/>
        <path d="M 4 18 C 4 16, 6 15, 8 15 L 40 15 C 42 15, 44 17, 44 19 L 42 38 C 42 40, 40 41, 38 41 L 10 41 C 8 41, 6 40, 5 38 Z" fill="url(#folderGradDesktop)" stroke="#E65100" stroke-width="1.5"/>
        <defs>
          <linearGradient id="folderGradDesktop" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#FFD54F"/>
            <stop offset="100%" stop-color="#FFB300"/>
          </linearGradient>
        </defs>
      </svg>

      <!-- 5. Authentic 3D My Computer Icon -->
      <svg v-else-if="icon.type === 'pc'" viewBox="0 0 48 48" width="48" height="48">
        <ellipse cx="20" cy="38" rx="10" ry="3" fill="#B0BEC5" stroke="#37474F" stroke-width="1.5"/>
        <rect x="18" y="32" width="4" height="7" fill="#CFD8DC" stroke="#37474F" stroke-width="1.5"/>
        <rect x="4" y="8" width="30" height="25" rx="3" fill="#ECEFF1" stroke="#37474F" stroke-width="2"/>
        <rect x="7" y="11" width="24" height="19" rx="1" fill="#0055EA" />
        <path d="M 7 11 L 22 11 L 7 26 Z" fill="rgba(255,255,255,0.25)"/>
        <rect x="30" y="14" width="14" height="24" rx="1" fill="#ECEFF1" stroke="#37474F" stroke-width="2"/>
        <rect x="33" y="17" width="8" height="3" fill="#90A4AE"/>
        <rect x="33" y="22" width="8" height="2" fill="#78909C"/>
        <circle cx="37" cy="30" r="1.5" fill="#4CAF50"/>
        <circle cx="37" cy="34" r="1" fill="#F44336"/>
      </svg>

      <!-- 6. Authentic 3D Recycle Bin Icon -->
      <svg v-else-if="icon.type === 'trash'" viewBox="0 0 48 48" width="48" height="48">
        <path d="M 12 14 L 15 42 C 15 44, 33 44, 33 42 L 36 14 Z" fill="url(#binGradDesktop)" stroke="#546E7A" stroke-width="2"/>
        <ellipse cx="24" cy="14" rx="12" ry="4" fill="#B0BEC5" stroke="#546E7A" stroke-width="2"/>
        <path d="M 21 22 L 27 22 L 24 17 Z" fill="#4CAF50"/>
        <path d="M 24 24 L 28 30 L 31 25 Z" fill="#43A047"/>
        <path d="M 22 30 L 17 25 L 20 20 Z" fill="#388E3C"/>
        <defs>
          <linearGradient id="binGradDesktop" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#E0F7FA" stop-opacity="0.8"/>
            <stop offset="100%" stop-color="#80DEEA" stop-opacity="0.6"/>
          </linearGradient>
        </defs>
      </svg>

      <span class="icon-label">{{ icon.name }}</span>
    </div>

    <!-- 1. FACEDETECTOR.EXE CLASSIC WINDOWS DIALOG WINDOW -->
    <div
      v-if="windows.detector.isOpen && !windows.detector.isMinimized"
      class="xp-window"
      :style="{
        left: windows.detector.x + 'px',
        top: windows.detector.y + 'px',
        width: windows.detector.width + 'px',
        height: windows.detector.height + 'px',
        zIndex: windows.detector.zIndex
      }"
      @mousedown="focusWindow('detector')"
    >
      <div class="xp-title-bar" @mousedown.prevent="startWindowDrag('detector', $event)">
        <div class="title-left">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#FFFFFF" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" fill="#93C5FD" />
          </svg>
          <span class="title-text">FaceDetector.exe</span>
        </div>
        <div class="xp-win-controls">
          <button class="xp-btn min-btn" @click.stop="minimizeWindow('detector')">_</button>
          <button class="xp-btn max-btn" @click.stop="toggleMaximizeWindow('detector')">□</button>
          <button class="xp-btn close-btn" @click.stop="closeWindow('detector')">✕</button>
        </div>
      </div>

      <div class="xp-menu-bar">
        <span>File</span><span>Options</span><span>View</span><span>Help</span>
      </div>

      <div class="xp-window-body classic-xp-dialog">
        <fieldset class="xp-fieldset">
          <legend class="xp-legend">Webcam Stream</legend>
          <div class="video-container">
            <div class="video-badge">FaceDetector</div>
            <div v-if="cameraError" class="camera-error-overlay">
              <div class="xp-error-dialog-box">
                <div class="xp-error-header">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="#DC2626">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="15" y1="9" x2="9" y2="15" stroke="white" stroke-width="2"/>
                    <line x1="9" y1="9" x2="15" y2="15" stroke="white" stroke-width="2"/>
                  </svg>
                  <span>Camera Access Error</span>
                </div>
                <div class="xp-error-body">
                  <p class="error-msg-text">{{ cameraError }}</p>
                  <p class="error-sub-text">Please check camera permissions in your browser or macOS Privacy Settings.</p>
                  <button class="xp-dialog-btn" @click="requestCameraPermission">Retry Camera Access</button>
                </div>
              </div>
            </div>
            <video ref="videoRef" autoplay playsinline muted></video>
            <canvas ref="canvasRef"></canvas>
          </div>
        </fieldset>

        <fieldset class="xp-fieldset">
          <legend class="xp-legend">System Telemetry & Controls</legend>

          <div class="status-badges">
            <div :class="['xp-status-box critical', { active: telemetry.is_drowsy }]">
              CRITICAL - Continuous Eye Closure Detected
            </div>
            <div :class="['xp-status-box warning', { active: telemetry.eyes_closed && !telemetry.is_drowsy }]">
              HIGH - Eyes Closed Warning
            </div>
          </div>

          <div class="xp-progress-channel">
            <div class="xp-progress-fill" :style="{ width: progressPercent + '%' }"></div>
            <span class="progress-val">{{ telemetry.closed_duration.toFixed(1) }}s</span>
          </div>

          <div class="classic-metrics-table">
            <div class="metric-row">
              <span class="m-label">EYES:</span>
              <span class="m-val" :style="{ color: telemetry.eyes_closed ? '#D32F2F' : '#2E7D32' }">
                {{ telemetry.eyes_closed ? 'CLOSED' : 'OPEN' }}
              </span>
            </div>
            <div class="metric-row">
              <span class="m-label">DANGER LEVEL:</span>
              <span class="m-val" :style="{ color: telemetry.is_drowsy ? '#D32F2F' : telemetry.eyes_closed ? '#F57C00' : '#2E7D32' }">
                {{ telemetry.is_drowsy ? 'CRITICAL' : telemetry.eyes_closed ? 'HIGH' : 'SAFE' }}
              </span>
            </div>
            <div class="metric-row">
              <span class="m-label">CLOSED DURATION:</span>
              <span class="m-val">{{ telemetry.closed_duration.toFixed(1) }}s</span>
            </div>
          </div>

          <div class="xp-sunken-field">
            EAR: {{ telemetry.ear_avg.toFixed(3) }} | threshold: {{ earThreshold.toFixed(2) }}
          </div>

          <div class="controls-panel">
            <div class="button-group">
              <button @click="toggleTracking" class="win-dialog-btn default-btn">
                {{ isTracking ? 'Pause Tracking' : 'Start Tracking' }}
              </button>
              <button @click="openWindow('wordDoc')" class="win-dialog-btn">
                Sleep Guide Doc
              </button>
            </div>

            <div class="sliders-grid">
              <div class="slider-row">
                <label>EAR Sensitivity: {{ earThreshold.toFixed(2) }}</label>
                <input type="range" min="0.12" max="0.28" step="0.01" :value="earThreshold" @input="onEarInput">
              </div>
              <div class="slider-row">
                <label>Trigger Timeout: {{ drowsyTimeout.toFixed(1) }}s</label>
                <input type="range" min="1.0" max="5.0" step="0.5" :value="drowsyTimeout" @input="onTimeInput">
              </div>
            </div>
          </div>
        </fieldset>
      </div>

      <div class="xp-resize-handle" @mousedown.prevent.stop="startResize('detector', $event)"></div>
    </div>

    <!-- 2. MICROSOFT WORD SLEEP TYPES & FACTS DOCUMENT WINDOW -->
    <div
      v-if="windows.wordDoc.isOpen && !windows.wordDoc.isMinimized"
      class="xp-window word-window"
      :style="{
        left: windows.wordDoc.x + 'px',
        top: windows.wordDoc.y + 'px',
        width: windows.wordDoc.width + 'px',
        height: windows.wordDoc.height + 'px',
        zIndex: windows.wordDoc.zIndex
      }"
      @mousedown="focusWindow('wordDoc')"
    >
      <div class="xp-title-bar" @mousedown.prevent="startWindowDrag('wordDoc', $event)">
        <div class="title-left">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="#93C5FD">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
            <path d="M14 2v6h6" fill="#FFFFFF"/>
            <text x="7" y="18" fill="#1E40AF" font-size="9" font-weight="bold">W</text>
          </svg>
          <span class="title-text">Sleep_Guide.docx - Microsoft Word</span>
        </div>
        <div class="xp-win-controls">
          <button class="xp-btn min-btn" @click.stop="minimizeWindow('wordDoc')">_</button>
          <button class="xp-btn max-btn" @click.stop="toggleMaximizeWindow('wordDoc')">□</button>
          <button class="xp-btn close-btn" @click.stop="closeWindow('wordDoc')">✕</button>
        </div>
      </div>

      <div class="word-toolbar">
        <div class="word-menu-row">
          <span>File</span><span>Edit</span><span>View</span><span>Insert</span><span>Format</span><span>Tools</span><span>Table</span><span>Window</span><span>Help</span>
        </div>
        <div class="word-formatting-bar">
          <select class="font-select"><option>Times New Roman</option><option>Arial</option></select>
          <select class="size-select"><option>12pt</option><option>14pt</option></select>
          <button class="word-icon-btn">B</button>
          <button class="word-icon-btn">I</button>
          <button class="word-icon-btn">U</button>
        </div>
      </div>

      <div class="word-document-canvas">
        <div class="word-page-paper">
          <h1 class="doc-title">Sleep Architecture & Drowsiness Science Guide</h1>
          <hr class="doc-divider" />

          <h2>1. Fundamental Sleep Stages</h2>
          <p>
            Human sleep is divided into NREM (Non-Rapid Eye Movement) and REM (Rapid Eye Movement) sleep.
          </p>
          <ul>
            <li><strong>Stage N1 (Light Sleep):</strong> 1-7 minutes transition into theta wave brain activity.</li>
            <li><strong>Stage N2 (Baseline Sleep):</strong> ~50% total sleep duration with sleep spindles.</li>
            <li><strong>Stage N3 (Slow-Wave Deep Sleep):</strong> Delta wave physiological restoration.</li>
            <li><strong>REM Sleep (Dreaming):</strong> Brain activation with temporary motor paralysis.</li>
          </ul>

          <h2>2. The 90-Minute Sleep Cycle</h2>
          <p>
            Sleep cycles repeat every 90-110 minutes. Awakening during Stage N3 causes sleep inertia.
          </p>

          <h2>3. Cognitive Fatigue Metrics</h2>
          <p>
            17 hours of wakefulness impairs reaction times equivalent to 0.05% BAC.
          </p>
          <div class="callout-box">
            <strong>Micro-Sleep Definition:</strong><br />
            An involuntary blackout lasting 1-15 seconds where visual processing suspends.
          </div>
        </div>
      </div>

      <div class="xp-resize-handle" @mousedown.prevent.stop="startResize('wordDoc', $event)"></div>
    </div>

    <!-- 3. GITHUB SOURCE CODE WINDOW -->
    <div
      v-if="windows.githubRepo.isOpen && !windows.githubRepo.isMinimized"
      class="xp-window github-window"
      :style="{
        left: windows.githubRepo.x + 'px',
        top: windows.githubRepo.y + 'px',
        width: windows.githubRepo.width + 'px',
        height: windows.githubRepo.height + 'px',
        zIndex: windows.githubRepo.zIndex
      }"
      @mousedown="focusWindow('githubRepo')"
    >
      <div class="xp-title-bar" @mousedown.prevent="startWindowDrag('githubRepo', $event)">
        <div class="title-left">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="#FFFFFF">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          <span class="title-text">Repository - Source Code</span>
        </div>
        <div class="xp-win-controls">
          <button class="xp-btn min-btn" @click.stop="minimizeWindow('githubRepo')">_</button>
          <button class="xp-btn max-btn" @click.stop="toggleMaximizeWindow('githubRepo')">□</button>
          <button class="xp-btn close-btn" @click.stop="closeWindow('githubRepo')">✕</button>
        </div>
      </div>

      <div class="github-body">
        <div class="repo-card">
          <div class="repo-header">
            <div>
              <h3>whooslizi/DrowsinessDetector</h3>
              <p>Facial Landmark Eye Aspect Ratio (EAR) Monitor System</p>
            </div>
            <a href="https://github.com/whooslizi/DrowsinessDetector" target="_blank" class="repo-link-btn">
              Open Repository
            </a>
          </div>
          <div class="readme-preview">
            <pre>
Repository URL: https://github.com/whooslizi/DrowsinessDetector

DrowsinessDetector System Architecture
Real-time facial landmark tracking & Eye Aspect Ratio (EAR) monitor 
built with Vue 3, MediaPipe FaceMesh, OpenCV, and PyWebView.
            </pre>
          </div>
        </div>
      </div>

      <div class="xp-resize-handle" @mousedown.prevent.stop="startResize('githubRepo', $event)"></div>
    </div>

    <!-- 4. SLEEP FACTS EXPLORER FOLDER WINDOW -->
    <div
      v-if="windows.sleepFactsFolder.isOpen && !windows.sleepFactsFolder.isMinimized"
      class="xp-window explorer-window"
      :style="{
        left: windows.sleepFactsFolder.x + 'px',
        top: windows.sleepFactsFolder.y + 'px',
        width: windows.sleepFactsFolder.width + 'px',
        height: windows.sleepFactsFolder.height + 'px',
        zIndex: windows.sleepFactsFolder.zIndex
      }"
      @mousedown="focusWindow('sleepFactsFolder')"
    >
      <div class="xp-title-bar" @mousedown.prevent="startWindowDrag('sleepFactsFolder', $event)">
        <div class="title-left">
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" fill="#FDE047"/>
          </svg>
          <span class="title-text">C:\Documents and Settings\Dev\Sleep_Facts</span>
        </div>
        <div class="xp-win-controls">
          <button class="xp-btn min-btn" @click.stop="minimizeWindow('sleepFactsFolder')">_</button>
          <button class="xp-btn max-btn" @click.stop="toggleMaximizeWindow('sleepFactsFolder')">□</button>
          <button class="xp-btn close-btn" @click.stop="closeWindow('sleepFactsFolder')">✕</button>
        </div>
      </div>

      <div class="xp-menu-bar">
        <span>File</span><span>Edit</span><span>View</span><span>Favorites</span><span>Tools</span><span>Help</span>
      </div>

      <div class="explorer-body">
        <div class="explorer-sidebar">
          <div class="sidebar-title">Tasks</div>
          <ul>
            <li>Open Sleep Guide</li>
          </ul>
        </div>

        <div class="explorer-files">
          <div class="xp-file-item" @dblclick="openWindow('wordDoc')">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="#1E40AF">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="#2563EB"/>
              <path d="M14 2v6h6" fill="#93C5FD"/>
              <text x="7" y="18" fill="white" font-size="9" font-weight="bold">W</text>
            </svg>
            <span class="file-name">Sleep_Guide.docx</span>
            <span class="file-size">42 KB</span>
          </div>
          <div class="xp-file-item" @dblclick="openWindow('githubRepo')">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="#181717">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            <span class="file-name">Source_Code.url</span>
            <span class="file-size">1 KB</span>
          </div>
        </div>
      </div>

      <div class="xp-resize-handle" @mousedown.prevent.stop="startResize('sleepFactsFolder', $event)"></div>
    </div>

    <!-- 5. RECYCLE BIN EXPLORER WINDOW -->
    <div
      v-if="windows.recycleBin && windows.recycleBin.isOpen && !windows.recycleBin.isMinimized"
      class="xp-window explorer-window"
      :style="{
        left: windows.recycleBin.x + 'px',
        top: windows.recycleBin.y + 'px',
        width: windows.recycleBin.width + 'px',
        height: windows.recycleBin.height + 'px',
        zIndex: windows.recycleBin.zIndex
      }"
      @mousedown="focusWindow('recycleBin')"
    >
      <div class="xp-title-bar" @mousedown.prevent="startWindowDrag('recycleBin', $event)">
        <div class="title-left">
          <svg viewBox="0 0 48 48" width="16" height="16">
            <path d="M 12 14 L 15 42 C 15 44, 33 44, 33 42 L 36 14 Z" fill="#90A4AE" stroke="#546E7A" stroke-width="2"/>
            <ellipse cx="24" cy="14" rx="12" ry="4" fill="#B0BEC5" stroke="#546E7A" stroke-width="2"/>
          </svg>
          <span class="title-text">Recycle Bin</span>
        </div>
        <div class="xp-win-controls">
          <button class="xp-btn min-btn" @click.stop="minimizeWindow('recycleBin')">_</button>
          <button class="xp-btn max-btn" @click.stop="toggleMaximizeWindow('recycleBin')">□</button>
          <button class="xp-btn close-btn" @click.stop="closeWindow('recycleBin')">✕</button>
        </div>
      </div>

      <div class="xp-menu-bar">
        <span>File</span><span>Edit</span><span>View</span><span>Favorites</span><span>Tools</span><span>Help</span>
      </div>

      <div class="explorer-body">
        <div class="explorer-sidebar">
          <div class="sidebar-title">Recycle Bin Tasks</div>
          <button class="sidebar-action-btn" @click="emptyRecycleBin" :disabled="trashedIcons.length === 0">
            Empty Recycle Bin
          </button>
          <button class="sidebar-action-btn" @click="restoreAllTrashedIcons" :disabled="trashedIcons.length === 0">
            Restore All Items
          </button>
        </div>

        <div class="explorer-files">
          <div v-if="trashedIcons.length === 0" class="empty-bin-notice">
            Recycle Bin is empty.
          </div>
          <div v-for="item in trashedIcons" :key="item.id" class="xp-file-item">
            <svg viewBox="0 0 48 48" width="32" height="32">
              <path d="M 10 4 L 32 4 L 42 14 L 42 42 C 42 44, 40 46, 38 46 L 10 46 C 8 46, 6 44, 6 42 L 6 8 C 6 6, 8 4, 10 4 Z" fill="#FFFFFF" stroke="#78909C" stroke-width="1.5"/>
            </svg>
            <span class="file-name">{{ item.name }}</span>
          </div>
        </div>
      </div>

      <div class="xp-resize-handle" @mousedown.prevent.stop="startResize('recycleBin', $event)"></div>
    </div>

    <!-- FUNNY WINDOWS XP DIALOG WHEN TRYING TO TRASH FACEDETECTOR -->
    <div v-if="showFunnyTrashDialog" class="xp-dialog-modal-backdrop" @click.self="showFunnyTrashDialog = false">
      <div class="xp-dialog-window">
        <div class="xp-title-bar">
          <div class="title-left">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="#F59E0B">
              <path d="M12 2L1 21h22L12 2zm1 14h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
            </svg>
            <span class="title-text">FaceDetector.exe - Action Blocked</span>
          </div>
          <div class="xp-win-controls">
            <button class="xp-btn close-btn" @click="showFunnyTrashDialog = false">✕</button>
          </div>
        </div>
        <div class="xp-dialog-content">
          <div class="dialog-icon-row">
            <svg viewBox="0 0 48 48" width="40" height="40" style="flex-shrink:0;">
              <polygon points="24,4 44,40 4,40" fill="#F59E0B" stroke="#D97706" stroke-width="2"/>
              <text x="20" y="32" fill="#FFFFFF" font-size="22" font-weight="bold">!</text>
            </svg>
            <div class="dialog-text-box">
              <p class="dialog-main-msg">Nice try bro, but deleting FaceDetector.exe won't fix your sleep schedule!</p>
              <p class="dialog-sub-msg">Go take a nap bro, zero coding allowed right now.</p>
            </div>
          </div>
          <div class="dialog-buttons-row">
            <button class="xp-dialog-action-btn" @click="showFunnyTrashDialog = false">Go Take A Nap</button>
            <button class="xp-dialog-action-btn secondary" @click="showFunnyTrashDialog = false">Power Nap Mode</button>
          </div>
        </div>
      </div>
    </div>

    <!-- DRAMATIC DROWSY ALARM OVERLAY -->
    <div v-if="telemetry.is_drowsy" class="drowsy-overlay">
      <div class="drowsy-content">
        <h1 class="drowsy-title">WAKE UP BRO</h1>
        <div class="meme-frame">
          <img :src="TENOR_BABY_MEME" alt="Crying Baby Meme" class="tenor-baby-meme" />
        </div>
        <p class="drowsy-msg">Continuous eye closure detected</p>
        <p class="drowsy-foot">OPEN YOUR EYES TO TURN OFF ALARM</p>
      </div>
    </div>

    <!-- WINDOWS XP TASKBAR -->
    <div class="xp-taskbar">
      <button class="xp-start-btn" @click.stop="isStartMenuOpen = !isStartMenuOpen">
        <svg viewBox="0 0 48 48" width="18" height="18" class="start-flag-logo">
          <path fill="#EE3224" d="M 6 10 C 13 8, 19 14, 25 12 L 25 24 C 19 26, 13 20, 6 22 Z" />
          <path fill="#7FBA00" d="M 27 11.5 C 33 9.5, 39 13.5, 44 12 L 44 23.5 C 39 25, 33 21, 27 23 Z" />
          <path fill="#00A4EF" d="M 6 24 C 13 22, 19 28, 25 26 L 25 38 C 19 40, 13 34, 6 36 Z" />
          <path fill="#FFB900" d="M 27 25.5 C 33 23.5, 39 27.5, 44 26 L 44 37.5 C 39 39, 33 35, 27 37 Z" />
        </svg>
        <span>start</span>
      </button>

      <div class="taskbar-tasks">
        <button
          v-if="windows.detector.isOpen"
          :class="['task-tab', { active: !windows.detector.isMinimized }]"
          @click="windows.detector.isMinimized ? openWindow('detector') : minimizeWindow('detector')"
        >
          <svg viewBox="0 0 48 48" width="14" height="14">
            <circle cx="24" cy="20" r="14" fill="#3B82F6"/>
            <circle cx="24" cy="20" r="6" fill="#1D4ED8"/>
          </svg>
          <span>FaceDetector.exe</span>
        </button>

        <button
          v-if="windows.wordDoc.isOpen"
          :class="['task-tab', { active: !windows.wordDoc.isMinimized }]"
          @click="windows.wordDoc.isMinimized ? openWindow('wordDoc') : minimizeWindow('wordDoc')"
        >
          <svg viewBox="0 0 48 48" width="14" height="14">
            <rect x="6" y="6" width="36" height="36" rx="4" fill="#1565C0"/>
            <text x="12" y="32" fill="#FFFFFF" font-family="Georgia" font-size="24" font-weight="bold">W</text>
          </svg>
          <span>Sleep_Guide.docx</span>
        </button>

        <button
          v-if="windows.githubRepo.isOpen"
          :class="['task-tab', { active: !windows.githubRepo.isMinimized }]"
          @click="windows.githubRepo.isMinimized ? openWindow('githubRepo') : minimizeWindow('githubRepo')"
        >
          <svg viewBox="0 0 48 48" width="14" height="14">
            <circle cx="24" cy="24" r="20" fill="#FFFFFF"/>
            <path d="M 24 10 C 16.3 10 10 16.3 10 24 C 10 30.1 14 35.2 19.5 37 C 20.2 37.1 20.5 36.7 20.5 36.3 L 20.5 33.7 C 16.6 34.5 15.8 32 15.8 32 C 15.2 30.4 14.3 30 14.3 30 C 13 29.1 14.4 29.1 14.4 29.1 C 15.8 29.2 16.6 30.5 16.6 30.5 C 17.8 32.6 19.8 32 20.6 31.7 C 20.7 30.8 21.1 30.2 21.5 29.8 C 18.4 29.5 15.1 28.3 15.1 23 C 15.1 21.5 15.6 20.3 16.5 19.3 C 16.4 18.9 15.9 17.5 16.6 15.6 C 16.6 15.6 17.8 15.2 20.5 17.1 C 21.6 16.8 22.8 16.6 24 16.6 C 25.2 16.6 26.4 16.8 27.5 17.1 C 30.2 15.2 31.4 15.6 31.4 15.6 C 32.1 17.5 31.6 18.9 31.5 19.3 C 32.4 20.3 32.9 21.5 32.9 23 C 32.9 28.3 29.6 29.5 26.5 29.8 C 27 30.2 27.5 31.1 27.5 32.5 L 27.5 36.3 C 27.5 36.7 27.8 37.1 28.5 37 C 34 35.2 38 30.1 38 24 C 38 16.3 31.7 10 24 10 Z" fill="#161B22"/>
          </svg>
          <span>Source Code</span>
        </button>
      </div>

      <div class="xp-systray">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="#4ADE80" style="margin-right: 6px;" title="FaceDetector Active">
          <circle cx="12" cy="12" r="8" />
        </svg>
        <svg viewBox="0 0 24 24" width="14" height="14" fill="#93C5FD" style="margin-right: 6px;" title="Volume">
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
        </svg>
        <span class="clock-text">{{ currentTime }}</span>
      </div>
    </div>

    <!-- START MENU -->
    <div v-if="isStartMenuOpen" class="xp-start-menu" @click.stop>
      <div class="start-sidebar">
        <span>Windows XP</span>
      </div>
      <div class="start-items">
        <div class="start-user">
          <svg viewBox="0 0 48 48" width="24" height="24">
            <circle cx="24" cy="24" r="22" fill="#0055EA"/>
            <path d="M 24 12 C 18 12 14 16 14 21 C 14 26 18 29 24 29 C 30 29 34 26 34 21 C 34 16 30 12 24 12 Z" fill="#FFFFFF"/>
            <path d="M 10 40 C 10 32 16 30 24 30 C 32 30 38 32 38 40 Z" fill="#FFFFFF"/>
          </svg>
          <strong>Developer</strong>
        </div>
        <hr />
        <div class="start-menu-item" @click="openWindow('detector'); isStartMenuOpen = false">
          <svg viewBox="0 0 48 48" width="18" height="18">
            <circle cx="24" cy="20" r="14" fill="#3B82F6"/>
            <circle cx="24" cy="20" r="6" fill="#1D4ED8"/>
          </svg>
          <span>FaceDetector.exe</span>
        </div>
        <div class="start-menu-item" @click="openWindow('wordDoc'); isStartMenuOpen = false">
          <svg viewBox="0 0 48 48" width="18" height="18">
            <rect x="6" y="6" width="36" height="36" rx="4" fill="#1565C0"/>
            <text x="12" y="32" fill="#FFFFFF" font-family="Georgia" font-size="24" font-weight="bold">W</text>
          </svg>
          <span>Sleep_Guide.docx</span>
        </div>
        <div class="start-menu-item" @click="openWindow('githubRepo'); isStartMenuOpen = false">
          <svg viewBox="0 0 48 48" width="18" height="18">
            <circle cx="24" cy="24" r="20" fill="#FFFFFF"/>
            <path d="M 24 10 C 16.3 10 10 16.3 10 24 C 10 30.1 14 35.2 19.5 37 C 20.2 37.1 20.5 36.7 20.5 36.3 L 20.5 33.7 C 16.6 34.5 15.8 32 15.8 32 C 15.2 30.4 14.3 30 14.3 30 C 13 29.1 14.4 29.1 14.4 29.1 C 15.8 29.2 16.6 30.5 16.6 30.5 C 17.8 32.6 19.8 32 20.6 31.7 C 20.7 30.8 21.1 30.2 21.5 29.8 C 18.4 29.5 15.1 28.3 15.1 23 C 15.1 21.5 15.6 20.3 16.5 19.3 C 16.4 18.9 15.9 17.5 16.6 15.6 C 16.6 15.6 17.8 15.2 20.5 17.1 C 21.6 16.8 22.8 16.6 24 16.6 C 25.2 16.6 26.4 16.8 27.5 17.1 C 30.2 15.2 31.4 15.6 31.4 15.6 C 32.1 17.5 31.6 18.9 31.5 19.3 C 32.4 20.3 32.9 21.5 32.9 23 C 32.9 28.3 29.6 29.5 26.5 29.8 C 27 30.2 27.5 31.1 27.5 32.5 L 27.5 36.3 C 27.5 36.7 27.8 37.1 28.5 37 C 34 35.2 38 30.1 38 24 C 38 16.3 31.7 10 24 10 Z" fill="#161B22"/>
          </svg>
          <span>Source Code</span>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.xp-desktop {
  width: 100vw;
  height: 100vh;
  position: fixed;
  inset: 0;
  background: url('https://i.imgur.com/Zk6TR5k.jpg') no-repeat center center fixed;
  background-size: cover;
  overflow: hidden;
  user-select: none;
  font-family: Tahoma, sans-serif;
}

.xp-icon {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  width: 90px;
  border: 1px transparent solid;
}
.xp-icon:hover {
  background: rgba(11, 97, 255, 0.35);
  border: 1px dotted rgba(255, 255, 255, 0.8);
}
.xp-icon svg {
  filter: drop-shadow(2px 4px 6px rgba(0, 0, 0, 0.5));
  margin-bottom: 6px;
}

.file-icon-box {
  background: #2563EB;
  color: white;
  font-size: 0.75rem;
  font-weight: bold;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 4px;
}

.icon-label {
  color: white;
  font-size: 0.76rem;
  font-weight: 600;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9);
  font-family: Tahoma, sans-serif;
  word-break: break-word;
}

.xp-window {
  position: absolute;
  background: #ECE9D8;
  border: 3px solid #0055EA;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.xp-resize-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
  background: linear-gradient(135deg, transparent 50%, #808080 50%, #808080 75%, transparent 75%, transparent 100%);
  z-index: 100;
}

.xp-title-bar {
  background: linear-gradient(180deg, #0058EE 0%, #3593FF 10%, #0055EA 100%);
  color: white;
  padding: 6px 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: move;
  font-weight: 700;
  font-size: 0.85rem;
  font-family: Tahoma, sans-serif;
}

.title-left { display: flex; align-items: center; gap: 6px; }

.xp-win-controls { display: flex; gap: 4px; }
.xp-btn {
  width: 20px;
  height: 20px;
  border: 1px solid white;
  border-radius: 3px;
  color: white;
  font-weight: 900;
  font-size: 0.7rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.min-btn { background: #3B82F6; }
.max-btn { background: #3B82F6; }
.close-btn { background: #E81123; }
.close-btn:hover { background: #F43F5E; }

.classic-xp-dialog {
  background: #ECE9D8;
  padding: 12px;
  flex: 1;
  overflow-y: auto;
  font-family: Tahoma, sans-serif;
  color: #000;
}

.xp-fieldset {
  border: 1px solid #D4D0C8;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 10px;
  background: #ECE9D8;
}

.xp-legend {
  font-size: 0.78rem;
  font-weight: bold;
  color: #0055EA;
  padding: 0 6px;
}

.video-container {
  position: relative;
  width: 100%;
  height: 230px;
  background: #000000;
  border: 2px inset #7F9DB9;
  overflow: hidden;
}

.video-badge {
  position: absolute;
  top: 6px; left: 6px;
  background: #000; color: #00FF66;
  font-family: monospace;
  font-size: 0.78rem;
  padding: 2px 6px;
  border-radius: 2px;
  z-index: 10;
}

.camera-error-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
}

.xp-error-dialog-box {
  background: #ECE9D8;
  border: 2px solid #0055EA;
  border-radius: 4px;
  width: 90%;
  max-width: 380px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  font-family: Tahoma, sans-serif;
}

.xp-error-header {
  background: linear-gradient(180deg, #D32F2F 0%, #B71C1C 100%);
  color: white;
  padding: 4px 8px;
  font-size: 0.78rem;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 6px;
}

.xp-error-body {
  padding: 12px;
  text-align: center;
  color: #1F2937;
}

.error-msg-text {
  font-size: 0.75rem;
  font-weight: bold;
  color: #DC2626;
  margin-bottom: 6px;
  word-break: break-word;
}

.error-sub-text {
  font-size: 0.72rem;
  color: #4B5563;
  margin-bottom: 10px;
}

.xp-dialog-btn {
  background: linear-gradient(180deg, #FFFFFF 0%, #ECE9D8 100%);
  border: 1px solid #0055EA;
  border-radius: 3px;
  padding: 4px 12px;
  font-size: 0.75rem;
  font-weight: bold;
  color: #0055EA;
  cursor: pointer;
}
.xp-dialog-btn:hover {
  background: #0055EA;
  color: white;
}

video, canvas { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }

.status-badges { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
.xp-status-box {
  font-size: 0.75rem;
  padding: 4px 8px;
  border-radius: 3px;
  font-weight: bold;
  color: white;
  text-align: center;
  opacity: 0.4;
}
.xp-status-box.active { opacity: 1; }
.xp-status-box.critical { background: #D32F2F; border: 1px solid #9A0007; }
.xp-status-box.warning { background: #F57C00; border: 1px solid #B26A00; }

.xp-progress-channel {
  position: relative;
  width: 100%;
  height: 16px;
  background: #FFFFFF;
  border: 2px inset #7F9DB9;
  margin-bottom: 8px;
  overflow: hidden;
}

.xp-progress-fill {
  height: 100%;
  background: repeating-linear-gradient(
    90deg,
    #2E7D32 0px,
    #2E7D32 8px,
    #ECE9D8 8px,
    #ECE9D8 10px
  );
  transition: width 0.15s ease-out;
}

.progress-val {
  position: absolute;
  right: 6px;
  top: 0;
  font-size: 0.7rem;
  font-weight: bold;
  line-height: 16px;
  color: #000;
}

.classic-metrics-table {
  background: #FFF;
  border: 1px inset #7F9DB9;
  padding: 6px;
  margin-bottom: 8px;
  font-size: 0.78rem;
}

.metric-row { display: flex; justify-content: space-between; padding: 2px 0; }
.m-label { font-weight: bold; color: #333; }
.m-val { font-weight: bold; }

.xp-sunken-field {
  text-align: center;
  font-family: monospace;
  font-size: 0.78rem;
  background: #FFF;
  border: 1px inset #7F9DB9;
  padding: 4px;
  margin-bottom: 8px;
}

.controls-panel { display: flex; flex-direction: column; gap: 8px; }
.button-group { display: flex; gap: 8px; }

.win-dialog-btn {
  flex: 1;
  padding: 6px 12px;
  background: linear-gradient(180deg, #FFFFFF 0%, #ECE9D8 100%);
  border: 1px solid #003C74;
  border-radius: 3px;
  font-weight: bold;
  font-size: 0.78rem;
  cursor: pointer;
  color: #000;
  box-shadow: inset 1px 1px #FFFFFF, inset -1px -1px #B5B5B5;
}
.win-dialog-btn:active { background: #D8D4C0; }
.default-btn { border: 2px solid #0055EA; }

.sliders-grid { display: flex; flex-direction: column; gap: 4px; font-size: 0.72rem; }
.slider-row { display: flex; flex-direction: column; }

.word-toolbar { background: #ECE9D8; border-bottom: 1px solid #B5B5B5; font-size: 0.78rem; }
.word-menu-row { display: flex; gap: 12px; padding: 4px 10px; border-bottom: 1px solid #D4D0C8; }
.word-formatting-bar { display: flex; align-items: center; gap: 6px; padding: 4px 10px; background: #F5F4EA; }
.font-select, .size-select { font-size: 0.75rem; border: 1px solid #94A3B8; border-radius: 2px; }
.word-icon-btn { border: 1px solid #CBD5E1; background: #FFF; padding: 2px 6px; font-size: 0.75rem; cursor: pointer; }

.word-document-canvas {
  background: #808080;
  padding: 16px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  justify-content: center;
}

.word-page-paper {
  background: #FFFFFF;
  width: 100%;
  max-width: 540px;
  padding: 30px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
  font-family: 'Times New Roman', Times, serif;
  color: #111827;
  font-size: 0.9rem;
  line-height: 1.6;
}

.doc-title { font-size: 1.4rem; font-weight: bold; margin-bottom: 4px; color: #1E3A8A; }
.doc-divider { border: 0; border-top: 1px solid #9CA3AF; margin-bottom: 14px; }
.word-page-paper h2 { font-size: 1.05rem; color: #1E40AF; margin-top: 14px; margin-bottom: 6px; }
.word-page-paper ul { padding-left: 20px; margin-bottom: 12px; }
.callout-box { background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 10px; margin: 12px 0; border-radius: 4px; font-size: 0.85rem; }

.github-body { padding: 16px; background: #0D1117; color: #C9D1D9; flex: 1; overflow-y: auto; }
.repo-card { background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 16px; }
.repo-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.repo-header h3 { color: #58A6FF; margin: 0; font-size: 1.1rem; }
.repo-header p { font-size: 0.8rem; color: #8B949E; margin: 2px 0 0; }
.repo-link-btn {
  background: #238636;
  color: #FFFFFF;
  text-decoration: none;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 6px;
  white-space: nowrap;
}
.repo-link-btn:hover { background: #2EA043; }
.readme-preview { background: #0D1117; padding: 10px; border-radius: 6px; margin: 10px 0; border: 1px solid #30363D; }
.readme-preview pre { font-size: 0.72rem; color: #7EE787; font-family: monospace; }

.xp-menu-bar { background: #ECE9D8; border-bottom: 1px solid #CBD5E1; padding: 4px 10px; font-size: 0.78rem; display: flex; gap: 14px; color: #334155; }
.explorer-body { display: flex; flex: 1; background: white; }
.explorer-sidebar { width: 150px; background: #6582F3; padding: 10px; color: white; font-size: 0.78rem; }
.sidebar-title { font-weight: 700; border-bottom: 1px solid rgba(255,255,255,0.4); padding-bottom: 4px; margin-bottom: 6px; }
.explorer-sidebar ul { list-style: none; padding-left: 0; }

.explorer-files { flex: 1; padding: 14px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; align-content: start; }
.xp-file-item { display: flex; flex-direction: column; align-items: center; padding: 8px; cursor: pointer; border-radius: 4px; text-align: center; }
.xp-file-item:hover { background: #E2E8F0; }
.file-name { font-size: 0.72rem; font-weight: 600; margin-top: 2px; }
.file-size { font-size: 0.65rem; color: #64748B; }

.xp-taskbar {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 34px;
  background: linear-gradient(180deg, #245EDC 0%, #1F47B8 100%);
  border-top: 2px solid #3882F6;
  display: flex;
  align-items: center;
  padding: 0 4px;
  z-index: 9000;
}

.xp-start-btn {
  background: linear-gradient(180deg, #388E3C 0%, #2E7D32 100%);
  color: white;
  border: 1px solid #1B5E20;
  border-radius: 0 8px 8px 0;
  padding: 4px 14px;
  font-weight: 900;
  font-style: italic;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.taskbar-tasks { flex: 1; display: flex; gap: 4px; margin: 0 10px; }
.task-tab {
  background: #3C82F6;
  color: white;
  border: 1px solid #1D4ED8;
  border-radius: 3px;
  padding: 3px 10px;
  font-size: 0.78rem;
  cursor: pointer;
}
.task-tab.active { background: #1E40AF; font-weight: 700; }

.xp-systray {
  background: #0F2D87;
  color: white;
  padding: 4px 10px;
  border-left: 1px solid #3B82F6;
  font-size: 0.78rem;
  display: flex;
  align-items: center;
}

.xp-start-menu {
  position: absolute;
  bottom: 34px;
  left: 0;
  width: 250px;
  background: white;
  border: 2px solid #245EDC;
  border-radius: 6px 6px 0 0;
  box-shadow: 0 -8px 24px rgba(0,0,0,0.3);
  display: flex;
  z-index: 9500;
}

.start-sidebar { background: #245EDC; color: white; width: 30px; font-weight: 900; writing-mode: vertical-lr; transform: rotate(180deg); text-align: center; padding: 10px 0; }
.start-items { flex: 1; padding: 10px; font-size: 0.82rem; }
.start-user { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.start-menu-item { display: flex; align-items: center; gap: 8px; padding: 6px; cursor: pointer; border-radius: 4px; }
.start-menu-item:hover { background: #3B82F6; color: white; }

.drowsy-overlay {
  position: fixed; inset: 0;
  background: #D50000;
  z-index: 9999;
  display: flex; justify-content: center; align-items: center;
  text-align: center;
  animation: pulse-bg 0.4s infinite alternate ease-in-out;
  font-family: monospace;
}

@keyframes pulse-bg { 0% { background: #B71C1C; } 100% { background: #FF1744; } }
.drowsy-content { color: #FFFFFF; padding: 24px; }
.drowsy-title { font-size: 3.2rem; font-weight: 900; color: #FFEB3B; margin-bottom: 16px; }
.meme-frame { margin: 16px auto; width: 150px; height: 150px; border-radius: 50%; overflow: hidden; border: 4px solid #FFF; }
.tenor-baby-meme { width: 100%; height: 100%; object-fit: cover; }
.drowsy-msg { font-size: 1.3rem; font-weight: 600; margin-bottom: 10px; }
.drowsy-foot { font-size: 0.9rem; font-weight: 700; color: #FFCDD2; }

.sidebar-action-btn {
  background: #ECE9D8;
  border: 1px solid #7F9DB9;
  border-radius: 3px;
  color: #1E3A8A;
  font-size: 0.72rem;
  font-weight: bold;
  padding: 4px 8px;
  margin-top: 6px;
  width: 100%;
  cursor: pointer;
  text-align: left;
}
.sidebar-action-btn:hover:not(:disabled) {
  background: #3B82F6;
  color: white;
}
.sidebar-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty-bin-notice {
  font-size: 0.8rem;
  color: #64748B;
  padding: 10px;
  font-style: italic;
}

.xp-dialog-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 9800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.xp-dialog-window {
  background: #ECE9D8;
  border: 3px solid #0055EA;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  width: 90%;
  max-width: 440px;
  overflow: hidden;
  font-family: Tahoma, sans-serif;
}

.xp-dialog-content {
  padding: 16px;
}

.dialog-icon-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.dialog-text-box {
  flex: 1;
}

.dialog-main-msg {
  font-size: 0.85rem;
  font-weight: bold;
  color: #111827;
  margin-bottom: 6px;
}

.dialog-sub-msg {
  font-size: 0.78rem;
  color: #4B5563;
}

.dialog-buttons-row {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.xp-dialog-action-btn {
  background: linear-gradient(180deg, #FFFFFF 0%, #ECE9D8 100%);
  border: 1px solid #0055EA;
  border-radius: 3px;
  padding: 5px 14px;
  font-size: 0.78rem;
  font-weight: bold;
  color: #0055EA;
  cursor: pointer;
}
.xp-dialog-action-btn:hover {
  background: #0055EA;
  color: white;
}
.xp-dialog-action-btn.secondary {
  border-color: #6B7280;
  color: #374151;
}
.xp-dialog-action-btn.secondary:hover {
  background: #4B5563;
  color: white;
}
</style>
