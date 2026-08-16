import Logo from './Logo'
import HormoneChart from './HormoneChart'
import PhaseDashboard from './PhaseDashboard'
import { PHASE_LABELS } from '../cycle/phaseEngine'
import { HORMONE_CHART_INSIGHTS } from '../cycle/hormoneInsights'
import { useCycle } from '../hooks/useCycle'

export default function Insights() {
  const { phaseInfo, cycleLength } = useCycle()

  return (
    <div className="flex flex-col items-center px-6 py-8">
      <h1 className="text-2xl font-bold text-peach-fuzz mb-2">Insights</h1>
      <Logo className="w-16 h-16 text-powder-blush mb-4" />
      {phaseInfo.phase && (
        <p className="text-powder-blush/90 text-sm text-center mb-2">
          {PHASE_LABELS[phaseInfo.phase]} · day {phaseInfo.cycleDay}
        </p>
      )}
      <div className="w-full max-w-3xl">
        <HormoneChart
          phase={phaseInfo.phase}
          cycleDay={phaseInfo.cycleDay}
          cycleLength={phaseInfo.cycleLength ?? cycleLength}
          windows={phaseInfo.windows}
          ovulationDay={phaseInfo.ovulationDay}
        />
        {phaseInfo.phase && HORMONE_CHART_INSIGHTS[phaseInfo.phase] && (
          <p className="text-powder-blush/90 text-sm text-center leading-snug max-w-xl mx-auto mb-8 line-clamp-2">
            {HORMONE_CHART_INSIGHTS[phaseInfo.phase]}
          </p>
        )}
        <PhaseDashboard phase={phaseInfo.phase} cycleDay={phaseInfo.cycleDay} />
      </div>
    </div>
  )
}
