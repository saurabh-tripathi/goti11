export default function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg px-4 py-3 text-sm">
      {message}
    </div>
  )
}
