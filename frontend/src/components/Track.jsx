import Logo from './Logo'
import CalendarArc from './CalendarArc'
import HormoneChart from './HormoneChart'
import ErrorBanner from './ErrorBanner'
import { PHASE_LABELS } from '../cycle/phaseEngine'
import { CALENDAR_WIDTH } from '../cycle/dates'
import { useCycle } from '../hooks/useCycle'

export default function Track() {
  const {
    selectedDate,
    setSelectedDate,
    logs,
    loading,
    saving,
    error,
    dismissError,
    awaitingPeriodEnd,
    phaseInfo,
    handlePeriodClick,
    handleFlowSelect,
    selectedLog,
    FLOW_OPTIONS,
    cycleLength,
  } = useCycle()

  const busy = loading || saving

  return (
    <div className="flex flex-col items-center px-6 py-8">
      <h1 className="text-2xl font-bold text-peach-fuzz mb-2">Aestas</h1>
      <Logo className="w-16 h-16 text-powder-blush mb-4" />
      {phaseInfo.phase && (
        <p className="text-powder-blush/90 text-sm text-center mb-2">
          {PHASE_LABELS[phaseInfo.phase]} · day {phaseInfo.cycleDay}
        </p>
      )}
      <div className="w-full max-w-3xl">
        <ErrorBanner message={error} onDismiss={dismissError} className="mb-4" />
        <HormoneChart
          phase={phaseInfo.phase}
          cycleDay={phaseInfo.cycleDay}
          cycleLength={phaseInfo.cycleLength ?? cycleLength}
          windows={phaseInfo.windows}
          ovulationDay={phaseInfo.ovulationDay}
        />
        <CalendarArc
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
          logs={logs}
        />
        <div className={`mb-8 ${CALENDAR_WIDTH}`}>
          <button
            type="button"
            onClick={handlePeriodClick}
            disabled={busy}
            className={`
              w-full rounded-2xl font-semibold py-4 px-8 text-lg transition-colors
              ${awaitingPeriodEnd
                ? 'bg-burnt-rose text-white hover:bg-dusty-mauve'
                : 'bg-dusty-mauve/60 text-peach-fuzz hover:bg-dusty-mauve'
              }
              disabled:opacity-50
            `}
          >
            {awaitingPeriodEnd ? 'Period Ended' : 'Period Started'}
          </button>
        </div>
        <p className="text-powder-blush/90 text-base text-center mb-3" id="flow-label">
          Flow
        </p>
        <div className="flex justify-center gap-5 flex-wrap" role="group" aria-labelledby="flow-label">
          {FLOW_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => handleFlowSelect(opt.id)}
              disabled={busy}
              aria-pressed={selectedLog.flow === opt.id}
              className={`
                rounded-2xl px-6 py-3 text-base font-medium transition-colors
                ${selectedLog.flow === opt.id
                  ? 'bg-dusty-mauve text-white ring-2 ring-powder-blush/50'
                  : 'bg-dusty-mauve/30 text-powder-blush/80 hover:bg-dusty-mauve/50'
                }
                disabled:opacity-50
              `}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
