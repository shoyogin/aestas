/** One consistent way to show a failure the user can act on. */
export default function ErrorBanner({ message, onDismiss, className = '' }) {
  if (!message) return null
  return (
    <div
      role="alert"
      className={`flex items-start gap-3 rounded-xl bg-burnt-rose/30 border border-burnt-rose text-peach-fuzz p-3 text-sm ${className}`}
    >
      <span className="flex-1">{message}</span>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss"
          className="flex-shrink-0 text-peach-fuzz/70 hover:text-peach-fuzz"
        >
          ✕
        </button>
      )}
    </div>
  )
}
