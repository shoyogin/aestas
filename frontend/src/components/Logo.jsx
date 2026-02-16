export default function Logo({ className = '' }) {
  return (
    <span className={`inline-block ${className}`} aria-hidden>
      <svg
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        <circle cx="32" cy="32" r="28" fill="currentColor" opacity="0.2" />
        <circle cx="32" cy="32" r="16" fill="currentColor" opacity="0.5" />
        <circle cx="32" cy="26" r="6" fill="currentColor" />
      </svg>
    </span>
  )
}
