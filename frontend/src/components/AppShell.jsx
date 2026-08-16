import { NavLink, Outlet } from 'react-router-dom'

const TABS = [
  { to: '/app', end: true, label: 'Track' },
  { to: '/app/insights', label: 'Insights' },
  { to: '/app/friends', label: 'Friends' },
  { to: '/app/account', label: 'Account' },
]

export default function AppShell() {
  return (
    <div className="min-h-screen bg-night-bordeaux text-peach-fuzz">
      <div className="pb-36">
        <Outlet />
      </div>
      <nav
        className="fixed inset-x-0 bottom-0 z-50 border-t border-powder-blush/20 bg-night-bordeaux/95 backdrop-blur-sm pb-[max(0.5rem,env(safe-area-inset-bottom))]"
        aria-label="Main"
      >
        <div className="max-w-3xl mx-auto flex">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) =>
                `flex-1 py-5 px-1 text-center text-sm font-semibold sm:text-base tracking-wide ${
                  isActive ? 'text-peach-fuzz' : 'text-powder-blush/70'
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
