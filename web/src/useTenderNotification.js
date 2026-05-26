import { useState } from 'react'
import { sendTenderNotification } from './api'

export function useTenderNotification(tender) {
  const [sending, setSending] = useState(false)
  const [notifyStatus, setNotifyStatus] = useState('')

  function sendToTelegram() {
    setSending(true)
    setNotifyStatus('')
    sendTenderNotification(tender)
      .then((payload) => setNotifyStatus(payload.message || (payload.sent ? 'Отправлено в Telegram' : 'Telegram не настроен')))
      .catch((err) => setNotifyStatus(err.message))
      .finally(() => setSending(false))
  }

  return {
    sending,
    notifyStatus,
    setNotifyStatus,
    sendToTelegram,
  }
}
