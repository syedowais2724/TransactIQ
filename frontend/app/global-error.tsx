'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center bg-black text-white">
          <div className="text-center space-y-4 p-8">
            <h2 className="text-2xl font-bold">Something went wrong!</h2>
            <button
              onClick={reset}
              className="px-4 py-2 bg-white text-black rounded-md hover:bg-gray-200"
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  )
}
