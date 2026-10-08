import Link from 'next/link'

export function Navbar() {
  const logoSVG = (
    <svg
      viewBox="0 0 256 256"
      fill="currentColor"
      className="w-6 h-6 text-[#191919]"
    >
      <path d="M 144 256 L 27.598 256 L 144 139.598 Z" />
      <path d="M 256 207.5 L 200 256 L 200 56 L 0 56 L 48 0 L 256 0 Z" />
      <path d="M 0 204.402 L 0 112 L 92.402 112 Z" />
    </svg>
  )

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/60 backdrop-blur-md border-b border-gray-200/40 transition-all duration-200">
      <div className="px-6 sm:px-10 md:px-14 py-3.5 sm:py-4 flex items-center justify-between">
        {/* Logo & Tag */}
        <Link href="/" className="flex items-center gap-2.5 group">
          {logoSVG}
          <div className="flex items-center gap-2">
            <span className="font-semibold text-base sm:text-lg tracking-tight text-[#191919]">
              Stratos Enterprises
            </span>
            <span className="text-[10px] uppercase font-semibold tracking-wider text-[#191919]/60 bg-[#191919]/5 px-2 py-0.5 rounded border border-[#191919]/10">
              Powered by SentinelRAG
            </span>
          </div>
        </Link>

        {/* CTA Button */}
        <Link
          href="/login"
          className="px-5 py-2.5 bg-[#191919] text-white text-sm font-medium rounded-lg hover:bg-[#191919]/90 transition-colors duration-200"
        >
          Get Started
        </Link>
      </div>
    </nav>
  )
}
