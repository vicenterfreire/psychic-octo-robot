import type { IScannerControls } from '@zxing/browser'
import { useEffect, useRef, useState } from 'react'
import styles from '../gate.module.css'

type GateCameraState = 'idle' | 'starting' | 'scanning' | 'captured' | 'error'

interface GateCameraScannerProps {
  disabled: boolean
  onScan: (token: string) => void
}

function cameraErrorMessage(error: unknown): string {
  const errorName =
    typeof error === 'object' && error !== null && 'name' in error
      ? String(error.name)
      : 'UnknownError'

  if (errorName === 'NotAllowedError' || errorName === 'SecurityError') {
    return 'Camera access was denied. Allow it in browser settings or use manual entry below.'
  }

  if (errorName === 'NotFoundError' || errorName === 'OverconstrainedError') {
    return 'No usable camera was found. Connect a camera or use manual entry below.'
  }

  if (errorName === 'NotReadableError' || errorName === 'AbortError') {
    return 'The camera is busy or could not be started. Close other camera apps or use manual entry.'
  }

  return 'Camera scanning could not start. Check browser permissions or use manual entry below.'
}

export function GateCameraScanner({ disabled, onScan }: GateCameraScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const controlsRef = useRef<IScannerControls | null>(null)
  const requestIdRef = useRef(0)
  const capturedRef = useRef(false)
  const [cameraState, setCameraState] = useState<GateCameraState>('idle')
  const [cameraError, setCameraError] = useState<string | null>(null)

  function stopActiveScanner() {
    requestIdRef.current += 1
    controlsRef.current?.stop()
    controlsRef.current = null
  }

  function stopCamera() {
    stopActiveScanner()
    capturedRef.current = false
    setCameraState('idle')
    setCameraError(null)
  }

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia || !videoRef.current) {
      setCameraState('error')
      setCameraError(
        'This browser cannot access a camera. Use a modern browser over HTTPS or enter the code manually.',
      )
      return
    }

    stopActiveScanner()
    const requestId = requestIdRef.current
    capturedRef.current = false
    setCameraState('starting')
    setCameraError(null)

    try {
      const { BrowserQRCodeReader } = await import('@zxing/browser')
      if (requestId !== requestIdRef.current) {
        return
      }

      const reader = new BrowserQRCodeReader(undefined, {
        delayBetweenScanAttempts: 250,
        delayBetweenScanSuccess: 1000,
      })
      const controls = await reader.decodeFromConstraints(
        {
          audio: false,
          video: { facingMode: { ideal: 'environment' } },
        },
        videoRef.current,
        (result, _error, activeControls) => {
          if (requestId !== requestIdRef.current || !result || capturedRef.current) {
            return
          }

          capturedRef.current = true
          activeControls.stop()
          controlsRef.current = null
          setCameraState('captured')
          onScan(result.getText())
        },
      )

      if (requestId !== requestIdRef.current || capturedRef.current) {
        controls.stop()
        return
      }

      controlsRef.current = controls
      setCameraState('scanning')
    } catch (error) {
      if (requestId !== requestIdRef.current) {
        return
      }

      controlsRef.current = null
      setCameraState('error')
      setCameraError(cameraErrorMessage(error))
    }
  }

  useEffect(() => {
    if (!disabled) {
      return
    }

    stopActiveScanner()
    setCameraState((currentState) => (currentState === 'captured' ? currentState : 'idle'))
  }, [disabled])

  useEffect(
    () => () => {
      requestIdRef.current += 1
      controlsRef.current?.stop()
      controlsRef.current = null
    },
    [],
  )

  const cameraIsActive = cameraState === 'starting' || cameraState === 'scanning'
  const cameraBadge =
    cameraState === 'starting' ? 'Starting' : cameraState === 'scanning' ? 'Live' : 'Off'
  const statusMessage = {
    idle: 'Camera is off. Start it only when you are ready to scan.',
    starting: 'Requesting camera access...',
    scanning: 'Camera active. Hold the QR code inside the frame.',
    captured: 'QR captured. Waiting for the authoritative server result.',
    error: cameraError ?? 'Camera unavailable. Use manual entry below.',
  }[cameraState]

  return (
    <section className={styles['gate-camera']} aria-labelledby="gate-camera-title">
      <div className={styles['gate-camera__heading']}>
        <div>
          <p className="eyebrow">Camera input</p>
          <h2 id="gate-camera-title">Scan the ticket QR</h2>
        </div>
        <span>{cameraBadge}</span>
      </div>

      <div className={styles['gate-camera__viewport']}>
        <video ref={videoRef} aria-label="Gate camera preview" autoPlay muted playsInline />
        {!cameraIsActive && (
          <div className={styles['gate-camera__placeholder']} aria-hidden="true">
            <span>Camera off</span>
          </div>
        )}
        {cameraState === 'scanning' && (
          <div className={styles['gate-camera__target']} aria-hidden="true" />
        )}
      </div>

      <p
        className={`${styles['gate-camera__status']} ${
          cameraState === 'error' ? styles['is-error'] : ''
        }`}
        role={cameraState === 'error' ? 'alert' : 'status'}
        aria-live="polite"
      >
        {statusMessage}
      </p>

      {cameraIsActive ? (
        <button className="secondary-button" type="button" onClick={stopCamera}>
          Stop camera
        </button>
      ) : (
        <button
          className="secondary-button"
          type="button"
          disabled={disabled}
          onClick={startCamera}
        >
          {cameraState === 'captured' ? 'Scan another ticket' : 'Start camera'}
        </button>
      )}
    </section>
  )
}
