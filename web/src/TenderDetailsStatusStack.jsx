export function TenderDetailsStatusStack({ messages = [] }) {
  if (!messages.length) return null

  return (
    <div className="status-stack">
      {messages.map((message) => <p className="inline-status" key={message}>{message}</p>)}
    </div>
  )
}
