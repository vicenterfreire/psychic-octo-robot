import { QRCodeSVG } from 'qrcode.react'

interface TicketQrCodeProps {
  token: string
  label: string
}

export function TicketQrCode({ token, label }: TicketQrCodeProps) {
  return (
    <div className="ticket-qr" aria-label={label}>
      <QRCodeSVG value={token} size={184} level="M" title={label} />
    </div>
  )
}
