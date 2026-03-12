interface TeamSummaryBarProps {
  selectedCount: number
  creditsUsed: number
  maxCredits: number
  hasCaptain: boolean
  hasVC: boolean
  onSubmit: () => void
  isLoading?: boolean
  isLocked?: boolean
}

export default function TeamSummaryBar({
  selectedCount,
  creditsUsed,
  maxCredits,
  hasCaptain,
  hasVC,
  onSubmit,
  isLoading,
  isLocked,
}: TeamSummaryBarProps) {
  const isValid = selectedCount === 11 && hasCaptain && hasVC && creditsUsed <= maxCredits

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-navy-800 border-t border-navy-700 px-4 py-3 flex items-center justify-between gap-3 z-50">
      <div className="flex gap-4 text-sm">
        <span className={selectedCount === 11 ? 'text-teal-400' : 'text-white'}>
          <span className="font-bold">{selectedCount}</span>/11
        </span>
        <span className={creditsUsed > maxCredits ? 'text-red-400' : 'text-white'}>
          <span className="font-bold">{creditsUsed.toFixed(1)}</span>/{maxCredits} cr
        </span>
        {!hasCaptain && selectedCount > 0 && (
          <span className="text-yellow-400 text-xs">No C</span>
        )}
        {!hasVC && selectedCount > 0 && (
          <span className="text-yellow-400 text-xs">No VC</span>
        )}
      </div>

      <button
        onClick={onSubmit}
        disabled={!isValid || isLoading || isLocked}
        className="px-4 py-2 rounded-lg bg-teal-500 text-white font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-teal-400 transition-colors"
      >
        {isLocked ? 'Locked' : isLoading ? 'Saving…' : 'Save Team'}
      </button>
    </div>
  )
}
