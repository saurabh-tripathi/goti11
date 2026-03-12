export default function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-12 h-12' : 'w-8 h-8'
  return (
    <div className="flex justify-center items-center p-4">
      <div className={`${sizeClass} border-2 border-teal-500 border-t-transparent rounded-full animate-spin`} />
    </div>
  )
}
