import { useSearchParams } from 'react-router-dom'
import Logo from './Logo'
import ErrorBanner from './ErrorBanner'
import { useAuth } from '../context/authContext'

const LOGIN_ERRORS = {
  no_code: 'Google did not send us back a login code. Please try again.',
  invalid_state: 'That login link expired. Please try signing in again.',
  oauth_failed: 'We could not complete the sign-in with Google. Please try again.',
  access_denied: 'Sign-in was cancelled.',
}

export default function Welcome() {
  const { loginUrl } = useAuth()
  const [params] = useSearchParams()
  const error = params.get('error')

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-night-bordeaux">
      <div className="max-w-md w-full text-center space-y-10">
        <Logo className="mx-auto w-16 h-16 text-powder-blush" />
        <div>
          <h1 className="text-4xl font-bold text-peach-fuzz tracking-tight">Aestas</h1>
          <p className="mt-2 text-powder-blush/90 text-lg">It&apos;s your time to bloom.</p>
        </div>
        {/* Login failures redirect here with ?error=…; they used to be invisible. */}
        <ErrorBanner
          message={error ? LOGIN_ERRORS[error] || 'Sign-in failed. Please try again.' : null}
        />
        <div className="flex flex-col gap-4 pt-4">
          <a
            href={loginUrl}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-dusty-mauve hover:bg-burnt-rose text-white font-semibold py-3 px-6 transition-colors shadow-lg"
          >
            <GoogleIcon className="w-5 h-5" />
            Sign in with Google
          </a>
          <p className="text-powder-blush/70 text-sm">Use one account to sign up or log in.</p>
        </div>
      </div>
    </div>
  )
}

function GoogleIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="currentColor"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="currentColor"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="currentColor"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="currentColor"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  )
}
