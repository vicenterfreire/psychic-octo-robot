import { QRCodeSVG } from 'qrcode.react'

interface TicketQrCodeProps {
  token: string
  label: string
}

const TICKET_QR_SIZE = 184

export function TicketQrCode({ token, label }: TicketQrCodeProps) {
  return (
    <div className="ticket-qr" aria-label={label}>
      <QRCodeSVG value={token} size={TICKET_QR_SIZE} level="M" title={label} />
    </div>
  )
}
