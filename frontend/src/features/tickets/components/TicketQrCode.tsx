import { QRCodeSVG } from 'qrcode.react'
import styles from '../tickets.module.css'

interface TicketQrCodeProps {
  token: string
  label: string
}

const TICKET_QR_SIZE = 184

export function TicketQrCode({ token, label }: TicketQrCodeProps) {
  return (
    <div className={styles['ticket-qr']} aria-label={label}>
      <QRCodeSVG value={token} size={TICKET_QR_SIZE} level="M" title={label} />
    </div>
  )
}
