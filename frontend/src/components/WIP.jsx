import Logo from './Logo'

export default function WIP() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-night-bordeaux">
      <div className="max-w-md w-full text-center space-y-8">
        <Logo className="mx-auto w-20 h-20 text-powder-blush" />
        <div>
          <h1 className="text-3xl font-bold text-peach-fuzz">
            Under construction
          </h1>
          <p className="mt-3 text-powder-blush/90">
            You’re all set. We’re building the rest of the app — check back
            soon.
          </p>
        </div>
        <div className="rounded-xl bg-dusty-mauve/20 border border-powder-blush/30 p-4 text-powder-blush text-sm text-left">
          You’ve completed sign-up and onboarding. This page is a placeholder
          for the main app experience.
        </div>
      </div>
    </div>
  )
}
